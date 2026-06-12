# Access Log Cleaner

This small Python project reads an `access.log` file, extracts the required fields, writes them to `requests.csv`, and prints a short summary report.

## Sample `access.log` format

Each line should look like this:

```text
10.0.6.128 [2026-06-08T00:04:12Z] "POST /api/export HTTP/1.1" 201 1489ms
```

The script extracts:

- `timestamp`
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
python main.py access.log --output requests.csv
```

If you omit the log file, the script looks for `access.log` in the current folder.

## Example output

```text
Summary Report
--------------
Total requests: 500

Requests per endpoint:
  /api/orders: 117
  /api/users: 83
  /api/export: 69
  /login: 66
  /api/search: 64
  /health: 54
  /api/reports: 47

4xx errors: 8
5xx errors: 20

Cleaned data saved to: requests.csv
```

Malformed lines are skipped with a warning so the rest of the file can still be processed.