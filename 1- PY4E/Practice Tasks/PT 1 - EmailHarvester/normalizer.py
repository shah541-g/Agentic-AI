from collections.abc import Iterable

from extractor import extract_emails
from models import Contact



def normalize_email(email: str) -> str:
    """Normalize email casing while preserving plus aliases."""
    email = email.strip()

    local, separator, domain = email.rpartition("@")

    if not separator or not local or not domain:
        return ""

    return f"{local.lower()}@{domain.lower()}"


def get_domain(email:str) -> str:
  return email.rpartition('@')[2].lower()

def build_contacts(
  records: list[dict],
  fields: tuple[str,...] = ("sender", "to", "cc", "bcc", "body"),
) -> tuple[dict[str,Contact],int,int]:
  """
  Returns:
    contacts, total_matches, invalid_candidates_rejected
  """
  contacts: dict[str,Contact] = {}
  total_matches = 0
  invalid_candidates_rejected = 0
  
  for record in records:
    record_id = str(record.get("id", ""))
    
    # Preventing repeated appearances in one record from inflating frequency
    record_emails: dict[str, set[str]] = {}
    
    for field_name in fields:
      value = record.get(field_name,"")
      
      if not isinstance(value, str):
        continue
      
      for raw_email in extract_emails(value):
        total_matches+=1
        normalized = normalize_email(raw_email)
        
        if not normalized or "@" not in normalized:
          invalid_candidates_rejected += 1
          continue
        
        domain = get_domain(normalized)
        
        if not domain:
          invalid_candidates_rejected += 1
          continue
        
        source = field_name
        record_emails.setdefault(normalized, set()).add(source)
    
    for email, sources in record_emails.items():
      if email not in contacts:
        contacts[email] = Contact(
          email=email,
          domain=get_domain(email)
        )
        
      contact = contacts[email]
      contact.sources.update(sources)
      contact.occurrences += 1
      
  return contacts, total_matches, invalid_candidates_rejected


  