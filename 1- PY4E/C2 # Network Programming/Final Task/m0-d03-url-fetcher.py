from urllib import request

with request.urlopen("https://www.youtube.com/") as response:
  header = response.headers
  body = response.read().decode()

with open("output.txt","w", encoding="utf-8") as file:
   
  file.write(f"""
      ====================
          H E A D E R
      ====================
            {header}
            
            
            
      ====================
            B O D Y
      ====================
            {body}
      """)
print(header)




















