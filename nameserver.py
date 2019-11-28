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
server_ip = 'http://10.1.1.141:1337'


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


def find_create(paths, username):
    fileID = 0
    try:
        if len(paths) == 3:
            q = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" % (username, paths[1])
            fileID = db.query(q)[0][0]
            q = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" % (username, paths[1])
            fileID = db.query(q)[0][0]
        elif len(paths) > 3:
            q = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" % (username, paths[1])
            fileID = db.query(q)[0][0]
            for p in range(2, len(paths) - 1):
                query = "MATCH (s) WHERE ID(s) = %s MATCH (s)-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" \
                        % (str(fileID), paths[p])
                fileID = db.query(query)[0][0]
    except Exception:
        print("Error during query execution")
    return fileID


def find(paths, username):
    fileID = 0
    try:
        if len(paths) == 2:
            q = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" % (username, paths[1])
            fileID = db.query(q)[0][0]
        elif len(paths) > 2:
            q = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" % (username, paths[1])
            fileID = db.query(q)[0][0]
            for p in range(2, len(paths)):
                query = "MATCH (s) WHERE ID(s) = %s MATCH (s)-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" \
                        % (str(fileID), paths[p])
                fileID = db.query(query)[0][0]
    except Exception:
        print("Error during query execution")
    return fileID


def create_dir(message):
    path = message["args"]["path"]
    username = message["args"]["username"]
    paths = path.split('/')
    data = json.loads(requests.get(server_ip, json=message).text)
    if data["status"] == "success":
        try:
            if len(paths) > 2:
                fid = find_create(paths, username)
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


def list_dir(message):
    path = message["args"]["path"]
    username = message["args"]["username"]
    paths = path.split('/')
    if len(paths) > 1:
        fid = find(paths, username)
        query = "MATCH (s) WHERE ID(s) = %s MATCH (s)-[r]->(f) RETURN {name: f.name, label: labels(f)}" % str(fid)
        res = db.query(query)
    else:
        query = "MATCH (s:Users) WHERE s.name = \"%s\" MATCH (s)-[r]->(f) RETURN {name: f.name, label: labels(f)}" \
                % username
        res = db.query(query)
    lis = []
    for r in res:
        ll = r[0]['label'][0]
        if ll == "Folders":
            ll = 'dir'
        elif ll == "Files":
            ll = 'file'
        lis.append((r[0]['name'], ll))
    data = {
        "status": "OK",
        "message": "Directory listed",
        "names": lis
    }
    return json.dumps(data)


def file_create(message):
    path = message["args"]["path"]
    username = message["args"]["username"]
    paths = path.split('/')
    data = json.loads(requests.get(server_ip, json=message).text)
    if data["status"] == "success":
        try:
            if len(paths) > 2:
                fid = find_create(paths, username)
                query = "MATCH (s) WHERE ID(s) = %s CREATE (n:Files { name: \'%s\'}) CREATE (s)-[r:store]->(n)" \
                        % (str(fid), paths[-1])
                db.query(query)
            else:
                query = "MATCH (s:Users) WHERE s.name = \"%s\" CREATE (n:Files { name: \'%s\'}) " \
                        "CREATE (s)-[r:own]->(n)" % (username, paths[1])
                db.query(query)
        except Exception:
            data = {"status": "error", "message": "Error during query execution"}
    return json.dumps(data)


def file_delete(message):
    path = message["args"]["path"]
    username = message["args"]["username"]
    paths = path.split('/')
    data = json.loads(requests.get(server_ip, json=message).text)
    if data["status"] == "success":
        try:
            if len(paths) > 1:
                fid = find(paths, username)
                query = "MATCH (s) WHERE ID(s) = %s DETACH DELETE s" \
                        % str(fid)
                db.query(query)
                print(fid)
            else:
                query = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" \
                        % (username, paths[-1])
                fid = db.query(query)[0][0]
                query = "MATCH (s) WHERE ID(s) = %s DETACH DELETE s" \
                        % str(fid)
                db.query(query)
        except Exception:
            data = {"status": "error", "message": "Error during query execution"}
    return json.dumps(data)


def file_copy(message):
    path = message["args"]["path"]
    username = message["args"]["username"]
    paths = path.split('/')
    data = json.loads(requests.get(server_ip, json=message).text)
    new_name = data["args"]["filename"]
    if data["status"] == "success":
        try:
            if len(paths) > 2:
                fid = find_create(paths, username)
                query = "MATCH (s) WHERE ID(s) = %s CREATE (n:Files { name: \'%s\'}) CREATE (s)-[r:store]->(n) " \
                        % (str(fid), new_name)
                db.query(query)
            else:
                query = "MATCH (s:Users) WHERE s.name = \"%s\" CREATE (n:Files { name: \'%s\'}) " \
                        "CREATE (s)-[r:own]->(n)" % (username, new_name)
                db.query(query)
        except Exception:
            data = {"status": "error", "message": "Error during query execution"}
    return json.dumps(data)


def file_move(message):
    src_path = message["args"]["src_path"]
    dst_path = message["args"]["dst_path"]
    username = message["args"]["username"]
    spaths = src_path.split('/')
    dpaths = dst_path.split('/')
    data = json.loads(requests.get(server_ip, json=message).text)
    dfid = 0
    if data["status"] == "success":
        if len(spaths) > 1:
            sfid = find(spaths, username)
        else:
            query = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" \
                    % (username, spaths[-1])
            sfid = db.query(query)[0][0]
        if len(dpaths) > 2:
            dfid = find_create(dpaths, username)
            query = "MATCH (s) WHERE ID(s) = %s MATCH (n) WHERE ID(n) = %s MATCH (x)-[r]->(n) DELETE r " \
                    "CREATE (s)-[f:own]->(n)" % (str(dfid), str(sfid))
            db.query(query)
        else:
            query = "MATCH (s:Users) WHERE s.name = \"%s\" MATCH (n) WHERE ID(n) = %s MATCH (x)-[r]->(n) DELETE r " \
                    "CREATE (s)-[f:own]->(n)" % (username, str(sfid))
            db.query(query)
    return json.dumps(data)


def file_info(message):
    data = json.loads(requests.get(server_ip, json=message).text)
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
        elif message["command"] == "list_dir":
            data_json = list_dir(message)
        elif message["command"] == "file_create":
            data_json = file_create(message)
        elif message["command"] == "file_info":
            data_json = file_info(message)
        elif message["command"] == "file_copy":
            data_json = file_copy(message)
        elif message["command"] == "file_delete":
            data_json = file_delete(message)
        elif message["command"] == "file_move":
            data_json = file_move(message)
        elif message["command"] == "delete_dir":
            data_json = file_delete(message)
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