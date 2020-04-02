import json
import session.choices
from django.contrib.staticfiles import finders


def load_json(path: str):
    with open(finders.find(path), 'rb') as file:
        output = json.load(file)
    if output is not None:
        return output
    else:
        raise FileNotFoundError("JSON at {} not found".format(path))


class OptimizerInfo(object):
    def __init__(self):
        self.length = len(session.choices.TEST_NUMBER_CHOICES)


optimizer_info = OptimizerInfo()

common_cura_qulity_types = [
        "a",
        "adaptive",
        "alya_normal",
        "alyanx_normal",
        "b",
        "best",
        "c",
        "coarse",
        "course",
        "d",
        "draft",
        "Draft",
        "e",
        "Engineering",
        "extra coarse",
        "extracoarse",
        "extra_course",
        "extrafast",
        "extrafine",
        "extra_high",
        "extreme",
        "f",
        "fast",
        "fine",
        "Fine",
        "g",
        "good",
        "h",
        "high",
        "kupido_normal",
        "low",
        "normal",
        "Normal",
        "slightlycoarse",
        "sprint",
        "standard",
        "super",
        "superdraft",
        "supersprint",
        "thickerdraft",
        "ultra",
        "ultrahigh",
        "ultrasprint",
        "verydraft"]
