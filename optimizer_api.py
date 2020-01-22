import requests
from base64 import b64decode
import simplejson as json
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
        """
        Sends **kwargs as a JSON to base_url.
        :param kwargs:
        :return:
        """
        response = requests.post(self.base_url, json=kwargs)
        if response.status_code == 500:
            raise ConnectionError("Optimizer API encountered an error while processing the request.")
        self.response = response

    def get_template(self):
        """
        Returns a blank persistence dictionary. Useful for a blank testing session
        :return:
        """
        self.get_response()
        if self.response.status_code == 200:
            response = json.loads(self.response.text)
            self.persistence = response["persistence"]
            return self.persistence

    def get_test_info(self, persistence: dict):
        """
        Returns test specific information, like paramters to be tested, their units and precision
        :param persistence:
        :return:
        """
        return json.loads(requests.post(self.base_url + "/test_info", json=persistence).text)

    def return_data(self, arguments, output: str = "gcode"):
        """
        Returns either a persistence dict or a gcode when a valid persistence is passed as a dict or string.
        :param arguments:
        :param output:
        :return:
        """
        self.get_response(**arguments)
        if self.response.status_code == 200:
            response_parsed = json.loads(self.response.text)
            self.persistence = response_parsed["persistence"]
            self.test_info = response_parsed["test_info"]
            if response_parsed["content"] is not None:
                # A gcode file has been returned

                # Decode from b64 and then from bytes to UTF-8
                self.gcode = b64decode(response_parsed["content"]).decode()
                if output == "gcode":
                    return self.gcode
                elif output == "persistence":
                    return self.persistence
                else:
                    raise KeyError("Specified output is invalid. Valid outputs are 'gcode'(default) and 'persistence'.")

    def get_routine(self, mode: str = "full"):
        """
        Returns information about 3DOptimizer testing routine
        :param mode: By default 'full', can also be 'primary' and 'secondary'.
        Will only return test numbers with such priority
        :return:
        """
        routine = json.loads(requests.get(self.base_url + "/routine").text)

        if mode == 'full':
            return routine

        elif mode == 'primary':
            primary_tests = {}
            for number, test in routine.items():
                if test['priority'] == 'primary':
                    primary_tests[number] = test
            return primary_tests

        elif mode == 'secondary':
            secondary_tests = {}
            for number, test in routine.items():
                if test['priority'] == 'secondary':
                    secondary_tests[number] = test
            return secondary_tests

        else:
            raise ValueError("Incorrect routine return mode selected. Valid modes are ['full', 'primary', 'secondary']")

    def get_config(self, slicer: str, persistence: dict):
        response = requests.post(self.base_url + "/config/" + slicer, json=persistence)
        if response.status_code == 500:
            raise ConnectionError("Optimizer API encountered an error while processing the request.")
        imported_json = json.loads(response.text)
        assert "content" in imported_json and "format" in imported_json
        return b64decode(imported_json["content"]), imported_json["format"]

    def get_report(self, persistence: dict):
        response = requests.post(self.base_url + "/report/", json=persistence)
        if response.status_code == 500:
            raise ConnectionError("Optimizer API encountered an error while processing the request.")
        imported_json = json.loads(response.text)
        assert "content" in imported_json and "format" in imported_json
        return b64decode(imported_json["content"]), imported_json["format"]

    @property
    def base_url(self):
        """
        Returns an assembled URL with protocol and port included
        :return:
        """
        return "http://" + self.url + ":{}".format(str(self.port))


api_client = ApiClient(config["OPTIMIZER_DNS"], port=80)


if __name__ == "__main__":
    api = ApiClient("127.0.0.1", port=5000)
    with open("212.json") as jsonfile:
        session212 = json.load(jsonfile)
