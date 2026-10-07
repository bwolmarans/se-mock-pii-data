#!/usr/bin/env python3
"""Generate deterministic mock PII datasets.

Everything emitted here is synthetic. See README.md for why each category is
safe to commit, publish, and send through log pipelines.

Usage: python3 generate.py
"""

import csv
import json
import random
from pathlib import Path

SEED = 20261007
OUT = Path(__file__).parent / "data"

# --- Names -------------------------------------------------------------------

FIRST = [
    "Ada", "Blaise", "Cleo", "Dmitri", "Esperanza", "Fenwick", "Greta", "Hiro",
    "Imani", "Jalen", "Kestrel", "Lourdes", "Mateo", "Nadia", "Oisin", "Priya",
    "Quill", "Rosalind", "Soren", "Tamsin", "Ulric", "Vashti", "Wendell",
    "Xiomara", "Yusuf", "Zelda", "Ambrose", "Beatrix", "Caspian", "Delphine",
]

LAST = [
    "Abernathy", "Blackwood", "Castellanos", "Duvall", "Eriksen", "Fairweather",
    "Grimaldi", "Haverford", "Ibarra", "Jorgensen", "Kowalczyk", "Lindqvist",
    "Montenegro", "Nakashima", "Okonkwo", "Pemberton", "Quintanilla", "Rutherford",
    "Stavropoulos", "Thackeray", "Ueda", "Vasquez", "Whitlock", "Xanthopoulos",
    "Yarborough", "Zimmerman", "Ashworth", "Brightwater", "Calloway", "Doyle",
]

# RFC 2606 / RFC 6761 reserved domains: guaranteed never to resolve to a real
# mail server, so these addresses can never reach a real person.
DOMAINS = [
    "example.com", "example.net", "example.org",
    "test.example.com", "mail.example.net", "corp.example.org",
    "invalid", "localhost.example.com",
]

CITIES = [
    ("Springfield", "IL", "62704"), ("Riverton", "WY", "82501"),
    ("Fairview", "OR", "97024"), ("Greenville", "SC", "29601"),
    ("Clinton", "IA", "52732"), ("Madison", "WI", "53703"),
    ("Georgetown", "DE", "19947"), ("Salem", "MA", "01970"),
    ("Arlington", "TX", "76010"), ("Bristol", "VA", "24201"),
]

# --- Credit cards ------------------------------------------------------------

# (network, IIN prefix, total length). All prefixes below sit in test/reserved
# BIN space published by the card networks and gateway vendors.
CARD_SPECS = [
    ("visa", "4111", 16),
    ("visa", "4012888888", 16),
    ("visa", "4222", 16),
    ("mastercard", "5555555555", 16),
    ("mastercard", "5105105105", 16),
    ("mastercard", "2223", 16),
    ("amex", "378282", 15),
    ("amex", "371449", 15),
    ("discover", "6011", 16),
    ("discover", "6011000990", 16),
    ("diners", "30569309", 14),
    ("jcb", "3530111333", 16),
]

# Canonical gateway test numbers, reproduced verbatim because tooling often
# special-cases these exact strings.
KNOWN_TEST_CARDS = [
    ("visa", "4111111111111111"),
    ("visa", "4012888888881881"),
    ("visa", "4222222222222"),
    ("mastercard", "5555555555554444"),
    ("mastercard", "5105105105105100"),
    ("mastercard", "2223003122003222"),
    ("amex", "378282246310005"),
    ("amex", "371449635398431"),
    ("discover", "6011111111111117"),
    ("discover", "6011000990139424"),
    ("diners", "30569309025904"),
    ("jcb", "3530111333300000"),
]


