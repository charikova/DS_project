import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import subprocess

PORT = 1337


def json_handler(content):
    obj = json.loads(content.decode("utf-8"))
    return obj


def init_dir(message):
    data = {}
    directory_name = message["args"]["username"]
    available_size = subprocess.check_output("df -Ph . | tail -1 | awk '{print $4}'", shell=True)
    try:
        os.mkdir('{}'.format(directory_name))

        data = {"status": "success", "message": "root directory initialized",
                "size": "{}".format(available_size.decode("utf-8").strip())}
    except FileExistsError:
        shutil.rmtree('{}'.format(directory_name), ignore_errors=True)
        os.mkdir('{}'.format(directory_name))
        data = {"status": "success", "message": "root directory cleaned, reinitialized",
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

    try:
        os.makedirs(root_directory + path)
        data = {"status": "success", "message": "directory crated"}
    except FileExistsError:
        data = {"status": "error", "message": "directory already exists"}

    data_json = json.dumps(data)
    return data_json


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)
        message = json_handler(content)
        data_json = json.dumps('{}')
        if message["command"] == "init":
            data_json = init_dir(message)
        elif message["command"] == "create_dir":
            data_json = create_dir(message)
        else:
            data_json = json.dumps({"status": "error", "message": "unknown command"})
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(data_json, "utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)


if __name__ == "__main__":
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, Server)

    print(f"Starting server on localhost:", PORT)
    httpd.serve_forever()
