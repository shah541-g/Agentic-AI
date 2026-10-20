
from models import Contact, ProcessingReport


def analyze_contacts(
    contacts: dict[str, Contact],
    input_file: str,
    total_email_records: int,
    total_matches: int,
    invalid_candidates_rejected: int,
    processing_seconds: float = 0.0,
) -> ProcessingReport:

    domain_counts: dict[str, int] = {}

    for contact in contacts.values():
        domain_counts[contact.domain] = (
            domain_counts.get(contact.domain, 0) + 1
        )

    unique_count = len(contacts)

    return ProcessingReport(
        input_file=input_file,
        total_email_records=total_email_records,
        total_matches=total_matches,
        unique_addresses=unique_count,
        duplicate_matches_removed=max(0, total_matches - unique_count),
        distinct_domains=len(domain_counts),
        invalid_candidates_rejected=invalid_candidates_rejected,
        domains=dict(sorted(domain_counts.items())),
        processing_seconds=round(processing_seconds, 4),
    )
