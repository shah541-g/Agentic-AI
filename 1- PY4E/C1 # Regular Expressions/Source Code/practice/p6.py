import re

line = 'From: alice To: bob' 

print(re.findall('^F.+?:',line))