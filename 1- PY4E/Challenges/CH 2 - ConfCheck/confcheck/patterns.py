"""
Compiled regular expressions for ConfCheck.

Every recognizing, tokenizing, stripping, and type-detection step in ConfCheck
must be performed exclusively using the compiled patterns in this module.
No config/INI/TOML/YAML parser libraries are used anywhere.
"""

import re

# Matches empty or whitespace-only lines.
BLANK = re.compile(r'^\s*$')

# Matches full-line comments whose first non-whitespace character is ; or #.
COMMENT = re.compile(r'^\s*[;#]')

# Matches section header: [name] at column 0.
# Section name may contain letters, digits, _, ., -, and spaces.
# Trailing whitespace and comments are permitted.
SECTION = re.compile(r'^\[\s*(?P<name>[A-Za-z0-9_.\-](?:[A-Za-z0-9_.\- ]*[A-Za-z0-9_.\-])?)\s*\][ \t]*(?:[;#].*)?$')

# Matches lines that start with [ at column 0 but failed the valid SECTION pattern.
BAD_SECTION = re.compile(r'^\s*\[')

# Matches key-value definitions at column 0.
# Key begins with letter or _, followed by letters, digits, _, ., -.
# Separator is = or :, surrounded by optional spaces or tabs.
KEY_VALUE = re.compile(r'^(?P<key>[A-Za-z_][A-Za-z0-9_.\-]*)[ \t]*(?P<sep>[=:])[ \t]*(?P<value>.*)$')

# Matches continuation lines indented with at least one space or tab.
CONTINUATION = re.compile(r'^[ \t]+(?P<text>\S.*)$')

# Matches a trailing backslash line continuation marker with optional preceding whitespace.
BACKSLASH_END = re.compile(r'[ \t]*\\$')

# Matches line content before an inline comment (; or # preceded by whitespace outside quotes).
# Pairs of quotes ("..." or '...') are consumed whole so comments inside quotes are preserved.
# If quotes are unmatched (e.g. apostrophe in it's), individual characters are matched one by one.
INLINE_COMMENT = re.compile(
    r'''^(?P<body>(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|(?!\s+[;#]).)*?)(?:\s+[;#].*)?$''',
    re.DOTALL,
)

# Matches fully quoted strings enclosed in matching single or double quotes.
QUOTED = re.compile(r'''^(?P<q>["'])(?P<body>(?:(?!(?P=q)|\\).|\\.)*)(?P=q)$''', re.DOTALL)

# Matches any single or double quoted span within a string.
QUOTED_SPAN = re.compile(r'''"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*\'''')

# Matches list items separated by commas outside quotes.
LIST_ITEM = re.compile(r'''(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[^,])+''')

# Matches backslash escape sequences like \n, \t, \", \', \\.
ESCAPE = re.compile(r'\\(.)', re.DOTALL)

# Matches boolean literals (case-insensitive true/yes/on and false/no/off).
BOOL = re.compile(r'^(?:(?P<true>true|yes|on)|(?P<false>false|no|off))$', re.IGNORECASE)

# Matches integer literals with optional sign, including leading zeros.
INT = re.compile(r'^[+-]?\d+$')

# Matches a schema rule declaration, e.g. str, required or list[int], min=1, max=100.
RULE = re.compile(
    r'^(?P<type>str|int|bool|list)(?:\[(?P<item>str|int|bool)\])?(?P<opts>(?:\s*,\s*[a-z]+(?:=[^,]*)?)*)\s*$'
)

# Extracts individual options from a schema rule's option list.
RULE_OPT = re.compile(r'\s*,\s*(?P<name>[a-z]+)(?:=(?P<val>[^,]*))?')
