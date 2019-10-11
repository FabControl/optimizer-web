from os import environ
import json

if environ.get("OPTIMIZER_READ_CONFIG_FILE"):
    config = environ
else:
    with open("/etc/config.json") as config_file:
        config = json.load(config_file)
