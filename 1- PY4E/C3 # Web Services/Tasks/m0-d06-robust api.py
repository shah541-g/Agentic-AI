from urllib import request, parse, error
import os
import json
import random
import time


serviceUrl = 'https://api.open-meteo.com/v1/forecast'
API_KEY = os.getenv("KEY")

class APIClient:
  def __init__(self, maxTries, apiKey = None):
    self.apiKey = apiKey
    self.maxTries = maxTries
  
  def get(self, url, params):
    if params:
      url = url + '?' + parse.urlencode(params)
    
    header = {
      'Accept':"application/json",
      "User-Agent":"RobustAPIClient/1.0"
    }
    
    if self.apiKey:
      header["Authorization"] = f"Bearer {self.apiKey}"
    
    
    for attempt in range(self.maxTries):
      req = request.Request(
        url=url,
        headers=header,
        method='GET'
      )
      try:
        with request.urlopen(req,timeout=10) as response:
          status = response.status
          print(f"Response Status: {status}")
          data = response.read().decode()
          return json.loads(data)
      except error.HTTPError as e:
        print("HTTP Error Occured with code: ",e.code)
        retryable = (e.code == 429 or 500<= e.code <=599)
        if not retryable:
          raise
        if attempt == self.maxTries-1:
          print("Max retries reached")
          raise
        retryAfter = e.headers.get('Retry-After')
        if retryAfter:
          wait = int(retryAfter)
        else:
          wait = (2**attempt) + random.random()
        print(f'Retrying after: {wait} seconds')
        time.sleep(wait)
      except error.URLError as e:
        print(f'Network Error: {e}')
        if attempt == self.maxTries-1:
          raise
        wait = (2**attempt) + random.random()
        print(f'Retrying after: {wait} seconds')
        time.sleep(wait)

client = APIClient(5,API_KEY)
params = {
    "latitude": 31.5204,
    "longitude": 74.3587,
    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m"
}
data = client.get(serviceUrl,params)
print(json.dumps(data,indent=4))