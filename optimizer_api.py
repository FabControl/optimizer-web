import requests
from base64 import b64decode
import json
from config import config


class ApiClient(object):
    def __init__(self, remote_url: str, port: int = 80):
        self.url = remote_url
        self.persistence = None
        self.port = port
        self.gcode = None
        self.response = None
        self.test_info = None

    def get_response(self, **kwargs):
        response = requests.post(self.base_url, json=kwargs)
        self.response = response

    def get_template(self):
        self.get_response()
        if self.response.status_code == 200:
            response = json.loads(self.response.text)
            self.persistence = response["persistence"]
            self.test_info = response["test_info"]
            return self.persistence

    def get_test_info(self, persistence: dict):
        return json.loads(requests.post(self.base_url + "/test_info", json=persistence).text)

    def get_gcode(self, arguments):
        self.get_response(**arguments)
        if self.response.status_code == 200:
            response_parsed = json.loads(self.response.text)
            self.persistence = response_parsed["persistence"]
            self.test_info = response_parsed["test_info"]
            if response_parsed["content"] is not None:
                # A gcode file has been returned

                # Decode from b64 and then from bytes to UTF-8
                self.gcode = b64decode(response_parsed["content"]).decode()
                return self.gcode

    def get_routine(self):
        return json.loads(requests.get(self.base_url + "/routine").text)

    @property
    def base_url(self):
        return "http://" + self.url + ":{}".format(str(self.port))


api_client = ApiClient(config["OPTIMIZER_DNS"])


if __name__ == "__main__":
    api = ApiClient("127.0.0.1", port=5000)
    with open("212.json") as jsonfile:
        session212 = json.load(jsonfile)
