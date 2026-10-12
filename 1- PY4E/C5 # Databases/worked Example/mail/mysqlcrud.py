import mysql.connector

conn = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root123",
  database="emailDB"
)

crr = conn.cursor()

crr.execute("DROP TABLE IF EXISTS COUNTS")
crr.execute("CREATE TABLE COUNTS (email VARCHAR(20), count INT)")

file = input("Enter File Name: ")
if len(file) == 0:
  file = "mbox-text.txt"
  
fh = open(file)

for line in fh:
  if not line.startswith("From: "):
    continue
  
  data = line.split()
  email = data[1]
  crr.execute("SELECT * FROM COUNTS WHERE email = %s",(email,))
  row = crr.fetchone()
  if row is None:
    crr.execute("INSERT INTO COUNTS (email, count) VALUES (%s, 1)",(email,))
  else:
    crr.execute("UPDATE COUNTS SET count = count + 1 WHERE email = %s",(email,))

crr.execute("SELECT email, count FROM COUNTS ORDER BY count DESC")
rows = crr.fetchall()
for row in rows:
  print(f"Email: {row[0]}, Frequency: {row[1]}")

crr.close()
conn.close()
    