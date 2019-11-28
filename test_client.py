import socket  # Import socket module

import requests

s = socket.socket()  # Create a socket object
host = "10.1.1.141"  # Ip address that the TCPServer  is there
port = 7331  # Reserve a port for your service every new transfer wants a new port or you must wait.

command = {"command": "file_download",
           "args": {
               "username": "roma",
               "path": "/regex.pdf"
           }
           }
try:
    requests.get('http://' + host + ':' + str(port), json=command, timeout=0.000001)
except requests.exceptions.ReadTimeout:
    pass

s.connect((host, port))
filename = command["args"]["path"].split("/")[-1]
with open('{}'.format(filename), 'wb') as f:
    while True:
        print('receiving data...')
        data = s.recv(1024)
        if not data:
            break
        # write data to a file
        f.write(data)

f.close()
print('Successfully get the file')
s.close()
print('connection closed')
