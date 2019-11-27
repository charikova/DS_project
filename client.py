import json
from flask import Flask, render_template, request
import requests

app = Flask(__name__, template_folder='templates')


@app.route('/')
def student():
    return render_template("index.html")


@app.route('/result', methods=['POST', 'GET'])
def result():
    name = request.form.getlist('Name')[0]
    print(name)
    response = requests.get('http://10.1.1.141:1337', json={"command": "init", "args": {"username": name}})
    print(response)
    #response = json.loads(request.get_json('http://10.1.1.141:1337', json={"command": "init", "args": {"username": name}}).text)
    #print(response["status"], ':', response["message"])
    #print('Available size:', response["size"])
    return render_template("result.html", result=result)


if __name__ == '__main__':
    app.run(debug=True)


def initialize(self, name):
    response = json.loads(requests.get('http://18.222.226.202:1338',
                                       json={"command": "init", "args": {"username": name}}).text)
    print(response["status"], ':', response["message"])
    print('Available size:', response["size"])
    return response


def file_create(self, filepath):
    return


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


def open_directory(self, filepath):
    return


def read_directory(self, filepath):
    return


def make_directory(self, filepath):
    return


def delete_directory(self, filepath):
    return


def client_run(self):
    return
