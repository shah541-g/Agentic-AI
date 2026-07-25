import re

email = 'word@word.word'

print(re.search(r'^.+@.+\..+$',email))
