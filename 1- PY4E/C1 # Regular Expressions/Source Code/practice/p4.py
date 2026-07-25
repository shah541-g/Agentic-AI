import re

line = 'Order 482 has 19 items' 

print(re.findall('[0-9]+',line))