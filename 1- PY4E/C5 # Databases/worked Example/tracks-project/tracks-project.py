import mysql.connector

conn = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root123",
  database="tracks",
)

crr = conn.cursor()


crr.execute("DROP TABLE IF EXISTS Track")
crr.execute("DROP TABLE IF EXISTS Album")
crr.execute("DROP TABLE IF EXISTS Artist")

crr.execute("""
    CREATE TABLE Artist (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) UNIQUE
    )
""")

crr.execute("""
    CREATE TABLE Album (
        id INT PRIMARY KEY AUTO_INCREMENT,
        artist_id INT,
        title VARCHAR(100) UNIQUE
    )
""")

crr.execute("""
    CREATE TABLE Track (
        id INT PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(100) UNIQUE,
        album_id INT,
        len INT,
        rating INT,
        count INT
    )
""")

fh = open('tracks.csv')

for line in fh:
  data = line.split(',')
  if len(data) < 6: continue
  
  name = data[0]
  artist = data[1]
  album = data[2]
  count = data[3]
  rating = data[4]
  length = data[5]
  
  print(f"""
        Name: {name}
        Artist: {artist}
        Album: {album}
        Count: {count}
        Rating: {rating}
        Length: {length} 
        """)
  crr.execute("INSERT IGNORE INTO ARTIST (name) VALUES (%s)",(artist,))
  crr.execute("SELECT id FROM Artist WHERE name = %s",(artist,))
  artist_id = crr.fetchone()[0]
  crr.execute("INSERT IGNORE INTO Album (title, artist_id) VALUES (%s, %s)",(album, artist_id))
  crr.execute("SELECT id FROM Album WHERE title = %s", (album,))
  album_id = crr.fetchone()[0]
  crr.execute("INSERT IGNORE INTO Track (title, album_id, len, rating, count) VALUES ( %s, %s, %s, %s, %s)",(name,album_id,length, rating, count))
  
conn.commit()

crr.close()
conn.close()