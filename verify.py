#!/usr/bin/env python3
"""Verify the generated data: every PAN passes Luhn, every SSN is unassignable."""

import csv
import re
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"
SAFE_RETIRED = {"078-05-1120", "219-09-9999"}


def luhn_valid(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def ssn_unassignable(ssn: str) -> bool:
    if ssn in SAFE_RETIRED:
        return True
    m = re.fullmatch(r"(\d{3})-(\d{2})-(\d{4})", ssn)
    if not m:
        return False
    area, group, serial = m.group(1), m.group(2), m.group(3)
    if area in ("000", "666") or int(area) >= 900:
        return True
    if group == "00" or serial == "0000":
        return True
    if re.fullmatch(r"987-65-43(2\d)", ssn):  # SSA advertising block
        return True
    return False


def main():
    errors = []
    rows = list(csv.DictReader((DATA / "people.csv").open()))
    for r in rows:
        if not luhn_valid(r["card_number"]):
            errors.append(f"PAN fails Luhn: {r['card_number']}")
        if not ssn_unassignable(r["ssn"]):
            errors.append(f"SSN is potentially assignable: {r['ssn']}")
        if not re.search(r"@(.+\.)?(example\.(com|net|org)|invalid)$", r["email"]):
            errors.append(f"email not in a reserved domain: {r['email']}")

    for r in csv.DictReader((DATA / "ssns.csv").open()):
        if not ssn_unassignable(r["ssn"]):
            errors.append(f"SSN is potentially assignable: {r['ssn']}")

    for r in csv.DictReader((DATA / "credit_cards.csv").open()):
        if not luhn_valid(r["number"]):
            errors.append(f"PAN fails Luhn: {r['number']}")

    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print(f"OK: {len(rows)} records -- all PANs Luhn-valid, all SSNs unassignable, "
          "all emails in reserved domains")


if __name__ == "__main__":
    main()
