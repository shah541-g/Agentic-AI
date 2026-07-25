import re

line = 'My order number is 48219'

print(re.findall('[0-9]+',line))