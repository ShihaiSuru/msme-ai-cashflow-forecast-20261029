#!/usr/bin/env python3
"""
MSME AI Cash Flow Forecast - Starter Script
===========================================

Practical demo of short-term cash-flow forecasting for Indian MSMEs.
Uses sample UPI / invoice / GST-style transaction data.

No external dependencies. Run with: python cashflow_forecast.py

Future extensions:
- Load real bank CSVs (UPI statement exports)
- Parse GST portal data
- Replace simple moving average with ML models
- Add natural language summary via LLM
"""

from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# ---------------------------------------------------------------------------
# Sample data: typical MSME cash movements (INR)
# Positive = inflow (UPI credits, customer payments)
# Negative = outflow (supplier payments, GST, salaries, rent)
# ---------------------------------------------------------------------------
SAMPLE_TRANSACTIONS = [
    # Past 20 days of mixed activity
    {"date": "2026-10-09", "amount": 45000, "category": "UPI Customer Payment", "note": "Invoice #1042"},
    {"date": "2026-10-10", "amount": -18000, "category": "Supplier Payment", "note": "Raw materials"},
    {"date": "2026-10-11", "amount": 12000, "category": "UPI Customer Payment", "note": "Walk-in sale"},
    {"date": "2026-10-12", "amount": -8500, "category": "GST Payment", "note": "September GST"},
    {"date": "2026-10-13", "amount": 28000, "category": "UPI Customer Payment", "note": "Invoice #1045"},
    {"date": "2026-10-14", "amount": -15000, "category": "Salary", "note": "Staff salary"},
    {"date": "2026-10-15", "amount": 60000, "category": "UPI Customer Payment", "note": "Large order"},
    {"date": "2026-10-16", "amount": -22000, "category": "Supplier Payment", "note": "Packaging"},
    {"date": "2026-10-17", "amount": 9500, "category": "UPI Customer Payment", "note": ""},
    {"date": "2026-10-18", "amount": -12000, "category": "Rent", "note": "Shop rent"},
    {"date": "2026-10-19", "amount": 33000, "category": "UPI Customer Payment", "note": "Invoice #1048"},
    {"date": "2026-10-20", "amount": -7000, "category": "Utilities", "note": ""},
    {"date": "2026-10-21", "amount": 18000, "category": "UPI Customer Payment", "note": ""},
    {"date": "2026-10-22", "amount": -25000, "category": "Supplier Payment", "note": "Inventory"},
    {"date": "2026-10-23", "amount": 41000, "category": "UPI Customer Payment", "note": "Invoice #1050"},
    {"date": "2026-10-24", "amount": -9000, "category": "GST Payment", "note": "Advance tax"},
    {"date": "2026-10-25", "amount": 15500, "category": "UPI Customer Payment", "note": ""},
    {"date": "2026-10-26", "amount": -14000, "category": "Supplier Payment", "note": ""},
    {"date": "2026-10-27", "amount": 27000, "category": "UPI Customer Payment", "note": "Invoice #1052"},
    {"date": "2026-10-28", "amount": -11000, "category": "Miscellaneous", "note": ""},
]

# Starting cash balance (INR) before the sample period
STARTING_BALANCE = 125000


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def load_transactions(transactions):
    """Convert list of dicts into sorted list of (date, amount, category)."""
    parsed = []
    for t in transactions:
        parsed.append({
            "date": parse_date(t["date"]),
            "amount": t["amount"],
            "category": t["category"],
            "note": t.get("note", ""),
        })
    return sorted(parsed, key=lambda x: x["date"])


def calculate_daily_net(transactions):
    """Group by day and compute net cash flow."""
    daily = defaultdict(float)
    for t in transactions:
        day = t["date"].date()
        daily[day] += t["amount"]
    return dict(sorted(daily.items()))


def compute_running_balance(daily_net, starting_balance):
    """Return dict of date -> ending balance."""
    balance = starting_balance
    running = {}
    for day, net in daily_net.items():
        balance += net
        running[day] = balance
    return running


