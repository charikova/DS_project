import json
import os
import socket
from flask import Flask, render_template, request, send_file
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates')


@app.route('/')
def index():
    global ip
    return render_template("index.html", ip=ip)


@app.route('/enter_filesystem')
def enter_filesystem():
    global ip
    return render_template("enter_filesystem.html", ip=ip)


@app.route('/start')
def start():
    global ip
    return render_template("start.html", ip=ip)


@app.route('/initialize', methods=['POST', 'GET'])
def initialize():
    global igor
    global ip
    name = request.form.getlist('username')[0]
    response = json.loads(
        requests.get(igor, json={"command": "init", "args": {"username": name}}).text)
    return render_template("initialize.html", result=response, user=name, ip=ip)


@app.route('/file_create', methods=['POST', 'GET'])
def file_create():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    global ip
    global igor
    path += '/'
    path += filename
    response = json.loads(requests.get(igor, json={"command": "file_create",
                                                                           "args": {"username": name,
                                                                                    "path": path}}).text)
    return render_template("file_create.html", result=response, user=name, ip=ip)


@app.route('/file_download', methods=['POST', 'GET'])
def file_download():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    global igor
    global ip
    path += '/'
    path += filename
    host = json.loads(requests.get(igor, json={"command": "file_download",
                                                                       "args": {"username": name,
                                                                                "path": path}}).text)
    args = host['args']
    host = args['ip']
    port = args['port']
    s = socket.socket()
    command = {"command": "file_download",
               "args": {
                   "username": name,
                   "path": path
               }
               }
    try:
        requests.get('http://' + str(host) + ':' + str(1337), json=command, timeout=1)
    except requests.exceptions.ReadTimeout:
        pass
    s.connect((host, port))
    filename = command["args"]["path"].split("/")[-1]
    with open('{}'.format(filename), 'wb') as f:
        while True:
            data = s.recv(1024)
            if not data:
                break
            f.write(data)
    f.close()
    s.close()
    return render_template("file_download.html", result=host, user=name, filename=filename, ip=ip)


@app.route('/download', methods=['POST', 'GET'])
def downloadFile ():
    global ip
    path = request.form.getlist('name')[0]
    return send_file(path, as_attachment=True, ip=ip)



@app.route('/file_upload', methods=['POST', 'GET'])
def file_upload():
    name = current_user
    global path
    global ip
    global igor
    path += '/'
    fileplace = ''

    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        fileplace = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    host = json.loads(requests.get(igor, json={"command": "file_upload",
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
               "path": path + filename
           }
           }
    try:
        requests.get('http://' + host + ':' + str(1337), json=command, timeout=1)
    except requests.exceptions.ReadTimeout:
        pass
    s.connect((host, 7331))
    filepath = path
    f = open(fileplace, 'rb')
    l = f.read(1024)
    while l:
        s.send(l)
        l = f.read(1024)
    f.close()
    s.close()
    return render_template("file_upload.html", result=host, user=name, ip=ip)


@app.route('/file_delete', methods=['POST', 'GET'])
def file_delete():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    global ip
    global igor
    path += '/'
    path += filename
    response = json.loads(
        requests.get(igor,
                     json={"command": "file_delete", "args": {"username": name, "path": path}}).text)

    return render_template("file_delete.html", result=response, user=name, ip=ip)


@app.route('/file_info', methods=['POST', 'GET'])
def file_info():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    global igor
    global ip
    path += '/'
    path += filename
    response = json.loads(
        requests.get(igor,
                     json={"command": "file_info", "args": {"username": name, "path": path}}).text)
    return render_template("file_info.html", result=response, user=name, ip=ip)


@app.route('/file_copy', methods=['POST', 'GET'])
def file_copy():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    global igor
    global ip
    path += '/'
    path += filename
    response = json.loads(
        requests.get(igor,
                     json={"command": "file_copy", "args": {"username": name, "path": path}}).text)
    return render_template("file_copy.html", result=response, user=name, ip=ip)


@app.route('/file_move', methods=['POST', 'GET'])
def file_move():
    name = current_user
    filename = request.form.getlist('filename')[0]
    path_to_move = '/' + request.form.getlist('path_to_move')[0] + '/' + filename
    global path
    global igor
    global ip
    path += '/'
    path += filename
    response = json.loads(
        requests.get(igor,
                     json={"command": "file_move",
                           "args": {"username": name, "src_path": path, "dst_path": path_to_move}}).text)
    return render_template("file_copy.html", result=response, user=name, ip=ip)


@app.route('/filesystem', methods=['POST', 'GET'])
def log_in():
    global current_user
    global path
    global igor
    global ip
    name = current_user
    name = request.form.getlist('name')[0]
    current_user = name
    path = ''
    response = json.loads(
        requests.get(igor,
                     json={"command": "list_dir", "args": {"username": name, "path": path}}).text)
    files = response['names']
    return render_template("filesystem.html", result=files, name=current_user, ip=ip)


@app.route('/filesystem_dir', methods=['POST', 'GET'])
def open_directory():
    global current_user
    global path
    global igor
    global ip
    name = current_user
    dirname = request.form.getlist('filename')[0]
    if path[1:(len(dirname) + 1)] != dirname:
        path += '/'
        path += dirname
    response = json.loads(
        requests.get(igor,
                     json={"command": "list_dir", "args": {"username": name, "path": path}}).text)
    files = response['names']
    return render_template("filesystem_dir.html", result=files, name=current_user, directory=path, ip=ip)


@app.route('/directory_create', methods=['POST', 'GET'])
def directory_create():
    global current_user
    name = request.form.getlist('dirname')[0]
    global path
    global igor
    global ip
    path += '/'
    path += name
    response = json.loads(
        requests.get(igor,
                     json={"command": "create_dir", "args": {"username": current_user, "path": path}}).text)
    return render_template("directory_create.html", result=response, user=current_user, ip=ip)


@app.route('/dir_delete', methods=['POST', 'GET'])
def delete_directory():
    name = current_user
    filename = request.form.getlist('filename')[0]
    global path
    global igor
    global ip
    print(path)
    path += '/'
    path += filename
    print(path)
    response = json.loads(
        requests.get(igor,
                     json={"command": "delete_dir", "args": {"username": name, "path": path}}).text)

    return render_template("dir_delete.html", result=response, user=name, ip=ip)


@app.route('/are_you_sure', methods=['POST', 'GET'])
def are_you_sure():
    global ip
    name = current_user
    filename = request.form.getlist('filename')[0]
    return render_template("are_you_sure.html", result=filename, user=name, ip=ip)


@app.route('/are_you_sured', methods=['POST', 'GET'])
def are_you_sured():
    global ip
    name = current_user
    filename = request.form.getlist('filename')[0]
    return render_template("are_you_sured.html", result=filename, user=name, ip=ip)


current_user = ''
path = ''
UPLOAD_FOLDER = './upload_folder'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
igor = 'http://10.0.16.80:1338'
ip = 'http://10.1.1.131:5000/'

if __name__ == '__main__':
    app.run(host='10.1.1.131', port=5000)
