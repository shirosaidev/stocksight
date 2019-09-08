import yaml
from definitions import PROJECT_SRC_PATH

config_file = PROJECT_SRC_PATH+'/config.yml'

def load_config(config_file):
    data = None
    with open(config_file) as json_data_file:
        data = yaml.load(json_data_file, yaml.FullLoader)
    return data

config = load_config(config_file)
