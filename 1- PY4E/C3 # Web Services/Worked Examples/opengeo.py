from urllib import request, parse
import json

serviceUrl = 'https://py4e-data.dr-chuck.net/opengeo?'

while True:
  address = input("Enter Address: ")
  if len(address) < 1: break
  params = dict()
  params['q'] = address
  
  url = serviceUrl + parse.urlencode(params)
  print(f"Retrieving: {url}")
  response = request.urlopen(serviceUrl)
  data = response.read().decode()
  
  try:
    info = json.loads(data)
  except:
    info = None
  
  if not info or "features" not in info:
    print("Download Error".center(8,"="))
    print(data)
    break
  
  if len(info["features"])==0:
    print("Object not found".center(8,"="))
    print(data)
    break
  
  lat = print(info["features"][0]["properties"]["lat"])
  lon = print(info["features"][0]["properties"]["lon"])
  print(f"Lat: {lat}, Lon: {lon}")