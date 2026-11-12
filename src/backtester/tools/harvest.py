"""Local idea-harvest pipeline. See the fable research framework, sections 2-4."""
import argparse
import csv
import difflib
import html
import io
import json
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests

ROOT = Path("research/harvest")
TASK_COLUMNS = ["task_id", "key", "queries", "status", "worker", "run_date", "n_raw", "n_verified", "n_kept"]
SOURCES = {
    "ACAD": ("academic papers", '"intraday" "futures" "after transaction costs"',
             'site:arxiv.org q-fin rebalancing', '"out-of-sample" anomaly futures'),
    "CB": ("central banks and exchanges", 'site:bis.org working paper fixing',
           'site:cmegroup.com settlement procedure', 'MSCI index review price pressure'),
    "AGG": ("curated research lists", 'quantpedia futures calendar strategy',
            'quantocracy seasonality', 'alpha architect replication'),
    "BOOK": ("trading books", 'systematic trading rules backtest',
             '"trading system" book chapter rules', 'trading book sample code'),
    "BLOG": ("practitioner blogs", '"backtest" "after costs" blog',
             '"I tested" strategy "out of sample"', 'trading strategy backtest blog'),
    "GIT": ("GitHub repositories", 'github awesome systematic trading strategies',
            'github backtest strategy "walk forward" README', 'github trading strategy rules'),
    "FORUM": ("trading forums", 'site:forexfactory.com "rules" "backtest"',
              'site:elitetrader.com index futures', 'site:futures.io trading strategy'),
    "REDDIT": ("trading subreddits", 'site:reddit.com/r/algotrading "stopped working" costs',
               'site:reddit.com/r/algotrading "edge" futures', 'site:reddit.com/r/quant strategy'),
    "AV": ("video and podcast transcripts", '"Better System Trader" transcript strategy rules',
           '"Top Traders Unplugged" transcript futures', 'trading strategy podcast transcript'),
    "BROKER": ("broker and prop-firm pages", 'FTMO dividend index CFD adjustment',
               'CFD rollover futures expiry schedule', 'prop firm prohibited strategies list'),
}
MARKETS = {"FX-MAJ", "FX-CROSS", "IDX-US", "IDX-INTL", "METAL", "ENERGY", "CRYPTO"}
HORIZONS = {"INTRA", "SWING", "POS"}
MECHANISMS = {"FLOW", "EVENT", "CARRY", "TREND", "REVERSAL", "VOL", "CROSS", "MICRO"}
FLAGS = {"sells_course", "no_test_period", "single_example", "tiny_sample", "needs_discretion",
         "in_sample_only", "costs_ignored", "none"}
RULES = {"market", "timeframe", "entry", "exit", "stop", "filters"}
FIELDS = {"name", "claim", "source_url", "source_type", "quote", "language", "mechanism",
          "rules", "not_stated", "claimed_result", "required_data", "we_have", "red_flags"}
UA = "backtester-harvest/0.1"
WORDS = {  # search words for the key codes (raw codes are poor queries)
    "FX-MAJ": "major FX", "FX-CROSS": "FX crosses", "IDX-US": "US stock index",
    "IDX-INTL": "DAX FTSE Nikkei index", "METAL": "gold silver", "ENERGY": "crude oil",
    "CRYPTO": "bitcoin", "FLOW": "rebalancing flows", "EVENT": "scheduled release",
    "CARRY": "carry term structure", "TREND": "trend following", "REVERSAL": "reversal",
    "VOL": "volatility", "CROSS": "lead lag", "MICRO": "market microstructure",
}


def read_csv(path):
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, columns, rows, append=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a" if append else "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        if not append or not exists:
            writer.writeheader()
        writer.writerows(rows)


