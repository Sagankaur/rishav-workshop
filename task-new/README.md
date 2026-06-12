# Access Log Cleaner

This small Python project reads an `access.log` file, extracts the required fields, writes them to `requests.csv`, and creates a Markdown report in `summary.md`.

## Sample `access.log` format

Each line should look like this:

```text
10.0.6.128 [2026-06-08T00:04:12Z] "POST /api/export HTTP/1.1" 201 1489ms
```

The script extracts:

- `timestamp`
- `date`
- `endpoint`
- `status`
- `response_ms`

## How to run

From the `task-new` folder, run:

```bash
python main.py access.log
```

You can also choose a different output name:

```bash
python main.py access.log --output requests.csv --summary summary.md
```

If you omit the log file, the script looks for `access.log` in the current folder.

## Example output

```text
# Log Report

## Total Requests
500

## Requests Per Endpoint
| Endpoint | Count |
|----------|------:|
| /api/orders | 117 |
| /api/users | 83 |
| /api/export | 69 |
| /login | 66 |
| /api/search | 64 |
| /health | 54 |
| /api/reports | 47 |

## Error Summary
- 4xx Errors: 8
- 5xx Errors: 20

## Per-Day Breakdown
| Date | Requests |
|------|----------:|
| 2026-06-08 | 100 |
| 2026-06-09 | 88 |
| 2026-06-10 | 103 |
| 2026-06-11 | 122 |
| 2026-06-12 | 87 |

## Top 3 Slowest Endpoints
| Endpoint | Average Response Time (ms) |
|----------|---------------------------:|
| /api/export | 1356.80 |
| /api/reports | 909.77 |
| /api/search | 550.91 |
```

Malformed lines are skipped with a warning so the rest of the file can still be processed.