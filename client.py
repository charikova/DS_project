import json
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
    response = json.loads(requests.get('http://13.59.57.151:8589', json={"command": "init", "args": {"username": name}}).text)
    return render_template("initialize.html", result=response)


@app.route('/file_create', methods=['POST', 'GET'])
def file_create():
    name = request.form.getlist('filename')[0]
    response = json.loads(requests.get('http://13.59.57.151:8589', json={"command": "init", "args": {"username": name}}).text)
    return render_template("file_create.html", result=response)


def file_read(self, filepath):
    return


def file_write(self, filepath):
    return


def file_delete(self, filepath):
    return


def file_info(self, filepath):
    return


def file_copy(self, filepath, dest_filepath):
    return


def file_move(self, filepath, dest_filepath):
    return


@app.route('/filesystem', methods=['POST', 'GET'])
def log_in():
    name = request.form.getlist('username')[0]
    response = json.loads(
        requests.get('http://13.59.57.151:8589', json={"command": "listdir", "args": {"username": name, "path": "/"}}).text)
    print(response)
    return render_template("filesystem.html", result=response)


def open_directory():
    return


@app.route('/directory_create', methods=['POST', 'GET'])
def directory_create():
    name = request.form.getlist('dirname')[0]
    response = json.loads(requests.get('http://10.1.1.141:1337', json={"command": "init", "args": {"username": name}}).text)
    return render_template("directory_create.html", result=response)


def delete_directory(self, filepath):
    return


if __name__ == '__main__':
    app.run(debug=True)