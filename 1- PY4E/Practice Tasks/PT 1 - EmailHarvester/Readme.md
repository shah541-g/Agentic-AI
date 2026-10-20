# EmailHarvester

A Python command-line tool that extracts unique email addresses from structured email JSON data, groups them by domain, analyzes contact frequency, and exports TXT, CSV, and JSON reports.

## Features

- Regex-based email extraction from sender, recipient, CC, BCC, and body fields
- Support for plus aliases and subdomains
- Case-insensitive deduplication
- Domain-based sorting and grouping
- Contact frequency across distinct email records
- TXT, CSV, and JSON report generation
- Command-line input and output paths
- Unit tests for common edge cases

## Requirements

- Python 3.10+
- No third-party dependencies

## Project Structure

```text
EmailHarvester/
├── main.py
├── config.py
├── models.py
├── extractor.py
├── normalizer.py
├── analyzer.py
├── exporters.py
├── requirements.txt
├── README.md
├── tests/
│   └── test_extractor.py
├── data/
│   └── emails.json
└── output/
```

## Usage

Run from the project directory:

```bash
python main.py
```

Specify an input file:

```bash
python main.py --input data/emails.json
```

Choose an output directory:

```bash
python main.py --input data/emails.json --output-dir output
```

## Generated Files

- `emails_by_domain.txt`: unique addresses grouped by domain.
- `emails.csv`: address, domain, source fields, and record frequency.
- `report.json`: processing totals and domain statistics.

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## Normalization Policy

Email addresses are normalized to lowercase for deduplication. Plus aliases are preserved as distinct addresses, and subdomains are retained as exact domains.

The regex performs practical pattern matching, not complete RFC validation or mailbox verification. Malformed strings that never match the regex cannot be counted as rejected candidates by the current implementation.

## Limitations

The current version loads the entire JSON document into memory. For extremely large datasets, a streaming parser or JSON Lines input format would be a useful future improvement.

## Privacy

The tool processes local files and does not send extracted addresses to external services.