def parse_key(key):
    parts = key.split(".")
    if len(parts) != 4:
        raise ValueError(f"invalid key {key}: expected SOURCE.MARKET.HORIZON.MECHANISM")
    source, market, horizon, mechanism = parts
    base = source.split("-", 1)[-1]
    if base not in SOURCES or (source != base and not re.fullmatch(r"[A-Z]{2}-" + base, source)):
        raise ValueError(f"invalid source: {source}")
    for value, choices, label in [(market, MARKETS, "market"), (horizon, HORIZONS, "horizon"),
                                   (mechanism, MECHANISMS, "mechanism")]:
        if value != "*" and value not in choices:
            raise ValueError(f"invalid {label}: {value}")
    return source, market, horizon, mechanism


def plan(keys, path):
    rows = read_csv(path)
    active = {r["key"] for r in rows if r["status"] in {"open", "running"}}
    next_id = max((int(r["task_id"][1:]) for r in rows if re.fullmatch(r"T\d+", r["task_id"])),
                  default=0)
    new = []
    for key in keys:
        source, market, _horizon, mechanism = parse_key(key)
        if key in active:
            raise ValueError(f"task already open or running: {key}")
        active.add(key)
        next_id += 1
        templates = SOURCES[source.split("-")[-1]][1:]
        words = " ".join(WORDS[x] for x in (market, mechanism) if x != "*")
        new.append({"task_id": f"T{next_id:04d}", "key": key,
                        "queries": " | ".join(f"{q} {words}".strip() for q in templates), "status": "open"})
    write_csv(path, TASK_COLUMNS, new, append=True)


def prompt(task_id, tasks, families):
    row = next((r for r in read_csv(tasks) if r["task_id"] == task_id), None)
    if row is None:
        raise ValueError(f"unknown task: {task_id}")
    source, market, horizon, mechanism = parse_key(row["key"])
    known = ", ".join(r["family"] for r in read_csv(families) if r["verdict"].lower() != "open")
    print(f'''You collect trading ideas from the web. You do not judge them.

TASK {task_id}: sources = {SOURCES[source.split('-')[-1]][0]} ({source}); market = {market};
holding time = {horizon}; mechanism = {mechanism}.
Run these searches: {row['queries']}

RULES
1. Open the page before you use it. Never cite a page you did not open.
2. Report an idea only if the page states a trading rule or a measurable price effect.
3. Copy one sentence from the page, word for word, that states the rule or effect ("quote").
4. Do not fill gaps. If the page does not give a value, write "not stated".
5. Skip ideas in this list: {known}
6. At most 5 ideas. If you find none, answer exactly: {{"task_id": "{task_id}", "ideas": []}}
7. No opinion on whether it makes money. No advice. Output JSON only, nothing else.

OUTPUT: one JSON object with task_id and ideas; each idea has name (max 8 words), claim,
source_url, source_type (paper | central_bank | book | blog | repo | forum | video | broker),
quote (max 300 characters), language, mechanism, rules (market, timeframe, entry, exit, stop,
filters), not_stated (array), claimed_result, required_data (array), we_have (yes | partly | no),
and red_flags (sells_course, no_test_period, single_example, tiny_sample, needs_discretion,
in_sample_only, costs_ignored, none). If no web access output {{"task_id": "{task_id}",
"error": "no web access"}}.''')


class Fetcher:
    def __init__(self):
        self.last = {}
        self.robots = {}

    def get(self, url):
        host = urlsplit(url).netloc.lower()
        delay = 1 - (time.monotonic() - self.last.get(host, -1e20))
        if delay > 0:
            time.sleep(delay)
        self.last[host] = time.monotonic()
        return requests.get(url, headers={"User-Agent": UA}, timeout=20, allow_redirects=True)

    def __call__(self, url):
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            return 0, "", False
        origin = f"{parts.scheme}://{parts.netloc}"
        try:
            if origin not in self.robots:
                response = self.get(origin + "/robots.txt")
                if response.status_code >= 500 or response.status_code in (401, 403):
                    return 0, "", False
                robot = RobotFileParser()
                robot.parse(response.text.splitlines() if response.status_code == 200 else [])
                self.robots[origin] = robot
            if not self.robots[origin].can_fetch(UA, url):
                return 0, "", False
            response = self.get(url)
            return response.status_code, page_text(response), True
        except (requests.RequestException, ValueError):
            return 0, "", False


