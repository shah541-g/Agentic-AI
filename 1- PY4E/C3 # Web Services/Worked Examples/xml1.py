import xml.etree.ElementTree as ET

data = '''
<person>
  <name>Ahmad</name>
  <phone>+92-3271152475</phone>
  <email hide="yes" />
</person>
'''


tree = ET.fromstring(data)
print(tree.find("name").text)
print(tree.find("email").get("hide"))