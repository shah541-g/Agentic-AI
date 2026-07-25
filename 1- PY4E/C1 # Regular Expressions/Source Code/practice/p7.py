import re

line = 'Price: $45.99 Tax: $3.20'

print(re.findall('\$[0-9]+\.[0-9]*',line))