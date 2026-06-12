from __future__ import annotations

import argparse
import csv
import logging
import re
from collections import Counter
from datetime import datetime
from statistics import mean
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
                    "date": _extract_date(match.group("timestamp")),
                    "endpoint": match.group("endpoint"),
                    "status": int(match.group("status")),
                    "response_ms": int(match.group("response_ms")),
                }
            )

    return records


def _extract_date(timestamp: str) -> str:
    """Return the date portion of an ISO-8601 timestamp."""

    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date().isoformat()


def save_to_csv(records: list[dict[str, object]], csv_path: Path) -> None:
    """Write parsed log records to a CSV file."""

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp", "date", "endpoint", "status", "response_ms"],
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


def daily_breakdown(records: list[dict[str, object]]) -> Counter[str]:
    """Count the number of requests per day."""

    return Counter(str(record["date"]) for record in records)


def top_slowest_endpoints(records: list[dict[str, object]], limit: int = 3) -> list[tuple[str, float]]:
    """Return the endpoints with the highest average response time."""

    response_times_by_endpoint: dict[str, list[int]] = {}
    for record in records:
        endpoint = str(record["endpoint"])
        response_times_by_endpoint.setdefault(endpoint, []).append(int(record["response_ms"]))

    averages = [(endpoint, mean(values)) for endpoint, values in response_times_by_endpoint.items()]
    return sorted(averages, key=lambda item: (-item[1], item[0]))[:limit]


def generate_summary_markdown(records: list[dict[str, object]]) -> str:
    """Create a Markdown report for the parsed requests."""

    endpoint_counts = count_requests_per_endpoint(records)
    error_counts = count_errors(records)
    day_counts = daily_breakdown(records)
    slowest_endpoints = top_slowest_endpoints(records)

    lines = ["# Log Report", ""]
    lines.append("## Total Requests")
    lines.append(f"{len(records)}")
    lines.append("")
    lines.append("## Requests Per Endpoint")
    lines.append("| Endpoint | Count |")
    lines.append("|----------|------:|")
    for endpoint, count in sorted(endpoint_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {endpoint} | {count} |")

    lines.append("")
    lines.append("## Error Summary")
    lines.append(f"- 4xx Errors: {error_counts['4xx']}")
    lines.append(f"- 5xx Errors: {error_counts['5xx']}")

    lines.append("")
    lines.append("## Per-Day Breakdown")
    lines.append("| Date | Requests |")
    lines.append("|------|----------:|")
    for day, count in sorted(day_counts.items()):
        lines.append(f"| {day} | {count} |")

    lines.append("")
    lines.append("## Top 3 Slowest Endpoints")
    lines.append("| Endpoint | Average Response Time (ms) |")
    lines.append("|----------|---------------------------:|")
    for endpoint, avg_response_ms in slowest_endpoints:
        lines.append(f"| {endpoint} | {avg_response_ms:.2f} |")

    return "\n".join(lines)


def save_summary_markdown(records: list[dict[str, object]], summary_path: Path) -> None:
    """Write the Markdown report to disk."""

    summary_path.write_text(generate_summary_markdown(records), encoding="utf-8")


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
        "--summary",
        default="summary.md",
        help="Path to the output Markdown summary (defaults to ./summary.md).",
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
    summary_path = Path(args.summary)

    records = parse_log(log_path)
    save_to_csv(records, output_path)
    save_summary_markdown(records, summary_path)

    print(generate_summary_markdown(records))
    print()
    print(f"Cleaned data saved to: {output_path}")
    print(f"Markdown summary saved to: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())