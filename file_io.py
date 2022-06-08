import json

default_follower_dict = {"mutuals": [], "followers": []}


# Saves a dict to file, updated from old info if available
def save_dict_to_file(dct: dict, filename: str, old_info: dict = None) -> None:
    if old_info:
        old_info.update(dct)
        dct = old_info

    with open(filename, 'w') as file:
        file.write(json.dumps(dct, indent=4))


# Load user follower dict from json
def load_follower_dict(filename: str) -> dict:
    dct = {}
    try:
        with open(filename, 'r') as file:
            dct = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        save_dict_to_file(dct, filename)

    return dct


# Get config from json file as a dict
def get_config(config_filename: str) -> dict:
    with open(config_filename, 'r') as cfg:
        config = json.load(cfg)

    return config


# Append text to a file
def append_text_to_file(text: str, file_name: str):
    with open(file_name, 'a', encoding="utf-8") as file:
        file.write(text)
