import random
import shutil
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import subprocess
import socket
from multiprocessing import Process
import requests

PORT_http = 1337
PORT_ftp_send = 7331
node_ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1],
                       [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
                         [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
node_ip = requests.get('https://api.ipify.org').text
leader_ip = ""
nameserver_ip = os.environ.get('name_ip')
nameserver_port = 1338
replicas = []
beat = 0
last_beat = 0


def verify_path(message):
    data = {}

    root_directory = message["args"]["username"]
    path = message["args"]["path"]

    if os.path.exists(root_directory + path):
        return True
    else:
        return False


def json_handler(content):
    obj = json.loads(content.decode("utf-8"))
    return obj


def init_dir(message):
    data = {}
    root_directory = message["args"]["username"]
    available_size = subprocess.check_output("df -Ph . | tail -1 | awk '{print $4}'", shell=True)
    try:
        os.mkdir('{}'.format(root_directory))

        data = {"status": "success", "message": "root directory initialized",
                "size": "{}".format(available_size.decode("utf-8").strip())}
    except FileExistsError:
        shutil.rmtree('{}'.format(root_directory), ignore_errors=True)
        os.mkdir('{}'.format(root_directory))
        data = {"status": "reinit", "message": "root directory cleaned, reinitialized",
                "size": "{}".format(available_size.decode("utf-8").strip())}
    data_json = json.dumps(data)
    return data_json


def create_dir(message):
    data = {}

    root_directory = message["args"]["username"]
    path = message["args"]["path"]

    try:
        os.listdir('{}'.format(root_directory))
    except FileNotFoundError:
        data = {"status": "error", "message": "first initialize root directory"}
        data_json = json.dumps(data)
        return data_json

    if not verify_path(message):
        os.makedirs(root_directory + path)
        data = {"status": "success", "message": "directory created"}
    else:
        data = {"status": "error", "message": "directory already exists"}

    data_json = json.dumps(data)
    return data_json


def list_dir(message):
    data = {}

    root_directory = message["args"]["username"]
    path = message["args"]["path"]
    if verify_path(message):
        output = subprocess.check_output('ls ' + root_directory + path, shell=True).decode("utf-8").strip().split("\n")
        data = {"status": "success", "message": "content of requested directory", "args": {"data": "{}".format(output)}}
    else:
        data = {"status": "error", "message": "no such directory"}

    data_json = json.dumps(data)
    return data_json


def delete_dir(message):
    data = {}

    root_directory = message["args"]["username"]
    path = message["args"]["path"]

    if path == "":
        data = {"status": "error", "message": "cannot delete root directory"}
        data_json = json.dumps(data)
        return data_json

    if verify_path(message):
        os.listdir(root_directory + path)
        shutil.rmtree('{}'.format(root_directory + path), ignore_errors=True)
        data = {"status": "success", "message": "directory deleted"}
    else:
        data = {"status": "error", "message": "no such directory"}

    data_json = json.dumps(data)
    return data_json


def file_info(message):
    data = {}

    root_directory = message["args"]["username"]
    path = message["args"]["path"]

    if verify_path(message):
        created = subprocess.check_output('stat -c %z ' + root_directory + path, shell=True).decode(
            "utf-8").strip()
        size = subprocess.check_output('stat -c %s ' + root_directory + path, shell=True).decode("utf-8").strip()
        full_path = root_directory + path
        data = {"status": "success", "message": "file info",
                "args": {"created": "{}".format(created), "size": "{}".format(size), "path": "{}".format(full_path)}}
    else:
        data = {"status": "error", "message": "no such file"}

    data_json = json.dumps(data)
    return data_json


def file_delete(message):
    data = {}

    root_directory = message["args"]["username"]
    path = message["args"]["path"]
    if verify_path(message):
        os.remove(root_directory + path)
        data = {"status": "success", "message": "file deleted"}
    else:
        data = {"status": "error", "message": "no such file"}

    data_json = json.dumps(data)
    return data_json


def file_create(message):
    data = {}
    root_directory = message["args"]["username"]
    path = message["args"]["path"]
    full_path = root_directory + path
    ind = full_path.rfind("/")
    path_no_file = full_path[:ind] + "/"
    if not verify_path(message) and os.path.exists(path_no_file):
        os.system('touch ' + full_path)
        data = {"status": "success", "message": "file created"}
    else:
        data = {"status": "error", "message": "file with this name already exists"}

    data_json = json.dumps(data)
    return data_json


def file_copy(message):
    data = {}
    root_directory = message["args"]["username"]
    path = message["args"]["path"]
    ind = path.rfind(".")
    ext = path.split("/")[-1].split(".")[-1]
    copies_number = int(subprocess.check_output('ls ' + root_directory + path + '* | wc -l', shell=True).decode(
        "utf-8").strip())
    if ind == -1:
        new_name = path + '_copy{}'.format(
            str(copies_number))
    else:
        new_name = path[:ind] + '_copy{}.'.format(
            str(copies_number)) + str(ext)

    if verify_path(message):
        os.system(
            'cp ' + str(root_directory) + path + ' ' + root_directory + new_name)
        data = {"status": "success", "message": "file copied",
                "args": {"filename": new_name.split("/")[-1]}}
    else:
        data = {"status": "error", "message": "no such file"}

    data_json = json.dumps(data)
    return data_json


def file_move(message):
    data = {}
    root_directory = message["args"]["username"]
    src_path = message["args"]["src_path"]
    dst_path = message["args"]["dst_path"]

    if os.path.exists(root_directory + src_path) and not os.path.exists(dst_path):
        os.system('mv ' + root_directory + src_path + ' ' + root_directory + dst_path)
        data = {"status": "success", "message": "file moved"}
    else:
        data = {"status": "error", "message": "path incorrect"}

    data_json = json.dumps(data)
    return data_json


def start_download(message):
    root_directory = message["args"]["username"]
    path = message["args"]["path"]
    s = socket.socket()  # Create a socket object
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    host = ""  # Get local machine name
    s.bind((host, PORT_ftp_send))  # Bind to the port
    s.listen(5)  # Now wait for client connection.

    conn, addr = s.accept()  # Establish connection with client.
    if os.path.exists(root_directory + path):
        f = open(root_directory + path, 'rb')
        l = f.read(1024)
        while (l):
            conn.send(l)
            l = f.read(1024)
        f.close()

        data = {"status": "error", "message": "file sent"}
        conn.close()
    else:
        data = {"status": "error", "message": "no such file"}
    conn.close()
    s.close()
    data_json = json.dumps(data)
    return data_json


def file_download(message):
    p = Process(target=start_download(message))
    p.start()
    data = {"status": "success", "message": "download in progress"}
    data_json = json.dumps(data)
    return data_json


def replicate_uploaded(message):
    path = message["args"]["path"]
    username = message["args"]["username"]
    for node in replicas:
        try:
            response = json.loads(
                requests.get('http://' + node + ':' + str(PORT_http), json=message, timeout=1).text)
        except requests.exceptions.ReadTimeout:
            s = socket.socket()  # Create a socket object
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((node, PORT_ftp_send))

            filepath = username + path
            f = open(filepath, 'rb')
            l = f.read(1024)
            while (l):
                s.send(l)
                l = f.read(1024)
            f.close()
            s.close()
            response = "file replicated"
        except requests.exceptions.ConnectionError:
            response = "node dead"
        print(response)


def start_replicated_upload(message):
    p = Process(target=replicate_uploaded(message))
    p.start()
    data = {"status": "success", "message": "download in progress"}
    data_json = json.dumps(data)
    return data_json


def start_upload(message):
    root_directory = message["args"]["username"]
    path = message["args"]["path"]
    filename = root_directory + path

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = ""
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print(leader_ip)
    print(replicas)
    s.bind((host, PORT_ftp_send))

    s.listen(5)
    conn, addr = s.accept()

    with open('{}'.format(filename), 'wb') as f:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # write data to a file
            f.write(data)

    f.close()
    print('Successfully get the file')
    conn.close()
    s.close()
    if node_ip == leader_ip:
        command = {"command": "verify_upload", "args": {"username": root_directory, "path": path}}
        try:
            requests.get('http://' + nameserver_ip + ':' + str(nameserver_port), json=command, timeout=1)
        except requests.exceptions.ReadTimeout:
            pass
    print('connection closed')


def file_upload(message):
    p = Process(target=start_upload(message))
    p.start()
    data = {"status": "success", "message": "upload in progress"}
    data_json = json.dumps(data)
    return data_json


def initialize_node():
    global leader_ip
    command = {"command": "new_node", "args": {"ip": node_ip}}
    response = json.loads(requests.get('http://' + nameserver_ip + ':' + str(nameserver_port), json=command).text)
    if response["status"] == "leader":
        leader_ip = node_ip
    else:
        leader_ip = response["args"]["ip"]

    if response["args"]["status"] == "new":
        return True
    elif response["args"]["status"] == "old":
        return False


def get_replicas_list():
    global replicas
    command = {"command": "servers"}
    response = json.loads(
        requests.get('http://' + nameserver_ip + ':' + str(nameserver_port), json=command).text)
    replicas_new = response["args"]["ips"]
    for node in replicas_new:
        if node not in replicas and node != node_ip:
            replicas.append(node)


def commit_to_replicas(message):
    for node in replicas:
        try:
            response = json.loads(
                requests.get('http://' + node + ':' + str(PORT_http), json=message, timeout=1).text)
        except requests.exceptions.ReadTimeout:
            response = "node dead"
        except requests.exceptions.ConnectionError:
            response = "node dead"
        print(response)


def start_replication(message):
    p = Process(target=replicate_uploaded(message))
    p.start()
    data = {"status": "success", "message": "download in progress"}
    data_json = json.dumps(data)
    return data_json


def request_fs():
    message = {"command": "send_fs", "args": {"ip": node_ip}}
    try:
        response = json.loads(
            requests.get('http://' + leader_ip + ':' + str(PORT_http), json=message, timeout=0.000001).text)
    except requests.exceptions.ReadTimeout:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = ""
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, PORT_ftp_send))
        s.listen(5)
        conn, addr = s.accept()
        with open('bckp.zip', 'wb') as f:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                # write data to a file
                f.write(data)

        f.close()
        conn.close()
        s.close()

        os.system("unzip bckp.zip")
        os.system("rm bckp.zip")
    except requests.exceptions.ConnectionError:
        response = "node dead"


