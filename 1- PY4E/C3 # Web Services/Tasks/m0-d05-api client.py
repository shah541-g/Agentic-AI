from urllib import request, parse, error
import json

serviceUrl = 'https://api.open-meteo.com/v1/forecast?'

params = dict()
params['latitude'] = '31.5204'
params['longitude'] = '74.3587'
params['current'] = 'temperature_2m,relative_humidity_2m,wind_speed_10m'

url = serviceUrl + parse.urlencode(params)

print(f"Retrieving: {url}")

try:
    response = request.urlopen(url)
    data = response.read().decode()
except error.HTTPError as e:
    print("Status: ", e.code)
    print("response: ", e.read().decode())

try:
    info = json.loads(data)
except:
    info = None

print(json.dumps(info, indent=4))