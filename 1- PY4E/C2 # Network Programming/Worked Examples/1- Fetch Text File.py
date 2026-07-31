import socket

response = b""
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mySocket:
  mySocket.connect(('data.pr4e.org',80))
  cmd = 'GET http://data.pr4e.org/romeo.txt HTTP/1.0\r\n\r\n'.encode()
  mySocket.send(cmd)
  while(True):
    data = mySocket.recv(512)
    if len(data)<1:
      break
    response+=data
  
header, _,  body = response.partition(b'\r\n\r\n')
print("------")
print("Header")
print("------")
print(header.decode())
print("------")
print("Body")
print("------")
print(body.decode())



