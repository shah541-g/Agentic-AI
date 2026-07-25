import re

line = 'ERROR 2026-06-12 14:30:01 Disk full on server-3'

print(re.findall(r'^ERROR ([0-9]{4}-[0-9]{2}-[0-9]{2}) (\d{2}:\d{2}:\d{2}).*?(server-[0-9]+)',line))