def page_text(response):
    """HTML as text; a PDF's extracted text (its raw bytes would never match a quote)."""
    if "pdf" not in response.headers.get("Content-Type", "").lower() and response.content[:5] != b"%PDF-":
        return response.text
    from pypdf import PdfReader  # data extra; only PDF sources need it

    try:
        return " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(response.content)).pages)
    except Exception:  # noqa: BLE001 - any broken PDF counts as unreadable, never as bytes
        return ""


def normalized(text):
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", text)).lower().split())


def fuzzy_found(quote, text, ratio=0.9):
    """A same-length window with SequenceMatcher ratio >= `ratio`. Windows step by 5 % of the
    quote and only those passing the cheap upper bounds get the full ratio (pages are long)."""
    size = len(quote)
    if not size:
        return False
    matcher = difflib.SequenceMatcher(None, autojunk=False)
    matcher.set_seq2(quote)
    for i in range(0, max(1, len(text) - size + 1), max(1, size // 20)):
        matcher.set_seq1(text[i:i + size])
        if matcher.real_quick_ratio() >= ratio and matcher.quick_ratio() >= ratio and matcher.ratio() >= ratio:
            return True
    return False


def schema(item):
    if not isinstance(item, dict) or not FIELDS <= item.keys():
        return False
    strings = FIELDS - {"rules", "not_stated", "required_data", "red_flags"}
    if any(not isinstance(item[k], str) or not item[k].strip() for k in strings):
        return False
    if len(item["quote"]) > 300 or len(item["name"].split()) > 8:
        return False
    if item["source_type"] not in {"paper", "central_bank", "book", "blog", "repo", "forum", "video", "broker"}:
        return False
    if item["we_have"] not in {"yes", "partly", "no"}:
        return False
    rules = item["rules"]
    if not isinstance(rules, dict) or not RULES <= rules.keys() or any(
            not isinstance(rules[k], str) for k in RULES):
        return False
    if any(not isinstance(item[k], list) or any(not isinstance(x, str) for x in item[k])
           for k in ("not_stated", "required_data", "red_flags")):
        return False
    return set(item["red_flags"]) <= FLAGS


def stated(value):
    return bool(value.strip()) and value.strip().lower() != "not stated"


def symbol(market):
    text = market.lower()
    mappings = [(r"\b(s&p(?:\s*500)?|spx|es|us500)\b", "US500"),
                (r"\b(nasdaq|nq|nas100)\b", "NAS100"), (r"\b(dow|us30)\b", "US30"),
                (r"\b(dax|ger40)\b", "GER40"), (r"\b(ftse|uk100)\b", "UK100"),
                (r"\b(nikkei|jp225)\b", "JP225"), (r"\b(gold|xauusd)\b", "XAUUSD"),
                (r"\b(silver|xagusd)\b", "XAGUSD"), (r"\b(wti|crude|usoil)\b", "USOIL"),
                (r"\b(brent|ukoil)\b", "UKOIL"), (r"\b(bitcoin|btcusd)\b", "BTCUSD"),
                (r"\b(ether|ethereum|ethusd)\b", "ETHUSD")]
    for pattern, result in mappings:
        if re.search(pattern, text):
            return result
    fx = re.search(r"\b(?:aud|cad|chf|eur|gbp|jpy|nzd|usd){2}\b", text)
    return fx.group().upper() if fx else None


def check_idea(item, task_id, model, fetcher):
    result = dict(item) if isinstance(item, dict) else {"raw": item}
    result.update(task_id=task_id, model=model, status="rejected", reason="schema")
    if not schema(item):
        return result
    status, page, allowed = fetcher(item["source_url"])
    text, quote = normalized(page), normalized(item["quote"])
    if not allowed or status != 200 or any(x in text for x in (
            "sign in to continue", "subscribe to read", "log in to view")):
        result["reason"] = "unverified_source"
        return result
    if quote not in text and not fuzzy_found(quote, text):
            result["reason"] = "unverified_source"
            return result
    pos = text.find(quote)
    nearby = text[max(0, pos - 300):pos + len(quote) + 300] if pos >= 0 else text
    if re.search(r"\b(course|enroll|signals group|discount code|affiliate|coupon)\b", nearby):
        result["reason"] = "sells_course"
    elif (not all(stated(item["rules"][k]) for k in ("entry", "exit")) or re.search(
            r"\b(discretion|feel|context|experience)\b", " ".join(item["rules"].values()), re.IGNORECASE)):
        result["reason"] = "untestable"
    elif not symbol(item["rules"]["market"]):
        result.update(status="parked", reason="needs_data")
    elif not stated(item["mechanism"]):
        result.update(status="parked", reason="no_mechanism")
    elif re.search(r"would have|turned \$|never loses|win\s*rate\s*(?:of|:|=)?\s*(?:90\.\d*[1-9]\d*|9[1-9](?:\.\d+)?|100(?:\.\d+)?)\s*%",
                   " ".join((item["claim"], item["quote"], item["claimed_result"])), re.IGNORECASE):
        result["reason"] = "hindsight"
    else:
        result.update(status="verified", reason="", symbol=symbol(item["rules"]["market"]))
    return result


def check_file(path, model, fetcher):
    result = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                result.append(check_idea({}, "", model, fetcher))
                continue
            if isinstance(obj, dict) and isinstance(obj.get("ideas"), list):
                result.extend(check_idea(i, obj.get("task_id", ""), model, fetcher) for i in obj["ideas"])
            else:
                result.append(check_idea(obj, obj.get("task_id", "") if isinstance(obj, dict) else "", model, fetcher))
    return result


def tokens(item):
    return set(re.findall(r"\w+", (item["rules"]["entry"] + " " + item["rules"]["exit"]).lower()))


def deduplicate(rows, families, ledger):
    known = read_csv(families)
    urls = "\n".join(r.get("source", "") + " " + r.get("notes", "") for r in read_csv(ledger))
    accepted = []
    for row in rows:
        if row.get("status") != "verified":
            continue
        url = row["source_url"]
        if url in urls:
            row.update(status="merged", reason="ledger_url")
            continue
        content = (row["name"] + " " + row["claim"] + " " + " ".join(row["rules"].values())).lower()
        for family in known:
            if any(k.strip().lower() in content for k in family["keywords"].split(";") if k.strip()):
                row["family"] = family["family"]
                if family["verdict"].lower() in {"falsified", "closed", "tested", "screened_out"}:
                    row.update(status="rejected", reason="known_family")
                break
        if row["status"] != "verified":
            continue
        row.setdefault("seen_count", 1)
        row.setdefault("domains", [urlsplit(url).netloc.lower()])
        for previous in accepted:
            a, b = tokens(row), tokens(previous)
            if (symbol(row["rules"]["market"]) == symbol(previous["rules"]["market"])
                    and row["rules"]["timeframe"].lower() == previous["rules"]["timeframe"].lower()
                    and a and b and len(a & b) / len(a | b) >= .6):
                previous["seen_count"] += 1
                previous["domains"] = sorted(set(previous["domains"] + row["domains"]))
                row.update(status="merged", reason="similar_rules")
                break
        else:
            accepted.append(row)
    return rows


def score_idea(row):
    mechanism = row["mechanism"].lower()
    if any(x in mechanism for x in ("rebalanc", "hedg", "settlement", "index inclusion", "expiry", "fixing")):
        score = 3
    elif any(x in mechanism for x in ("carry", "liquidity provision", "risk premium")):
        score = 2
    else:
        score = 1
    source = row["source_type"]
    score += 2 if source in {"paper", "central_bank"} else int(
        source in {"book", "blog"} and stated(row["claimed_result"]))
    count = sum(stated(row["rules"][k]) for k in ("entry", "exit", "stop"))
    score += 2 if count == 3 else 1 if count == 2 else 0
    score += 1 + int(len(set(row.get("domains", []))) >= 2)
    score -= min(3, len(set(row["red_flags"]) - {"none"}))
    return max(0, min(10, score))


def read_jsonl(path):
    with open(path, encoding="utf-8-sig") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def report(rows, tasks, ledger, write_ledger=False):
    print("Status and reason:")
    for (status, reason), count in sorted(Counter((r.get("status", ""), r.get("reason", "")) for r in rows).items()):
        print(f"  {status} {reason}: {count}")
    task_keys = {r["task_id"]: r["key"] for r in read_csv(tasks)}
    print("Tasks:")
    for task, count in sorted(Counter(r.get("task_id", "") for r in rows).items()):
        print(f"  {task} {task_keys.get(task, 'unknown')}: {count}")
    print("Unverified rate by model:")
    for model in sorted({r.get("model", "") for r in rows}):
        group = [r for r in rows if r.get("model", "") == model]
        print(f"  {model}: {sum(r.get('reason') == 'unverified_source' for r in group) / len(group):.1%}")
    print("Top ideas:")
    for row in sorted((r for r in rows if r.get("score", 0) >= 6), key=lambda r: -r["score"])[:10]:
        print(f"  {row['score']} {row.get('name', '')}")
    if write_ledger:
        path = Path(ledger)
        existing = read_csv(path)
        with path.open(encoding="utf-8-sig", newline="") as f:
            columns = next(csv.reader(f))
        ids = {r["id"] for r in existing}
        new = []
        counts = Counter()
        for row in rows:
            task = row.get("task_id", "")
            counts[task] += 1
            ident = f"HV-{task}-{counts[task]}"
            if ident in ids:
                continue
            status = row.get("status", "harvested")
            new.append({"id": ident, "stage": status if status in {"verified", "parked", "rejected"} else "harvested",
                            "family": row.get("family", ""), "name": row.get("name", ""),
                            "mechanism": row.get("mechanism", ""), "source": row.get("source_url", ""),
                            "symbols": row.get("symbol", ""), "verdict": row.get("reason", "")})
        write_csv(path, columns, new, append=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan")
    p.add_argument("keys", nargs="+")
    p.add_argument("--tasks", default=ROOT / "tasks.csv")
    p = sub.add_parser("prompt")
    p.add_argument("task_id")
    p.add_argument("--tasks", default=ROOT / "tasks.csv")
    p.add_argument("--families", default=ROOT / "known_families.csv")
    p = sub.add_parser("check")
    p.add_argument("raw")
    p.add_argument("--out", default=ROOT / "checked.jsonl")
    p.add_argument("--model", default="unknown")
    for name in ("dedup", "score", "report"):
        p = sub.add_parser(name)
        p.add_argument("--checked", default=ROOT / "checked.jsonl")
        if name == "dedup":
            p.add_argument("--families", default=ROOT / "known_families.csv")
            p.add_argument("--ledger", default="research/ledger.csv")
        if name == "report":
            p.add_argument("--tasks", default=ROOT / "tasks.csv")
            p.add_argument("--ledger", default="research/ledger.csv")
            p.add_argument("--write-ledger", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            plan(args.keys, args.tasks)
        elif args.command == "prompt":
            prompt(args.task_id, args.tasks, args.families)
        elif args.command == "check":
            write_jsonl(args.out, check_file(args.raw, args.model, Fetcher()))
        elif args.command == "dedup":
            write_jsonl(args.checked, deduplicate(read_jsonl(args.checked), args.families, args.ledger))
        elif args.command == "score":
            rows = read_jsonl(args.checked)
            for row in rows:
                if row.get("status") == "verified":
                    row["score"] = score_idea(row)
            write_jsonl(args.checked, rows)
        else:
            report(read_jsonl(args.checked), args.tasks, args.ledger, args.write_ledger)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
