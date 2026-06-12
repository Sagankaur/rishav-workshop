from __future__ import annotations

import argparse
import csv
import logging
import re
from collections import Counter
from pathlib import Path


LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<endpoint>\S+) HTTP/(?P<http_version>\d\.\d)" '
    r'(?P<status>\d{3}) (?P<response_ms>\d+)ms$'
)


def parse_log(log_path: Path) -> list[dict[str, object]]:
    """Parse an access log file into structured request records."""

    records: list[dict[str, object]] = []

    with log_path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                logging.warning("Skipping empty line %s", line_number)
                continue

            match = LOG_PATTERN.match(line)
            if match is None:
                logging.warning("Skipping malformed line %s: %s", line_number, line)
                continue

            records.append(
                {
                    "timestamp": match.group("timestamp"),
                    "endpoint": match.group("endpoint"),
                    "status": int(match.group("status")),
                    "response_ms": int(match.group("response_ms")),
                }
            )

    return records


def save_to_csv(records: list[dict[str, object]], csv_path: Path) -> None:
    """Write parsed log records to a CSV file."""

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp", "endpoint", "status", "response_ms"],
        )
        writer.writeheader()
        writer.writerows(records)


def count_requests_per_endpoint(records: list[dict[str, object]]) -> Counter[str]:
    """Count how many requests were made to each endpoint."""

    return Counter(str(record["endpoint"]) for record in records)


def count_errors(records: list[dict[str, object]]) -> dict[str, int]:
    """Count 4xx client errors and 5xx server errors."""

    client_errors = 0
    server_errors = 0

    for record in records:
        status = int(record["status"])
        if 400 <= status < 500:
            client_errors += 1
        elif 500 <= status < 600:
            server_errors += 1

    return {"4xx": client_errors, "5xx": server_errors}


def generate_report(records: list[dict[str, object]]) -> str:
    """Create a human-readable summary report for the parsed requests."""

    endpoint_counts = count_requests_per_endpoint(records)
    error_counts = count_errors(records)

    lines = ["Summary Report", "--------------"]
    lines.append(f"Total requests: {len(records)}")
    lines.append("")
    lines.append("Requests per endpoint:")

    for endpoint, count in sorted(endpoint_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"  {endpoint}: {count}")

    lines.append("")
    lines.append(f"4xx errors: {error_counts['4xx']}")
    lines.append(f"5xx errors: {error_counts['5xx']}")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse access logs into CSV and print a summary report.")
    parser.add_argument(
        "log_file",
        nargs="?",
        default="access.log",
        help="Path to the access.log file (defaults to ./access.log).",
    )
    parser.add_argument(
        "--output",
        default="requests.csv",
        help="Path to the output CSV file (defaults to ./requests.csv).",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for malformed line warnings.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")

    log_path = Path(args.log_file)
    output_path = Path(args.output)

    records = parse_log(log_path)
    save_to_csv(records, output_path)

    print(generate_report(records))
    print()
    print(f"Cleaned data saved to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())