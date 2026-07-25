import re

lines = ["Date is good", "No Date"]
for line in lines:
  if re.search('^Date',line):
    print(line)
