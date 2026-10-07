# bwolmarans-mock-pii-data

Mock PII for testing data-loss-prevention rules, log scrubbers, AI Gateway PII
sanitizers, regex detectors, and tokenization pipelines.

**None of this data belongs to a real person.** Every value is drawn from a
range that is reserved, never-issued, or publicly voided — see
[Why this is safe](#why-this-is-safe). It is realistic enough to trip a
detector and safe enough to commit to a public repo.

## Files

| File | Contents |
| --- | --- |
| `data/people.csv` | 120 full records — name, email, phone, DOB, SSN, address, card, IP, IBAN |
| `data/people.json` | Same records as a JSON array |
| `data/people.ndjson` | Same records, one JSON object per line |
| `data/emails.txt` | 120 email addresses, one per line |
| `data/credit_cards.csv` | 120 Luhn-valid PANs with network, expiry, CVV |
| `data/ssns.csv` | Every SSN with its safety classification and why it can't be assigned |
| `data/sample_log.txt` | 40 lines of logfmt application logs with PII inline — feed this to a scrubber |

## Regenerate

```bash
python3 generate.py   # deterministic: SEED = 20261007
python3 verify.py     # asserts the safety properties below
```

No dependencies beyond the Python 3 standard library. `generate.py` is seeded,
so regenerating produces byte-identical output.

## Why this is safe

### Credit card numbers

All 120 PANs **pass the Luhn checksum**, so they exercise real validation code
paths. The first 12 records are the canonical gateway test numbers
(`4111111111111111`, `5555555555554444`, `378282246310005`, …) that payment
vendors publish specifically for testing; the rest are generated against
test/reserved IIN prefixes with a computed check digit. None map to an issued
account, so none can authorize a transaction.

### Social Security numbers

Three categories, all unassignable:

1. **Retired public specimens** — numbers that *were* real but were publicly
   voided and can never be reissued:
   - `078-05-1120` — printed on a specimen card in every Woolworth wallet sold
     in 1938. It was the SSN of Hilda Whitcher, a secretary at the wallet
     manufacturer. Over 40,000 people filed it as their own; the SSA voided it
     in 1943.
   - `219-09-9999` — used as the sample number in an SSA pamphlet, voided after
     the same thing happened.
2. **SSA advertising block** — `987-65-4320` through `987-65-4329`, a range the
   SSA reserved for advertising and training and has never issued.
3. **Structurally invalid** — numbers that violate an SSA issuance rule and
   therefore cannot exist: area `000`, area `666`, area `900`–`999`, group `00`,
   or serial `0000`.

`verify.py` re-checks every SSN in the repo against these rules.

### Email addresses

Every address uses a domain reserved by [RFC 2606](https://www.rfc-editor.org/rfc/rfc2606)
or [RFC 6761](https://www.rfc-editor.org/rfc/rfc6761) — `example.com`,
`example.net`, `example.org`, their subdomains, and `.invalid`. These domains
are guaranteed never to host a real mail server, so mail to them cannot reach
anyone.

### Everything else

- **Phone numbers** — the `555-0100`–`555-0199` block, reserved by the NANP for
  fictional use.
- **IP addresses** — RFC 5737 documentation ranges (`192.0.2.0/24`,
  `198.51.100.0/24`, `203.0.113.0/24`), not routable on the public internet.
- **Names** — invented combinations from fixed word lists; any resemblance to a
  real person is coincidental.
- **Addresses** — real city/state/ZIP combinations with invented street numbers.
  They geocode to a real town, which is usually what you want for testing, but
  no building exists at the given address.
- **IBANs** — built from the ISO 13616 published example pattern.

## Caveat

Safe data still trains bad habits. Don't wire these files into anything that
writes to a production datastore, and don't let a "this is only test data"
exception into your DLP policy — the point of this repo is to prove your
detectors fire, not to give them a bypass.
