import re

line = 'From stephen.marquard@uct.ac.za Sat Jan 5 09:14:16 2008'

print(re.findall(r'From (.*?)@(\S*)', line))