def send_fs(message):
    node = message["args"]["ip"]
    os.system(
        "zip -r bckp.zip $(ls) -x \"storageserver.py\" \"README.md\" \".zip\" \"requirements.txt\" \"Dockerfile\" \"docker-compose.yml\" ")
    s = socket.socket()  # Create a socket object
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((node, PORT_ftp_send))

    filepath = 'bckp.zip'
    f = open(filepath, 'rb')
    l = f.read(1024)
    while (l):
        s.send(l)
        l = f.read(1024)
    f.close()
    s.close()
    os.system("rm bckp.zip")
    return json.dumps({"status": "ok"})


def renew_beat():
    global last_beat
    last_beat = time.time()


def change_leader(message):
    global leader_ip
    leader_ip = message["args"]["ip"]


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)
        message = json_handler(content)
        data_json = json.dumps('{}')
        print(message)
        command = message["command"]
        if leader_ip == node_ip and command != "file_upload" and command != "file_download" \
                and command != "send_fs" and command != "beat" and command != "new_leader":
            commit_to_replicas(message)
        if command == "init":
            data_json = init_dir(message)
        elif command == "create_dir":
            data_json = create_dir(message)
        elif command == "list_dir":
            data_json = list_dir(message)
        elif command == "delete_dir":
            data_json = delete_dir(message)
        elif command == "file_info":
            data_json = file_info(message)
        elif command == "file_delete":
            data_json = file_delete(message)
        elif command == "file_copy":
            data_json = file_copy(message)
        elif command == "file_create":
            data_json = file_create(message)
        elif command == "file_move":
            data_json = file_move(message)
        elif command == "file_download":
            data_json = file_download(message)
        elif command == "file_upload":
            data_json = file_upload(message)
            start_replicated_upload(message)
        elif command == "send_fs":
            data_json = send_fs(message)
        elif command == "beat":
            renew_beat()
        elif command == "new_leader":
            change_leader(message)
        else:
            data_json = json.dumps({"status": "error", "message": "unknown command"})

        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(data_json, "utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)


class HeartBeatLeader(object):
    def __init__(self, interval=2):
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            get_replicas_list()
            if node_ip != leader_ip:
                break
            message = {"command": "beat"}
            try:
                requests.get('http://' + nameserver_ip + ':' + str(nameserver_port), json=message, timeout=1)
            except requests.exceptions.ReadTimeout:
                pass
            except requests.exceptions.ConnectionError:
                pass

            for node in replicas:
                try:
                    response = json.loads(
                        requests.get('http://' + node + ':' + str(PORT_http), json=message, timeout=1).text)
                except requests.exceptions.ReadTimeout:
                    response = "node dead"
                except requests.exceptions.ConnectionError:
                    response = "node dead"


class HeartBeatFollower(object):
    def __init__(self, interval=2):
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        global beat
        global last_beat
        global leader_ip
        global node_ip
        time.sleep(2)
        while True:
            beat = time.time()
            if beat - last_beat > 5:
                time.sleep(random.uniform(1.1, 1.9))
                message = {"command": "change_leader", "args": {"ip": node_ip}}
                response = json.loads(
                    requests.get('http://' + nameserver_ip + ':' + str(nameserver_port), json=message, timeout=1).text)
                if response["status"] == "OK":
                    leader_ip = node_ip
                    hbeat = HeartBeatLeader()
                    get_replicas_list()
                    for node in replicas:
                        message_to_replicas = {"command": "new_leader", "args": {"ip": node_ip}}
                        requests.get('http://' + node_ip + ':' + str(PORT_http), json=message_to_replicas, timeout=1)
                    break


if __name__ == "__main__":
    server_address = ('', PORT_http)
    httpd = HTTPServer(server_address, Server)
    print(node_ip)
    system_status = initialize_node()
    if not system_status:
        try:
            os.system("rm -r */")
        except Exception:
            pass
        request_fs()
    if leader_ip == node_ip:
        get_replicas_list()
        hbeat = HeartBeatLeader()
    else:
        print("follower state")
        hbeat = HeartBeatFollower()

    print(f"Starting server on localhost:", PORT_http)
    httpd.serve_forever()
