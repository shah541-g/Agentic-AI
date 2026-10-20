
import csv
import json
from pathlib import Path

from models import Contact, ProcessingReport


def export_text(
    contacts: dict[str, Contact],
    output_path: Path,
) -> None:
    grouped: dict[str, list[str]] = {}

    for contact in contacts.values():
        grouped.setdefault(contact.domain, []).append(contact.email)

    lines: list[str] = []

    for domain in sorted(grouped):
        emails = sorted(grouped[domain], key=str.lower)
        lines.append(f"Domain: {domain} ({len(emails)})")

        for email in emails:
            lines.append(f"  {email}")

        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(lines).rstrip() + "\n" if lines else "",
        encoding="utf-8",
    )


def export_csv(
    contacts: dict[str, Contact],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([
            "email",
            "domain",
            "source_types",
            "occurrences",
        ])

        for email in sorted(
            contacts,
            key=lambda value: (
                contacts[value].domain,
                value.lower(),
            ),
        ):
            contact = contacts[email]

            writer.writerow([
                contact.email,
                contact.domain,
                ";".join(sorted(contact.sources)),
                contact.occurrences,
            ])


def export_json_report(
    report: ProcessingReport,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "input_file": report.input_file,
        "total_email_records": report.total_email_records,
        "total_matches": report.total_matches,
        "unique_addresses": report.unique_addresses,
        "duplicate_matches_removed": report.duplicate_matches_removed,
        "distinct_domains": report.distinct_domains,
        "invalid_candidates_rejected": report.invalid_candidates_rejected,
        "domains": report.domains,
        "processing_seconds": report.processing_seconds,
    }

    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def export_all(
    contacts: dict[str, Contact],
    report: ProcessingReport,
    output_dir: Path,
) -> None:
    export_text(contacts, output_dir / "emails_by_domain.txt")
    export_csv(contacts, output_dir / "emails.csv")
    export_json_report(report, output_dir / "report.json")
