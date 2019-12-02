from neo4jrestclient import client
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import threading
import time
import os

neo4j_ip = os.environ.get('neo4j_host')
print(neo4j_ip)
neofull = 'http://' + neo4j_ip + ':7474'
db = client.GraphDatabase(neofull, username="DFSnameserver", password="123")
user_relation_label = "own"
folders_relation_label = "store"
PORT = 1338
user = db.labels.create("Users")
folder = db.labels.create("Folders")
file = db.labels.create("Files")
servers = []
server_ip = ''
leader_ip = ''
port = 7331
leader_alive = False
beat = 0
last_beat = 0


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


def delete_dir(message):
    path = message["args"]["path"]
    username = message["args"]["username"]
    paths = path.split('/')
    data = json.loads(requests.get(server_ip, json=message).text)
    if data["status"] == "success":
        try:
            if len(paths) > 1:
                fid = find(paths, username)
                query = "MATCH (s) WHERE ID(s) = %s MATCH (s)-[r *1..]->(f) DETACH DELETE f, s" % str(fid)
                db.query(query)
                query = "MATCH (s) WHERE ID(s) = %s DETACH DELETE s" \
                        % str(fid)
                db.query(query)
                print(fid)
            else:
                query = "MATCH (u:Users { name:\"%s\" })-[r]->(f) WHERE f.name = \'%s\' RETURN ID(f)" \
                        % (username, paths[-1])
                fid = db.query(query)[0][0]
                query = "MATCH (s) WHERE ID(s) = %s MATCH (s)-[r *1..]->(f) DETACH DELETE f, s" % str(fid)
                db.query(query)
                query = "MATCH (s) WHERE ID(s) = %s DETACH DELETE s" \
                        % str(fid)
                db.query(query)
        except Exception:
            data = {"status": "error", "message": "Error during query execution"}
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
                    "CREATE (s)-[f:store]->(n)" % (str(dfid), str(sfid))
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


def file_upload(message):
    data = {
        "status": "OK",
        "message": "Successfully initialized upload",
        "args": {
            "ip": leader_ip,
            "port": port
        }
    }
    return json.dumps(data)


def file_download(message):
    data = {
        "status": "OK",
        "message": "Successfully initialized download",
        "args": {
            "ip": leader_ip,
            "port": port
        }
    }
    return json.dumps(data)


def verify_upload(message):
    path = message["args"]["path"]
    username = message["args"]["username"]
    paths = path.split('/')
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
        print("Error during query execution")
    data = {
        "status": "OK",
        "message": "Successfully created file",
    }
    return json.dumps(data)


def new_node(message):
    ip = message["args"]["ip"]
    global leader_ip, server_ip, leader_alive
    data = {}
    query = "match (n) return count(n) as count"
    res = db.query(query)[0][0]
    status = ''
    if res == 0:
        status = 'new'
        if ip not in servers:
            servers.append(ip)
    else:
        status = 'old'
    if len(servers) == 1:
        leader_alive = True
        leader_ip = ip
        server_ip = 'http://' + ip + ':1337'
        data = {
            "status": "leader",
            "args": {
                "status": status,
                "ip": leader_ip
            }
        }
    else:
        data = {
            "status": "not_leader",
            "args": {
                "status": status,
                "ip": leader_ip
            }
        }
    return json.dumps(data)


def change_leader(message):
    global leader_ip, server_ip, leader_alive
    data = {}
    if not leader_alive:
        print("ХАВАЮ ПИСЬКИ")
        new_ip = message["args"]["ip"]
        leader_alive = True
        leader_ip = new_ip
        server_ip = 'http://' + new_ip + ':1337'
        data = {
            "status": "OK",
            "message": "Leader successfully changed"
        }
    else:
        data = {
            "status": "ERROR",
            "message": "Leader already alive"
        }
    return json.dumps(data)


def servers_ip(message):
    data = {
        "status": "OK",
        "args": {
            "ips": servers
        }
    }
    return json.dumps(data)


def json_handler(content):
    obj = json.loads(content.decode("utf-8"))
    return obj


def rec_beat():
    global last_beat, leader_alive
    leader_alive = True
    last_beat = time.time()


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)
        global leader_alive
        message = json_handler(content)
        print(message)
        data_json = json.dumps('{}')
        print(leader_ip)
        print(leader_alive)
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
            data_json = delete_dir(message)
        elif message["command"] == "file_upload":
            data_json = file_upload(message)
        elif message["command"] == "file_download":
            data_json = file_download(message)
        elif message["command"] == "file_download":
            data_json = file_download(message)
        elif message["command"] == "verify_upload":
            data_json = verify_upload(message)
        elif message["command"] == "servers":
            data_json = servers_ip(message)
        elif message["command"] == "new_node":
            data_json = new_node(message)
        elif message["command"] == "change_leader":
            data_json = change_leader(message)
        elif message["command"] == "beat":
            data_json = json.dumps({"status": "OK"})
            rec_beat()
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


class HeartBeatFollower(object):
    def __init__(self, interval=2):
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        global beat, leader_alive
        global last_beat
        time.sleep(5)
        while True:
            beat = time.time()
            if beat - last_beat > 5:
                # print("Leader ded")
                leader_alive = False


if __name__ == "__main__":
    hbeat = HeartBeatFollower()
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, Server)

    print(f"Starting server on localhost:", PORT)
    httpd.serve_forever()
