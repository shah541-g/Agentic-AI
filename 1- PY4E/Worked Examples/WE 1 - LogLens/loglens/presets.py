"""
Predefined regex patterns for common log formats.

For someone familiar with Regular Expressions (regex):
- Python's re module supports named capture groups using the syntax: (?P<group_name>pattern)
- LogLens uses these named capture groups to dynamically derive table column headers and export keys.
- If a group is not named (e.g. (?:...) non-capturing group or ordinary (...) group), LogLens ignores
  it for column generation and only uses it for structural matching.
"""

import re
from typing import Dict

# Dictionary mapping preset names to compiled regular expression patterns.
PRESETS: Dict[str, re.Pattern] = {
    # Nginx / Combined Log Format:
    # Example: 192.168.1.5 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1024 "-" "Mozilla/5.0"
    "nginx": re.compile(
        r'^(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<time>[^\]]+)\] '
        r'"(?P<method>[A-Z]+) (?P<path>\S+) (?P<protocol>[^"]+)" '
        r'(?P<status>\d{3}) (?P<size>\d+|-) '
        r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"$'
    ),
    # Standard RFC 3164 Syslog Format:
    # Example: Oct 10 13:55:36 myhost sshd[1234]: Failed password for root from 10.0.0.9 port 22 ssh2
    "syslog": re.compile(
        r'^(?P<time>\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2}) (?P<host>\S+) '
        r'(?P<process>[^\[:]+)(?:\[(?P<pid>\d+)\])?: (?P<message>.*)$'
    ),
    # Generic Application Log Format:
    # Example: 2025-10-10 13:55:36 ERROR Database connection timed out
    # Also handles: 2025-10-10T13:55:36.123 [INFO] User login successful
    "generic": re.compile(
        r'^(?P<time>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\s+'
        r'\[?(?P<level>DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\]?\s+'
        r'(?P<message>.*)$'
    ),
}

# Apache Combined Log Format is identical to standard Nginx combined log format
PRESETS["apache"] = PRESETS["nginx"]
