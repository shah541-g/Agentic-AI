import re

line = 'Loving #python and #regex today #100DaysOfCode'

hashTags = []
hashTags.extend(re.findall(r'\s(#\w+)',line))
print(hashTags)