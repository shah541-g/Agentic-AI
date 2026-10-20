
import re


EMAIL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_.%+-])"
    r"[A-Za-z0-9_%+-]+"
    r"(?:\.[A-Za-z0-9_%+-]+)*"
    r"@"
    r"(?:[A-Za-z0-9]"
    r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}"
    r"(?![A-Za-z0-9_.-])"
)


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text."""
    if not isinstance(text, str) or not text:
        return []

    return EMAIL_PATTERN.findall(text)


def is_valid_email(email: str) -> bool:
    """Check whether the complete string matches our email pattern."""
    if not isinstance(email, str):
        return False

    return EMAIL_PATTERN.fullmatch(email.strip()) is not None
