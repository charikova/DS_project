import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import subprocess
import socket
from multiprocessing import Process

PORT_http = 1337
PORT_ftp_send = 7331


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

    if not verify_path(message):
        os.system('touch ' + root_directory + path)
        data = {"status": "success", "message": "file created"}
    else:
        data = {"status": "error", "message": "file with this name already exists"}

    data_json = json.dumps(data)
    return data_json


def file_copy(message):
    data = {}
    root_directory = message["args"]["username"]
    path = message["args"]["path"]
    name = path.split("/")[-1]
    copies_number = int(subprocess.check_output('ls ' + root_directory + path + '* | wc -l', shell=True).decode(
        "utf-8").strip())

    if verify_path(message):
        os.system('cp ' + root_directory + path + ' ' + root_directory + path + '_copy{}'.format(str(copies_number)))
        data = {"status": "success", "message": "file copied",
                "args": {"filename": "{}".format(name + '_copy' + str(copies_number))}}
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

    if os.path.exists(root_directory+path):
        f = open(root_directory+path, 'rb')
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


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)
        message = json_handler(content)
        data_json = json.dumps('{}')
        command = message["command"]

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
        else:
            data_json = json.dumps({"status": "error", "message": "unknown command"})

        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(data_json, "utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)


if __name__ == "__main__":
    server_address = ('', PORT_http)
    httpd = HTTPServer(server_address, Server)

    print(f"Starting server on localhost:", PORT_http)
    httpd.serve_forever()
