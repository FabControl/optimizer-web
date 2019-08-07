import json
import session.choices


def load_json(path: str):
    with open(path, mode="r") as file:
        output = json.load(file)
    if output is not None:
        return output
    else:
        raise FileNotFoundError("JSON at {} not found".format(path))


class OptimizerInfo(object):
    def __init__(self):
        self.length = len(session.choices.TEST_NUMBER_CHOICES)


optimizer_info = OptimizerInfo()
