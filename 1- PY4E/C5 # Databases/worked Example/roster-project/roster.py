import mysql.connector
import json

conn = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root123",
  database="roster",
)

crr = conn.cursor()

crr.execute("DROP TABLE IF EXISTS User")
crr.execute("DROP TABLE IF EXISTS Member")
crr.execute("DROP TABLE IF EXISTS Course")

crr.execute("""
  CREATE TABLE User (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE
  )
""")
crr.execute("""
  CREATE TABLE Course (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) UNIQUE
  )
""")
crr.execute("""
  CREATE TABLE Member (
    user_id INT,
    course_id INT,
    role INT,
    PRIMARY KEY (user_id, course_id)
  )
""")

fname = input("Enter File Name: ")
if len(fname) < 1:
  fname = "roster_data_sample.json"

data = open(fname).read()
jsonData = json.loads(data)

for entry in jsonData:
  name = entry[0]
  title = entry[1]
  print(f"Course Title: {title}, Name: {name}")
  crr.execute("INSERT IGNORE INTO USER (name) VALUES (%s)", (name,))
  crr.execute("SELECT id FROM USER WHERE name = %s", (name,))
  user_id = crr.fetchone()[0]
  crr.execute("INSERT IGNORE INTO COURSE (title) VALUES (%s)", (title,))
  crr.execute("SELECT id FROM COURSE WHERE title = %s", (title,))
  course_id = crr.fetchone()[0]
  
  crr.execute("INSERT INTO Member (user_id, course_id) VALUES (%s, %s)", (user_id, course_id))

conn.commit()
crr.close()
conn.close()