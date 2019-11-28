import socket

import requests

PORT_ftp_send = 7331
s = socket.socket()  # Create a socket object
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = ""  # Get local machine name
s.bind((host, PORT_ftp_send))  # Bind to the port
s.listen(5)  # Now wait for client connection.

command = {"command": "file_upload",
           "args": {
               "username": "roma",
               "path": "/privet/roma.jpg",
               "client": "10.1.1.129",
               "port": "{}".format(PORT_ftp_send)
           }
           }
try:
    requests.get('http://10.1.1.141:1337', json=command, timeout=0.000001)
except requests.exceptions.ReadTimeout:
    pass


s.listen(5)  # Now wait for client connection.

conn, addr = s.accept()  # Establish connection with client.

filepath = './roma.jpg'
f = open(filepath, 'rb')
l = f.read(1024)
while (l):
    conn.send(l)
    l = f.read(1024)
f.close()

conn.close()
