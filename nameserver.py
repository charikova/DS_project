from neo4jrestclient import client
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests

db = client.GraphDatabase("http://localhost:7474", username="DFSnameserver", password="123")
user_relation_label = "own"
folders_relation_label = "store"
PORT = 1338
user = db.labels.create("Users")
folder = db.labels.create("Folders")
file = db.labels.create("Files")
server_ip = 'http://13.59.57.151:8589'


def init_db(message):
    username = message["args"]["username"]
    response = json.loads(requests.get(server_ip, json=message).text)
    if response["status"] == "reinit":
        query = "MATCH path = (u:Users { name:\"%s\" })-[r *1..]->(f) DETACH DELETE f, u" % username
        db.query(query)
        query = "MATCH (u:Users {name: \"%s\"}) DETACH DELETE u" % username
        db.query(query)
    new_user(username)
    return json.dumps(response)


def create_dir(message):
    path = message["args"]["path"]
    username = message["args"]["username"]
    paths = path.split('/')
    data = json.loads(requests.get(server_ip, json=message).text)
    if data["status"] == "success":
        try:
            if len(paths) == 3:
                q = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" % (username, paths[1])
                fid = db.query(q)[0][0]
                print(fid)
                query = "MATCH (s) WHERE ID(s) = %s CREATE (n:Folders { name: \'%s\'}) CREATE (s)-[r:store]->(n)" \
                        % (str(fid), paths[2])
                db.query(query)
            elif len(paths) > 3:
                q = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" % (username, paths[1])
                fid = db.query(q)[0][0]
                for p in range(2, len(paths) - 1):
                    query = "MATCH (s) WHERE ID(s) = %s MATCH (s)-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" \
                            % (str(fid), paths[p])
                    fid = db.query(query)[0][0]
                query = "MATCH (s) WHERE ID(s) = %s CREATE (n:Folders { name: \'%s\'}) CREATE (s)-[r:store]->(n)" \
                        % (str(fid), paths[-1])
                db.query(query)
            else:
                query = "MATCH (s:Users) WHERE s.name = \"%s\" CREATE (n:Folders { name: \'%s\'}) " \
                        "CREATE (s)-[r:own]->(n)" % (username, paths[1])
                db.query(query)
        except Exception:
            data = {"status": "error", "message": "Error during query execution"}
    return json.dumps(data)


def new_user(username):
    u1 = db.nodes.create(name=username)
    user.add(u1)


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
        elif message["command"] == "create_dir":
            data_json = create_dir(message)
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
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, Server)

    print(f"Starting server on localhost:", PORT)
    httpd.serve_forever()