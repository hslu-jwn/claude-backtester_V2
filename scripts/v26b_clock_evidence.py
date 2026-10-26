"""Offline, bounded cache audit; never connects to MT5 or changes cache files."""

from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from time import monotonic
from zoneinfo import ZoneInfo

import pandas as pd

NY = ZoneInfo("America/New_York")
EU = ZoneInfo("Europe/London")


def main():
    started = monotonic()
    rows = []
    for year in range(2010, 2022):
        day = date(year, 1, 1)
        while day.year == year:
            if monotonic() - started > 540:
                raise RuntimeError("cache evidence budget exceeded (540 seconds)")
            noon = datetime.combine(day, datetime.min.time(), UTC) + timedelta(hours=12)
            gap = bool(noon.astimezone(NY).dst()) != bool(noon.astimezone(EU).dst())
            if day.weekday() in (4, 6) and (gap or day.month in (1, 7)):
                for feed in ("histdata", "mt5"):
                    for symbol in ("GBPUSD", "XAUUSD"):
                        path = Path("data/cache") / feed / symbol / str(year) / f"{day}.parquet"
                        if not path.exists():
                            continue
                        frame = pd.read_parquet(path, columns=["ts"])
                        if frame.empty:
                            continue
                        stamp = (
                            frame.ts.min()
                            if day.weekday() == 6
                            else frame.ts.max() + pd.Timedelta(minutes=1)
                        )
                        rows.append(
                            {
                                "feed": feed,
                                "symbol": symbol,
                                "date": str(day),
                                "year": year,
                                "period": "gap" if gap else "normal",
                                "edge": "open" if day.weekday() == 6 else "close",
                                "utc": str(stamp),
                                "ny": stamp.tz_convert(NY).strftime("%H:%M"),
                                "bars": len(frame),
                            }
                        )
            day += timedelta(days=1)
    Path("results").mkdir(exist_ok=True)
    data = pd.DataFrame(rows)
    data.to_csv("results/v26b_clock_edges.csv", index=False)
    Path("results/v26b_clock_edges.log").write_text(
        f"Offline original-cache edge pass: {len(rows)} observations, "
        f"{monotonic() - started:.2f} seconds; no cache writes.\n",
        encoding="utf-8",
    )
    for feed in ("histdata", "mt5"):
        lines = [
            f"# {feed} clock evidence (before conversion changes)",
            "",
            "Offline cache measurements: Friday last bar + 1 minute; Sunday first bar.",
            "FX anchor: Sunday 17:00 New York; gold closes 17:00 and reopens 18:00 New York.",
            "Normal sample: every January/July Friday and Sunday. Gap: every US/EU mismatch edge.",
            "Times below are in New York using the existing UTC cache, before fixes.",
            "",
            "|Year|Symbol|Period|Edge|Observed NY time (count)|",
            "|---|---|---|---|---|",
        ]
        for keys, group in data[data.feed == feed].groupby(["year", "symbol", "period", "edge"]):
            lines.append("|" + "|".join(map(str, keys)) + "|" + str(dict(Counter(group.ny))) + "|")
        lines += [
            "",
            "Dated observations: `results/v26b_clock_edges.csv`.",
            f"Elapsed seconds: {monotonic() - started:.2f}",
        ]
        Path(f"results/clock_check_{feed}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"edges={len(rows)}, seconds={monotonic() - started:.2f}")
    price_matches()


def price_matches():
    from backtester.core.models import Timeframe
    from backtester.data.cache import cache_path, read_cached_days
    from backtester.data.resample import resample
    from backtester.tools.mt5_compare import weekly_offsets

    started = monotonic()
    records, weekly = [], []
    for year in range(2015, 2022):
        for stamp in pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="W-MON"):
            if monotonic() - started > 540:
                raise RuntimeError("price evidence budget exceeded (540 seconds)")
            day = stamp.date()
            noon = stamp.replace(hour=12, tzinfo=UTC)
            gap = bool(noon.astimezone(NY).dst()) != bool(noon.astimezone(EU).dst())
            if not (gap or (day.month in (1, 7) and 7 <= day.day <= 13)):
                continue
            for symbol in ("GBPUSD", "XAUUSD", "NAS100"):
                frames = {}
                for feed in ("histdata", "mt5"):
                    paths = [
                        cache_path(Path("data/cache") / feed, symbol, day + timedelta(days=i))
                        for i in range(7)
                    ]
                    frames[feed] = read_cached_days([p for p in paths if p.exists()])
                if any(f.empty for f in frames.values()):
                    continue
                ref = frames["histdata"]
                if year <= 2018 and gap:
                    ref = ref.assign(ts=ref.ts - pd.Timedelta(hours=1))
                for i in range(5):
                    d = day + timedelta(days=i)
                    a = frames["mt5"][frames["mt5"].ts.dt.date == d]
                    b = ref[ref.ts.dt.date == d]
                    if a.empty or b.empty:
                        continue
                    raw = pd.DataFrame(
                        {
                            "time": (
                                (a.ts - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(seconds=1)
                            ).to_numpy(),
                            "close": a.bid_close.to_numpy(),
                        }
                    )
                    refm = pd.DataFrame(
                        {"ts": b.ts, "close": b.bid_close, "high": b.bid_high, "low": b.bid_low}
                    )
                    for r in weekly_offsets(raw, refm, (-1, 0, 1)).itertuples():
                        records.append(
                            {
                                "year": year,
                                "symbol": symbol,
                                "day": str(d),
                                "period": "gap" if gap else "normal",
                                "cached_minus_utc": r.offset_h,
                                "error": r.error,
                                "runner": r.runner_up_error,
                                "range": r.range,
                                "bars": r.bars,
                                "matched": r.matched,
                            }
                        )
                a = resample(frames["mt5"], Timeframe.H1)
                b = resample(ref, Timeframe.H1)
                server = a.ts.dt.tz_convert(NY).dt.tz_localize(None) + pd.Timedelta(hours=7)
                raw = pd.DataFrame(
                    {
                        "time": (server - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1),
                        "close": a.close,
                    }
                )
                for r in weekly_offsets(raw, b).itertuples():
                    weekly.append(
                        {
                            "year": year,
                            "symbol": symbol,
                            "period": "gap" if gap else "normal",
                            "week": str(r.week),
                            "offset": r.offset_h,
                            "error": r.error,
                            "runner": r.runner_up_error,
                            "range": r.range,
                        }
                    )
    data, weeks = pd.DataFrame(records), pd.DataFrame(weekly)
    data.to_csv("results/v26b_clock_matches.csv", index=False)
    weeks.to_csv("results/v26b_clock_weekly.csv", index=False)
    from backtester.data.cache_repair import QUALITY

    data["proved"] = (
        (data.matched >= QUALITY.min_match_bars)
        & (data.matched >= QUALITY.min_matched_share * data.bars)
        & (data["range"] > 0)
        & (data.error <= QUALITY.max_error_range_share * data["range"])
        & (
            data.runner
            >= QUALITY.min_runner_error_ratio * data.error
            + QUALITY.min_runner_margin_range_share * data["range"]
        )
    )
    data.to_csv("results/v26b_clock_matches.csv", index=False)
    for feed in ("histdata", "mt5"):
        with Path(f"results/clock_check_{feed}.md").open("a", encoding="utf-8") as out:
            out.write("\n## Price matches, independent anchor checked above\n\n")
            out.write(
                "2015–2018 reference cache moved one hour earlier in US/EU gap weeks, "
                "as established by FX opens. M1 daily residual uses weekly_offsets with "
                "offsets -1,0,+1; H1 reconstructs server stamps via NY+7 from cached UTC. "
                "All gap weeks plus January/July normal weeks; three symbols. "
                "No terminal connection. Raw dated CSVs: v26b_clock_matches.csv, "
                "v26b_clock_weekly.csv.\n\n"
            )
            out.write(
                "|Year|Symbol|Period|Cached time minus reference UTC (counts)|\n|---|---|---|---|\n"
            )
            out.writelines(
                "|"
                + "|".join(map(str, keys))
                + "|"
                + str(dict(Counter(group.cached_minus_utc)))
                + "|\n"
                for keys, group in data.groupby(["year", "symbol", "period"])
            )
            out.write("\n### H1 weekly_offsets overlap from 2020\n\n")
            out.write(weeks[weeks.year >= 2020].to_string(index=False) + "\n")
            out.write("\n### Conclusions and repair scope\n\n")
            if feed == "histdata":
                out.write(
                    "2015–2018: US DST proved by FX weekly opens and closes in every gap "
                    "week, corroborated by gold closes; subtract one hour from the old "
                    "gap-week UTC conversion. 2019 onward: retain European DST dates. "
                    "No pre-2015 histdata available here. Normal weeks do not change.\n"
                )
            else:
                out.write(
                    "2010–2014: FX Friday edges conflict with Sunday anchors and no "
                    "histdata reference is cached; no whole-period offset proved, exclude "
                    "non-empty days. 2015–2019: many gap days prove +1 hour, but "
                    "exceptions prohibit a single blanket rule. Repair measures EACH input "
                    "day against corrected histdata; inconclusive/short/flat days are "
                    "excluded, with dated decisions saved by the queued job. MT5-only "
                    "symbols without a reference are also excluded before 2020. Empty "
                    "weekends remain closed days; sparse/empty weekdays are missing. "
                    "No cache repair was run for this audit.\n\n"
                    "The 2020+ overlap contradicts a universal NY+7 rule: GBPUSD fits, "
                    "but XAUUSD uses an effective European-DST clock in 2020 and March "
                    "2021. These modern clock corrections require a separate decision; "
                    "the pre-2020 repair leaves modern timestamps unchanged.\n\n"
                )
                out.write(
                    "|Year|Sampled days|Strong daily proofs|Unproven (excluded if re-measurement remains inconclusive)|\n"
                    "|---|---|---|---|\n"
                )
                for year, part in data[data.year < 2020].groupby("year"):
                    proved = int(part.proved.sum())
                    out.write(f"|{year}|{len(part)}|{proved}|{len(part) - proved}|\n")
                out.write(
                    "\nUnproven sampled dates (all unsampled days are measured by the repair job):\n\n"
                )
                for (year, symbol), part in data[(data.year < 2020) & ~data.proved].groupby(
                    ["year", "symbol"]
                ):
                    out.write(f"- {year} {symbol}: {', '.join(part.day)}\n")
    Path("results/v26b_clock_match.log").write_text(
        f"{len(records)} day matches; {len(weekly)} week matches; {monotonic() - started:.2f} seconds\n",
        encoding="utf-8",
    )
    print(f"matches={len(records)}, weeks={len(weekly)}, seconds={monotonic() - started:.2f}")


if __name__ == "__main__":
    main()
