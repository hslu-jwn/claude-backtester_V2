"""CLI for the persistent job queue. Spec: research-runner.md > Job queue."""

import argparse
import json

from backtester.jobs.config import DEFAULT_CONFIG
from backtester.jobs.queue import Queue, Runner, queue_status


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("--name")
    add.add_argument("--priority", type=int, default=0)
    add.add_argument("--max-attempts", type=int, default=DEFAULT_CONFIG.max_attempts)
    add.add_argument("argv", nargs=argparse.REMAINDER)
    grid = sub.add_parser("add-grid")
    grid.add_argument("toml")
    grid.add_argument("--retest", action="store_true")
    grid.add_argument("--dev-only", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("--workers", type=int, default=DEFAULT_CONFIG.workers)
    run.add_argument("--max-temp", type=float, default=DEFAULT_CONFIG.max_temp)
    run.add_argument("--resume-temp", type=float, default=DEFAULT_CONFIG.resume_temp)
    run.add_argument("--poll", type=float, default=DEFAULT_CONFIG.poll)
    run.add_argument("--sensor-url", default=DEFAULT_CONFIG.sensor_url)
    run.add_argument("--drain", action="store_true")
    status = sub.add_parser("status")
    status.add_argument("--json", action="store_true")
    for command in ("cancel", "retry"):
        sub.add_parser(command).add_argument("id")
    sub.add_parser("stop")
    clean = sub.add_parser("clean")
    clean.add_argument("--done-older-than", type=float, required=True)
    return p


def main(argv=None, *, queue=None):
    p = parser()
    args = p.parse_args(argv)
    q = queue if queue is not None else Queue()
    try:
        if args.command == "add":
            command = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
            print(
                q.add(
                    command, name=args.name, priority=args.priority, max_attempts=args.max_attempts
                ).id
            )
        elif args.command == "add-grid":
            command = ["backtester.tools.research", args.toml, "--workers", "1"]
            command += ["--retest"] if args.retest else []
            command += ["--dev-only"] if args.dev_only else []
            print(q.add(command).id)
        elif args.command == "run":
            Runner(
                q,
                workers=args.workers,
                max_temp=args.max_temp,
                resume_temp=args.resume_temp,
                poll=args.poll,
                sensor_url=args.sensor_url,
            ).run(drain=args.drain)
        elif args.command == "status":
            status = queue_status(q)
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print(" ".join(f"{k}: {v}" for k, v in status["counts"].items()))
                for j in status["running"]:
                    print(f"{j['id']} {j['name']} PID {j['pid']} elapsed {j['elapsed']:.0f}s")
                temperature = status["warning"] or (
                    f"CPU {status['temperature']} °C"
                    if status["temperature"] is not None
                    else "CPU temperature not yet read"
                )
                print(
                    f"{temperature}; paused: {'yes' if status['paused'] else 'no'}; "
                    f"runner: {'running' if status['runner_alive'] else 'not running'}"
                )
                if status["last_seen"]:
                    last = status["last_seen"]
                    print(
                        f"last seen {last.get('updated', 'unknown')}: "
                        f"CPU {last.get('temperature')}; paused: {last.get('paused')}"
                    )
                if status["broken"]:
                    print("broken: " + ", ".join(status["broken"]))
        elif args.command == "cancel":
            q.cancel(args.id)
        elif args.command == "retry":
            q.retry(args.id)
        elif args.command == "stop":
            q.stop()
        elif args.command == "clean":
            print(f"Removed {q.clean(args.done_older_than)} jobs")
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        p.exit(1, f"Queue: {exc}\n")
    return 0


if __name__ == "__main__":
    main()
