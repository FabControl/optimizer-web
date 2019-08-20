import requests
from base64 import b64decode
import json


class ApiClient(object):
    def __init__(self, remote_url: str, port: int = 80):
        self.url = remote_url
        self.persistence = None
        self.port = port
        self.gcode = None
        self.response = None

    def get_response(self, **kwargs):
        response = requests.post("http://" + self.url + ":{}".format(str(self.port)), json=kwargs)
        self.response = response

    def get_template(self):
        self.get_response()
        if self.response.status_code == 200:
            self.persistence = json.loads(self.response.text)["persistence"]
            return self.persistence

    def get_gcode(self, arguments):
        self.get_response(**arguments)
        if self.response.status_code == 200:
            response_parsed = json.loads(self.response.text)
            self.persistence = response_parsed["persistence"]
            if response_parsed["content"] is not None:
                # A gcode file has been returned

                # Decode from b64 and then from bytes to UTF-8
                self.gcode = b64decode(response_parsed["content"]).decode()
                return self.gcode


if __name__ == "__main__":
    api = ApiClient("ec2-54-93-100-66.eu-central-1.compute.amazonaws.com")
    with open("212.json") as jsonfile:
        session212 = json.load(jsonfile)
