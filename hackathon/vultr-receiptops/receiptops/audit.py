"""Trusted reference checker. Never imports or executes model-generated code."""
import csv
import io
import re
from collections import Counter
from datetime import date
from decimal import Decimal

AS_OF = "2026-11-08"
SAMPLE = """invoice_id,customer,amount,due_date,paid
INV-1001,Northstar Studio,1250.00,2026-10-15,true
INV-1002,Harbour Books,480.50,2026-10-21,false
INV-1003,Northstar Studio,875.00,2026-11-20,false
INV-1004,Cedar Works,320.00,2026-10-30,false
INV-1004,Cedar Works,320.00,2026-10-30,false
INV-1005,Harbour Books,149.99,2026-11-01,true
INV-1006,Valley Foods,2100.00,2026-11-05,false
INV-1007,Valley Foods,650.00,2026-12-01,false
"""
FIELDS = ["invoice_id", "customer", "amount", "due_date", "paid"]
CONTRACT = """Read /work/input.csv with columns invoice_id,customer,amount,due_date,paid.
Output ONLY one JSON object with these exact keys:
row_count (integer), total_amount (two-decimal string), paid_amount (two-decimal string),
unpaid_amount (two-decimal string), overdue_amount (two-decimal string),
duplicate_invoice_ids (sorted list of IDs appearing more than once),
overdue_invoice_ids (sorted UNIQUE list of IDs with paid=false and due_date strictly before 2026-11-08).
All sums count every row, INCLUDING duplicate IDs: report duplicates, do not silently deduplicate.
Use decimal.Decimal for money, csv.DictReader and datetime.date for dates.
paid is the literal lowercase string true or false. The as-of date is 2026-11-08.
Use Python standard library only. No files other than /work/input.csv are needed.
Do not install anything, use network, or write files. Print only the JSON result.
"""

def read_rows(content: str) -> list[dict]:
    if len(content.encode()) > 32768:
        raise ValueError("CSV must be at most 32 KiB.")
    reader = csv.DictReader(io.StringIO(content, newline=""))
    if reader.fieldnames != FIELDS:
        raise ValueError("CSV header must be: " + ",".join(FIELDS))
    rows = list(reader)
    if not 1 <= len(rows) <= 100:
        raise ValueError("Use between 1 and 100 rows.")
    for row in rows:
        if set(row) != set(FIELDS) or any(value is None for value in row.values()):
            raise ValueError("Every row must contain exactly five fields.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", row["invoice_id"]):
            raise ValueError("Invoice IDs must be short letters, numbers, dashes or underscores.")
        if not 1 <= len(row["customer"]) <= 100:
            raise ValueError("Customer names must contain 1–100 characters.")
        if not re.fullmatch(r"[0-9]{1,9}\.[0-9]{2}", row["amount"]):
            raise ValueError("Amounts must be positive two-decimal values.")
        if row["paid"] not in ("true", "false"):
            raise ValueError("paid must be true or false.")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["due_date"]):
            raise ValueError("Dates must use YYYY-MM-DD.")
        date.fromisoformat(row["due_date"])
    return rows

def reference(content: str) -> dict:
    rows = read_rows(content)
    ids = Counter(row["invoice_id"] for row in rows)
    total = paid = unpaid = overdue = Decimal("0.00")
    overdue_ids = set()
    for row in rows:
        amount = Decimal(row["amount"])
        total += amount
        if row["paid"] == "true":
            paid += amount
        else:
            unpaid += amount
            if date.fromisoformat(row["due_date"]) < date.fromisoformat(AS_OF):
                overdue += amount
                overdue_ids.add(row["invoice_id"])
    return dict(row_count=len(rows), total_amount=f"{total:.2f}",
                paid_amount=f"{paid:.2f}", unpaid_amount=f"{unpaid:.2f}",
                overdue_amount=f"{overdue:.2f}",
                duplicate_invoice_ids=sorted(k for k, v in ids.items() if v > 1),
                overdue_invoice_ids=sorted(overdue_ids))

def check(content: str, candidate: object) -> dict:
    expected = reference(content)
    differences = []
    if not isinstance(candidate, dict) or set(candidate) != set(expected):
        return {"passed": False, "differences": ["Result keys do not match the contract."]}
    for key, value in expected.items():
        if type(candidate[key]) is not type(value) or candidate[key] != value:
            differences.append(key)
    return {"passed": not differences, "differences": differences}
