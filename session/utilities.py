import json


def load_json(path: str):
    with open(path, mode="r") as file:
        output = json.load(file)
    if output is not None:
        return output
    else:
        raise FileNotFoundError("JSON at {} not found".format(path))
