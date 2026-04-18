"""Entry-point CLI for logwatch-cli."""
import sys
import signal
import argparse

from logwatch.tailer import tail_file, tail_lines
from logwatch.filter import build_filter, combined
from logwatch.alerts import check_alerts
from logwatch.alert_config import load_rules_from_yaml, default_rules
from logwatch.output import OutputSink
from logwatch.stats import SessionStats


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logwatch",
        description="Tail and filter structured logs with pattern alerts.",
    )
    p.add_argument("file", help="Log file to watch")
    p.add_argument("-n", "--lines", type=int, default=0,
                   help="Print last N lines before tailing (0 = skip)")
    p.add_argument("-l", "--level", default="INFO",
                   help="Minimum log level to display (default: INFO)")
    p.add_argument("-p", "--pattern", default=None,
                   help="Regex pattern to match against log messages")
    p.add_argument("-o", "--output", default=None,
                   help="Write output to file instead of stdout")
    p.add_argument("--alerts", default=None,
                   help="YAML file with alert rules")
    p.add_argument("--stats", action="store_true",
                   help="Print session statistics on exit")
    return p


def run(argv=None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    rules = load_rules_from_yaml(args.alerts) if args.alerts else default_rules()
    log_filter = build_filter(level=args.level, pattern=args.pattern)
    session = SessionStats()

    sink = OutputSink(path=args.output)

    def _shutdown(sig, frame):
        if args.stats:
            print(session.format_summary(), file=sys.stderr)
        sink.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    with sink:
        if args.lines > 0:
            for entry in tail_lines(args.file, args.lines):
                if log_filter(entry):
                    session.record_entry(entry)
                    sink.write_entry(entry)
                    for alert in check_alerts(entry, rules):
                        session.record_alert(alert.name)
                        sink.write_alert(alert, entry)

        for entry in tail_file(args.file):
            if log_filter(entry):
                session.record_entry(entry)
                sink.write_entry(entry)
                for alert in check_alerts(entry, rules):
                    session.record_alert(alert.name)
                    sink.write_alert(alert, entry)


if __name__ == "__main__":
    run()
