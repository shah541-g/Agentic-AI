from dataclasses import dataclass, field

@dataclass
class Contact:
  email: str
  domain: str
  sources: set[str] = field(default_factory=set)
  occurrences: int = 0
  
@dataclass
class ProcessingReport:
  input_file: str
  total_email_records: int
  total_matches: int
  unique_addresses: int
  duplicate_matches_removed: int
  distinct_domains: int
  invalid_candidates_rejected: int
  domains: dict[str,str] = field(default_factory=dict)
  processing_seconds: float = 0.0
  