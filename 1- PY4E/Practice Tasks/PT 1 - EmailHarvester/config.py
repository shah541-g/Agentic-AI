from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_INPUT = BASE_DIR / "data" / "emails.json"
OUTPUT_DIR = BASE_DIR / "output"

TEXT_OUTPUT = OUTPUT_DIR / "emails_by_domain.txt"
CSV_OUTPUT = OUTPUT_DIR / "emails.csv"
JSON_REPORT = OUTPUT_DIR / "report.json"

TEXT_FIELDS = ("sender","to","cc","bcc","body")