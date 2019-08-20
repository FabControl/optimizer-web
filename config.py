import json

with open("/etc/config.json") as config_file:
    config = json.load(config_file)
