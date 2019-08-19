import requests
from base64 import b64decode
import json


class ApiClient(object):
    def __init__(self, remote_url: str):
        self.url = remote_url
        self.persistence = None
        self.gcode = None
        self._last_response = None

    def get_template(self):
        return json.loads(requests.post("http://" + self.url + ":5000").text)["persistence"]

    def get_gcode(self, arguments):
        response = requests.post("http://" + self.url + ":5000", json=arguments)
        self._last_response = response
        if response.status_code == 200:
            response_parsed = json.loads(response.text)
            self.persistence = response_parsed["persistence"]
            if response_parsed["content"] is not None:
                # A gcode file has been returned
                self.gcode = b64decode(response_parsed["content"])








if __name__ == "__main__":
    api = ApiClient("127.0.0.1")
    with open("212.json") as jsonfile:
        session212 = json.load(jsonfile)
