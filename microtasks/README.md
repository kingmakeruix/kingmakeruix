# Nodo131 Paid Microtasks

Small, dependency-free tools that demonstrate the exact work offered through
Nodo131's buyer-funded microservice listings.

This repository is a capability sample, not a claim of paid client work.
Production work starts only after the marketplace marks an order as funded or
escrowed.

## Included tools

### CSV audit and deduplication

`csv_audit.py` reads UTF-8 CSV, preserves the first occurrence of each non-empty
key, flags missing fields, and emits an exact JSON audit report.

```bash
python csv_audit.py sample.csv --key-field order_id --output cleaned.csv
```

The report includes:

- rows read and rows written;
- duplicate row locations and their first occurrence;
- rows containing missing values;
- rows with an empty key field.

### Read-only HTTPS API probe

`api_probe.py` performs safe `GET` requests against up to five public HTTPS
URLs and reports status, latency, content type, redirect destination, response
size, and JSON validity.

```bash
python api_probe.py https://example.com/status
```

The probe rejects non-HTTPS URLs, does not send credentials, and never performs
state-changing requests.

## Tests

```bash
python -m unittest discover -s tests -v
```

All tests are local and deterministic; they do not require network access.

## Paid service boundaries

- Buyer supplies sanitized public data or public HTTPS endpoints.
- No authentication bypass, exploitation, load testing, private-data access,
  financial transaction, or state-changing request.
- Buyer-funded marketplace order or escrow is required before custom work.

## License

MIT
