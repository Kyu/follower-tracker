import json


def save_dict_to_file(dct: dict, filename: str) -> None:
    with open(filename, 'w') as file:
        file.write(json.dumps(dct, indent=4))


def load_follower_dict(filename: str) -> dict:
    try:
        with open(filename, 'r') as file:
            dct = json.load(file)
    except FileNotFoundError:
        dct = {'mutuals': [], 'followers': []}
        save_dict_to_file(dct, filename)

    return dct


def get_config(config_filename: str) -> dict:
    with open(config_filename, 'r') as cfg:
        config = json.load(cfg)

    return config
