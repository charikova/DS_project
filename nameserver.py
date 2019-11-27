from neo4jrestclient import client
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

db = client.GraphDatabase("http://localhost:7474", username="DFSnameserver", password="123")
user_relation_label = "own"
folders_relation_label = "store"
PORT = 1338


def init_db(message):
    username = message["args"]["username"]
    query = 'MATCH (u:User) RETURN u'
    users = db.query(query, returns=client.Node)
    exist = False
    for i in users:
        if i == username:
            exist = True
    if exist:
        # TODO: request to server
        data_init = json.dumps({
            "status": "OK",
            "message": "Root directory cleaned, reinitialized",
            "size": "1337"
        })
    else:
        # TODO: request to server
        user = db.labels.create("Users")
        folder = db.labels.create("Folders")
        file = db.labels.create("Files")
        u1 = db.nodes.create(name=username)
        user.add(u1)
        data_init = json.dumps({
            "status": "OK",
            "message": "Root directory initialized",
            "size": "1337"
        })
    return data_init


def json_handler(content):
    obj = json.loads(content.decode("utf-8"))
    return obj


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)
        message = json_handler(content)
        data_json = json.dumps('{}')
        if message["command"] == "init":
            data_json = init_db(message)
        else:
            data_json = json.dumps({
                "status": "error",
                "message": "unknown command",
                "size": "none"
            })
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(data_json, "utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)
        json_handler(content)


if __name__ == "__main__":
    server_address = ("localhost", PORT)
    httpd = HTTPServer(server_address, Server)

    print(f"Starting server on localhost:", PORT)
    httpd.serve_forever()