import json

import requests


class Client:
    def __init__(self):
        self.node = None

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


if __name__ == "__main__":
    c = Client()
    c.initialize("masha")

