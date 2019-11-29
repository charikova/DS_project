import json
import socket
from flask import Flask, render_template, request
import requests

app = Flask(__name__, template_folder='templates')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/enter_filesystem')
def enter_filesystem():
    return render_template("enter_filesystem.html")


@app.route('/start')
def start():
    return render_template("start.html")


@app.route('/initialize', methods=['POST', 'GET'])
def initialize():
    name = request.form.getlist('username')[0]
    response = json.loads(
        requests.get('http://18.222.226.202:1338', json={"command": "init", "args": {"username": name}}).text)
    return render_template("initialize.html", result=response)


@app.route('/file_create', methods=['POST', 'GET'])
def file_create():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    path += '/'
    path += filename
    response = json.loads(requests.get('http://18.222.226.202:1338', json={"command": "file_create",
                                                                         "args": {"username": name,
                                                                                  "path": path}}).text)
    return render_template("file_create.html", result=response)


@app.route('/file_download', methods=['POST', 'GET'])
def file_download():
    name = current_user
    filename = request.form.getlist('filename')[0]
    print(filename)
    global path
    path += '/'
    path += filename
    host = json.loads(requests.get('http://18.222.226.202:1338', json={"command": "file_download",
                                                                   "args": {"username": name,
                                                                            "path": path}}).text)
    args = host['args']
    host = args['ip']
    port = args['port']
    s = socket.socket()
    print(path)
    command = {"command": "file_download",
               "args": {
                   "username": name,
                   "path": path
               }
               }
    try:
        requests.get('http://' + str(host) + ':' + str(1337), json=command, timeout=0.000001)
    except requests.exceptions.ReadTimeout:
        pass
    s.connect((host, port))
    print('a')
    filename = command["args"]["path"].split("/")[-1]
    with open('{}'.format(filename), 'wb') as f:
        while True:
            print('receiving data...')
            data = s.recv(1024)
            if not data:
                break
            f.write(data)
    f.close()
    s.close()
    return render_template("file_download.html", result=host)


@app.route('/file_upload', methods=['POST', 'GET'])
def file_upload():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    path += '/'
    path += filename
    host = json.loads(requests.get('http://18.222.226.202:1338', json={"command": "file_upload",
                                                                   "args": {"username": name,
                                                                            "path": path}}).text)
    args = host['args']
    host = args['ip']
    port = args['port']

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    command = {"command": "file_upload",
               "args": {
                   "username": name,
                   "path": path + 'a.png'
               }
               }
    try:
        requests.get('http://' + host + ':' + str(1337), json=command, timeout=0.000001)
    except requests.exceptions.ReadTimeout:
        pass
    s.connect((host, 7331))
    filepath = './a.png'
    f = open(filepath, 'rb')
    l = f.read(1024)
    while (l):
        s.send(l)
        l = f.read(1024)
    f.close()
    s.close()
    return render_template("file_upload.html", result=host)


@app.route('/file_delete', methods=['POST', 'GET'])
def file_delete():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    path += '/'
    path += filename
    response = json.loads(
        requests.get('http://18.222.226.202:1338',
                     json={"command": "file_delete", "args": {"username": name, "path": path}}).text)

    return render_template("file_delete.html", result=response)


@app.route('/file_info', methods=['POST', 'GET'])
def file_info():
    name = current_user
    filename = request.form.getlist('filename')[0]
    print(filename)
    global path
    path += '/'
    path += filename
    response = json.loads(
        requests.get('http://18.222.226.202:1338',
                     json={"command": "file_info", "args": {"username": name, "path": path}}).text)
    return render_template("file_info.html", result=response)


@app.route('/file_copy', methods=['POST', 'GET'])
def file_copy():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    path += '/'
    path += filename
    response = json.loads(
        requests.get('http://18.222.226.202:1338',
                     json={"command": "file_copy", "args": {"username": name, "path": path}}).text)
    return render_template("file_copy.html", result=response)


@app.route('/file_move', methods=['POST', 'GET'])
def file_move():
    name = current_user
    filename = request.form.getlist('filename')[0]
    path_to_move = '/' + request.form.getlist('path_to_move')[0] + '/' + filename
    global path
    path += '/'
    path += filename
    response = json.loads(
        requests.get('http://18.222.226.202:1338',
                     json={"command": "file_move", "args": {"username": name, "src_path": path, "dst_path": path_to_move}}).text)
    return render_template("file_copy.html", result=response)


@app.route('/filesystem', methods=['POST', 'GET'])
def log_in():
    global current_user
    global path
    name = current_user
    name = request.form.getlist('name')[0]
    current_user = name
    path = ''
    response = json.loads(
        requests.get('http://18.222.226.202:1338',
                     json={"command": "list_dir", "args": {"username": name, "path": path}}).text)
    files = response['names']
    return render_template("filesystem.html", result=files, name=current_user)


@app.route('/filesystem_dir', methods=['POST', 'GET'])
def open_directory():
    global current_user
    global path
    name = current_user
    dirname = request.form.getlist('filename')[0]
    print(dirname)
    path += '/'
    path += dirname
    response = json.loads(
        requests.get('http://18.222.226.202:1338',
                     json={"command": "list_dir", "args": {"username": name, "path": path}}).text)
    files = response['names']
    return render_template("filesystem_dir.html", result=files, name=current_user, directory=dirname)


@app.route('/directory_create', methods=['POST', 'GET'])
def directory_create():
    global current_user
    name = request.form.getlist('dirname')[0]
    global path
    path += '/'
    path += name
    response = json.loads(
        requests.get('http://18.222.226.202:1338', json={"command": "create_dir", "args": {"username": current_user, "path": path}}).text)
    return render_template("directory_create.html", result=response)


@app.route('/dir_delete', methods=['POST', 'GET'])
def delete_directory():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    path += '/'
    path += filename
    response = json.loads(
        requests.get('http://18.222.226.202:1338',
                     json={"command": "delete_dir", "args": {"username": name, "path": path}}).text)

    return render_template("dir_delete.html", result=response)


current_user = ''
path = ''

if __name__ == '__main__':
    app.run(debug=True)
