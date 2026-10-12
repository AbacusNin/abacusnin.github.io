# Transaction review from merchant category codes

This offline proof of concept takes a transaction CSV with `timestamp`, `merchant`, `mcc`, and `amount`. It reports the five operations in the case: count by a reference MCC, list merchant names within a category, find the most frequent code, sum a category's spend, and count amounts strictly above a threshold. The source dataset is unavailable; `synthetic_transactions.csv` is an invented six-row test fixture and must not be read as the challenge data.

```sh
python -B transaction_review.py synthetic_transactions.csv --entity-mcc 3795 --category-mcc 5311 --spend-mcc 8011 --threshold 50 --name-hint hotel
python -B -m unittest test_transaction_review.py -v
```

The `--name-hint` comparison shows why a zero name match needs another path. An MCC describes a business category; most codes do not identify a specific merchant. Code 3795 is brand-specific in Visa's published list, but a code match still needs dataset and reference-table context. The tool refuses to name a unique merchant when multiple names appear in the selected category. It rejects invalid amounts, limits input to 10 MB and 100,000 rows, and makes no network requests.

The output is a review aid. It does not score money-laundering risk, identify structuring, validate merchant ownership, or make an AML filing decision. Real use would need an approved reference table, account/merchant IDs, currency and time-zone handling, data lineage, and analyst review. Avoid submitting cardholder identifiers or other sensitive financial data to a public test environment.

`mcc_lookup.py` searches the four-entry `mcc_reference.csv` excerpt checked against the Visa Merchant Data Standards Manual. It is intentionally incomplete. `category_review.yml` is an informational Sigma selection for a normalized transaction event with string MCC values, and `synthetic_review_stix.json` records a procedural course of action without inventing an IOC or actor. The Sigma rule still needs field mapping and backend conversion before use; the STIX file is a demonstration of representation, not an intelligence distribution.

`synthetic_category_events.jsonl` supplies a selected category, ordinary category, and one-digit near miss. `test_category_review.py` parses the Sigma rule with pySigma and checks those three cases. This requires PyYAML and pySigma for the test only; the CSV reviewer itself uses the Python standard library.