def forecast_next_days(daily_net, days=30):
    """
    Simple forecast: use average daily net flow from historical data.
    Returns list of (date, projected_ending_balance).
    """
    if not daily_net:
        return []

    nets = list(daily_net.values())
    avg_daily_net = statistics.mean(nets) if nets else 0

    last_date = max(daily_net.keys())
    # Project forward
    projections = []
    current_balance = None  # will be set from running balance of last day

    # We need the last known balance; compute it quickly
    temp_balance = STARTING_BALANCE
    for day in sorted(daily_net.keys()):
        temp_balance += daily_net[day]
    current_balance = temp_balance

    for i in range(1, days + 1):
        proj_date = last_date + timedelta(days=i)
        current_balance += avg_daily_net
        projections.append((proj_date, round(current_balance, 2)))

    return projections, avg_daily_net


def estimate_working_capital(projections, safety_days=7):
    """
    Estimate buffer needed: minimum projected balance over horizon
    plus a safety margin based on recent volatility.
    """
    if not projections:
        return 0
    min_balance = min(bal for _, bal in projections)
    # Simple safety: 7 days of average absolute daily movement (proxy)
    return max(0, -min_balance) + 50000  # fixed safety floor for demo


def print_report(transactions, daily_net, running_balance, projections, avg_daily, wc_buffer):
    print("=" * 60)
    print("  MSME AI CASH FLOW FORECAST  |  Demo Report")
    print("  Date: {}".format(datetime.now().strftime("%Y-%m-%d")))
    print("=" * 60)

    total_in = sum(t["amount"] for t in transactions if t["amount"] > 0)
    total_out = sum(-t["amount"] for t in transactions if t["amount"] < 0)
    net = total_in - total_out

    print(f"\nHistorical Summary (sample period):")
    print(f"  Starting balance     : ₹{STARTING_BALANCE:,.0f}")
    print(f"  Total inflows        : ₹{total_in:,.0f}")
    print(f"  Total outflows       : ₹{total_out:,.0f}")
    print(f"  Net change           : ₹{net:,.0f}")
    last_day = max(running_balance.keys())
    print(f"  Ending balance       : ₹{running_balance[last_day]:,.0f}")

    print(f"\nAverage daily net cash flow: ₹{avg_daily:,.0f}")

    print("\n30-Day Cash Balance Forecast (simple average model):")
    print("  Date         Projected Balance")
    print("  ----------   ------------------")
    # Show every 5th day + last day for readability
    for i, (d, bal) in enumerate(projections):
        if i % 5 == 0 or i == len(projections) - 1:
            print(f"  {d.strftime('%Y-%m-%d')}   ₹{bal:,.0f}")

    print(f"\nWorking Capital Buffer Estimate: ₹{wc_buffer:,.0f}")
    print("  (Minimum projected shortfall + safety margin)")

    # Simple risk flag
    min_proj = min(bal for _, bal in projections)
    if min_proj < 20000:
        print("\n⚠️  RISK FLAG: Projected cash may fall below ₹20,000.")
        print("   Recommend: accelerate receivables or arrange short-term credit.")
    else:
        print("\n✅  Liquidity looks manageable under current patterns.")

    print("\n" + "=" * 60)
    print("This is a starter demo. Replace sample data with real UPI/GST exports")
    print("and upgrade the forecast model for production use.")
    print("=" * 60)


def main():
    transactions = load_transactions(SAMPLE_TRANSACTIONS)
    daily_net = calculate_daily_net(transactions)
    running_balance = compute_running_balance(daily_net, STARTING_BALANCE)

    projections, avg_daily = forecast_next_days(daily_net, days=30)
    wc_buffer = estimate_working_capital(projections)

    print_report(transactions, daily_net, running_balance, projections, avg_daily, wc_buffer)


if __name__ == "__main__":
    main()
