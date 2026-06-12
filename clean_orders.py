import csv
import re
import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

INPUT = 'orders_v2.csv'
OUTPUT = 'clean_orders.csv'
REPORT = 'report.md'

DATE_FORMATS = [
    '%Y-%m-%d',
    '%d/%m/%Y',
    '%d/%m/%y',
    '%d-%m-%Y',
    '%b %d, %Y',
    '%B %d, %Y',
    '%d %b %Y',
    '%d %B %Y',
]

def parse_date(s):
    # Normalize and parse a variety of date formats into ISO YYYY-MM-DD.
    s = (s or '').strip().strip('"')
    if not s:
        return ''

    # Try a set of common explicit formats first (handles DD/MM/YYYY, YYYY-MM-DD, "Apr 10, 2026", etc.)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            pass

    # Use dateutil as a flexible fallback if installed. Try day-first then month-first to handle formats like 15/03/2026.
    try:
        from dateutil import parser
        try:
            return parser.parse(s, dayfirst=True).date().isoformat()
        except Exception:
            return parser.parse(s, dayfirst=False).date().isoformat()
    except Exception:
        pass

    # Last resort: simple numeric dd/mm/yyyy pattern handling
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', s)
    if m:
        d, mo, y = m.groups()
        try:
            return datetime(int(y), int(mo), int(d)).date().isoformat()
        except Exception:
            try:
                return datetime(int(y), int(d), int(mo)).date().isoformat()
            except Exception:
                pass

    # If parsing fails, return the original trimmed string so user can inspect it.
    return s

def clean_name(s):
    # Normalize customer name: trim, collapse repeated spaces, and convert to title case.
    s = (s or '').strip()
    if not s:
        return ''
    # collapse multiple whitespace into single spaces
    parts = [p for p in re.split(r'\s+', s) if p]
    # Use title-case for readability (e.g., "ROHAN SINGH" -> "Rohan Singh")
    return ' '.join(parts).title()

def clean_amount(s):
    if s is None:
        return 0.0
    # Remove surrounding whitespace/quotes
    s = s.strip().strip('"')
    if not s:
        return 0.0
    # Remove common currency tokens like 'Rs', 'Rs.', 'INR' (case-insensitive)
    s = re.sub(r'(?i)rs\.?|inr', '', s)
    # Remove commas used as thousands separators
    s = s.replace(',', '')
    # Remove any character that is not digit or period (keeps decimals)
    s = re.sub(r'[^0-9.]', '', s)
    if s == '':
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def format_inr(amount):
    """Format a numeric amount into Indian numbering system with rupee symbol.

    Examples:
      1000 -> ₹1,000
      10500 -> ₹10,500
      100000 -> ₹1,00,000
      1234567.89 -> ₹12,34,567.89
    """
    # Use Decimal for accurate rounding/formatting
    dec = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    sign = '-' if dec < 0 else ''
    dec = abs(dec)
    int_part = int(dec)
    frac = int((dec - int_part) * 100)

    s = str(int_part)
    if len(s) <= 3:
        int_grp = s
    else:
        # last 3 digits
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        # break rest into groups of 2 from the right
        while len(rest) > 2:
            parts.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.append(rest)
        parts.reverse()
        int_grp = ','.join(parts) + ',' + last3

    if frac:
        return f"{sign}₹{int_grp}.{frac:02d}"
    else:
        return f"{sign}₹{int_grp}"

def main():
    total = 0.0
    count = 0
    rows = []
    # Determine input file: prefer orders_v2.csv, optionally fall back to orders.csv
    actual_input = INPUT
    fallback_note = ''
    if not os.path.exists(actual_input):
        if os.path.exists('orders.csv'):
            actual_input = 'orders.csv'
            fallback_note = 'Used fallback input file orders.csv because orders_v2.csv was not found.'
        else:
            raise FileNotFoundError(f"Input file not found: {INPUT}")

    with open(actual_input, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            oid = r.get('order_id','').strip()
            date = parse_date(r.get('order_date',''))
            name = clean_name(r.get('customer_name',''))
            item = r.get('item','').strip()
            amt = clean_amount(r.get('amount',''))
            # Preserve email column if present; basic cleanup (trim)
            email = (r.get('email','') or '').strip()
            total += amt
            count += 1
            # Store amount as numeric string with two decimals for CSV
            rows.append({'order_id': oid, 'order_date': date, 'customer_name': name, 'item': item, 'email': email, 'amount': f'{amt:.2f}'})

    # write cleaned CSV
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=['order_id','order_date','customer_name','item','email','amount'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # Write a Markdown report with totals and timestamp
    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    with open(REPORT, 'w', encoding='utf-8') as rep:
        rep.write('# Order Cleaning Report\n')
        rep.write('\n')
        rep.write(f'Total number of orders: {count}\n')
        rep.write(f'Total order value: {format_inr(total)}\n')
        rep.write('\n')
        rep.write(f'Report generated: {now}\n')
        if fallback_note:
            rep.write('\n')
            rep.write(f'Note: {fallback_note}\n')

    # Minimal console output: indicate files generated
    print(f'Cleaned CSV written: {OUTPUT}')
    print(f'Report written: {REPORT}')

if __name__ == '__main__':
    main()
