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
    directory_name = message["dir_name"]
    try:
        os.mkdir('{}'.format(directory_name))
        available_size = subprocess.check_output("df -Ph . | tail -1 | awk '{print $4}'", shell=True)

        data = {"status": "success", "message": "Root directory initialized",
                "size": "{}".format(available_size.decode("utf-8").strip())}
    except FileExistsError:
        os.rmdir('{}'.format(directory_name))
        data = {"status": "success", "message": "Root directory cleaned, reinitialized"}
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
        else:
            data_json = json.dumps({"status": "error", "message": "unknown command"})
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