def luhn_check_digit(partial: str) -> str:
    """Return the digit that makes `partial + digit` pass the Luhn checksum."""
    total = 0
    # The appended check digit will occupy an odd position from the right (1),
    # so the rightmost digit of `partial` is position 2 and gets doubled.
    for i, ch in enumerate(reversed(partial)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


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


def make_card(rng: random.Random, prefix: str, length: int) -> str:
    body = prefix + "".join(str(rng.randrange(10)) for _ in range(length - len(prefix) - 1))
    return body + luhn_check_digit(body)


# --- SSNs --------------------------------------------------------------------

# Every SSN below is structurally impossible to belong to a living person.
# (See README.md for the SSA rules each one violates.)

# Reserved by the SSA for advertising and training use.
SSN_ADVERTISING = [f"987-65-43{n:02d}" for n in range(20, 30)]

# Historically issued, then publicly voided by the SSA. "Real at one point,
# now permanently invalid" -- these are the ones you asked about by name.
SSN_RETIRED = [
    ("078-05-1120", "Woolworth 'Hilda Whitcher' specimen wallet card, voided by SSA in 1943"),
    ("219-09-9999", "SSA pamphlet sample number, voided after public misuse"),
]


def structurally_invalid_ssns(rng: random.Random, n: int):
    """SSNs that violate an SSA issuance rule and can never be assigned."""
    out = []
    kinds = ["area_000", "area_666", "area_9xx", "group_00", "serial_0000"]
    for i in range(n):
        kind = kinds[i % len(kinds)]
        if kind == "area_000":
            area, group, serial = "000", rng.randrange(1, 100), rng.randrange(1, 10000)
        elif kind == "area_666":
            area, group, serial = "666", rng.randrange(1, 100), rng.randrange(1, 10000)
        elif kind == "area_9xx":
            area, group, serial = str(rng.randrange(900, 1000)), rng.randrange(1, 100), rng.randrange(1, 10000)
        elif kind == "group_00":
            area, group, serial = f"{rng.randrange(1, 666):03d}", 0, rng.randrange(1, 10000)
        else:
            area, group, serial = f"{rng.randrange(1, 666):03d}", rng.randrange(1, 100), 0
        out.append((f"{area}-{group:02d}-{serial:04d}", kind))
    return out


# --- Other identifiers -------------------------------------------------------

def phone(rng: random.Random) -> str:
    """555-0100..555-0199 is the NANP block reserved for fictional use."""
    area = rng.choice([201, 212, 310, 415, 512, 617, 718, 206, 303, 404])
    return f"+1-{area}-555-{rng.randrange(100, 200):04d}"


def ipv4(rng: random.Random) -> str:
    """RFC 5737 documentation ranges -- not routable on the public internet."""
    block = rng.choice(["192.0.2", "198.51.100", "203.0.113"])
    return f"{block}.{rng.randrange(1, 255)}"


def iban(rng: random.Random) -> str:
    # GB82 WEST ... is the ISO 13616 published example IBAN pattern.
    return "GB82WEST1234569876" + f"{rng.randrange(10, 100)}"


def dob(rng: random.Random) -> str:
    return f"{rng.randrange(1945, 2006)}-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}"


def email(first: str, last: str, i: int, rng: random.Random) -> str:
    style = i % 5
    f, l = first.lower(), last.lower()
    local = [f"{f}.{l}", f"{f[0]}{l}", f"{f}_{l}{i}", f"{l}.{f}", f"{f}{i}"][style]
    return f"{local}@{rng.choice(DOMAINS)}"


# --- Build -------------------------------------------------------------------

def build_people(n=120):
    rng = random.Random(SEED)
    adv = SSN_ADVERTISING
    invalid = structurally_invalid_ssns(rng, n)
    people = []
    for i in range(n):
        first = FIRST[i % len(FIRST)]
        last = LAST[(i * 7 + 3) % len(LAST)]
        city, state, zipc = CITIES[i % len(CITIES)]
        if i < len(SSN_RETIRED):
            ssn, ssn_class = SSN_RETIRED[i][0], "retired-public-specimen"
        elif i < len(SSN_RETIRED) + len(adv):
            ssn, ssn_class = adv[i - len(SSN_RETIRED)], "ssa-advertising-reserved"
        else:
            ssn, ssn_class = invalid[i][0], f"structurally-invalid:{invalid[i][1]}"

        if i < len(KNOWN_TEST_CARDS):
            network, pan = KNOWN_TEST_CARDS[i]
        else:
            network, prefix, length = CARD_SPECS[i % len(CARD_SPECS)]
            pan = make_card(rng, prefix, length)
        assert luhn_valid(pan), pan

        people.append({
            "id": i + 1,
            "first_name": first,
            "last_name": last,
            "email": email(first, last, i, rng),
            "phone": phone(rng),
            "date_of_birth": dob(rng),
            "ssn": ssn,
            "ssn_safety_class": ssn_class,
            "street": f"{rng.randrange(10, 9999)} {rng.choice(['Maple','Oak','Cedar','Birch','Willow','Aspen'])} {rng.choice(['St','Ave','Rd','Ln','Way'])}",
            "city": city,
            "state": state,
            "postal_code": zipc,
            "card_network": network,
            "card_number": pan,
            "card_exp": f"{rng.randrange(1, 13):02d}/{rng.randrange(27, 33)}",
            "card_cvv": f"{rng.randrange(100, 1000)}" if network != "amex" else f"{rng.randrange(1000, 10000)}",
            "ipv4": ipv4(rng),
            "iban": iban(rng),
        })
    return people


def main():
    OUT.mkdir(exist_ok=True)
    people = build_people()
    fields = list(people[0].keys())

    with (OUT / "people.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(people)

    (OUT / "people.json").write_text(json.dumps(people, indent=2) + "\n")

    with (OUT / "people.ndjson").open("w") as f:
        for p in people:
            f.write(json.dumps(p) + "\n")

    with (OUT / "emails.txt").open("w") as f:
        f.write("\n".join(p["email"] for p in people) + "\n")

    with (OUT / "credit_cards.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["network", "number", "exp", "cvv", "luhn_valid"])
        for p in people:
            w.writerow([p["card_network"], p["card_number"], p["card_exp"],
                        p["card_cvv"], luhn_valid(p["card_number"])])

    with (OUT / "ssns.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ssn", "safety_class", "note"])
        for ssn, note in SSN_RETIRED:
            w.writerow([ssn, "retired-public-specimen", note])
        for ssn in SSN_ADVERTISING:
            w.writerow([ssn, "ssa-advertising-reserved",
                        "Reserved by SSA for advertising; never issued"])
        for p in people:
            if p["ssn_safety_class"].startswith("structurally-invalid"):
                w.writerow([p["ssn"], p["ssn_safety_class"],
                            "Violates an SSA issuance rule; cannot be assigned"])

    with (OUT / "sample_log.txt").open("w") as f:
        for p in people[:40]:
            f.write(
                f'2026-10-07T12:{p["id"]%60:02d}:00Z level=info svc=checkout '
                f'user_id={p["id"]} email={p["email"]} ip={p["ipv4"]} '
                f'pan={p["card_number"]} ssn={p["ssn"]} msg="order placed"\n'
            )

    print(f"wrote {len(people)} records to {OUT}/")
    for path in sorted(OUT.iterdir()):
        print(f"  {path.name}")


if __name__ == "__main__":
    main()
