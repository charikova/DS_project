import json
import os
import socket  # Import socket module
import time

import requests

s = socket.socket()  # Create a socket object
host = "10.1.1.141"  # Ip address that the TCPServer  is there
port = 7331  # Reserve a port for your service every new transfer wants a new port or you must wait.

response = json.loads(requests.get('http://10.1.1.141:1337', json={"command": "file_download",
                                                                   "args": {
                                                                       "username": "roma",
                                                                       "path": "/privet/alo.txt"
                                                                   }
                                                                   }).text)
s.connect((host, port))
print(s.connect((host, port)))
s.send(b'{args:{"username": "roma"}, "path": "/privet/alo.txt"}')

with open('received_file', 'wb') as f:
    while True:
        print('receiving data...')
        data = s.recv(1024)
        print('data=%s', (data))
        if not data:
            break
        # write data to a file
        f.write(data)

f.close()
print('Successfully get the file')
s.close()
print('connection closed')
