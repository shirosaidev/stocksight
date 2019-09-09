import yaml
from definitions import PROJECT_SRC_PATH

config_file = PROJECT_SRC_PATH+'/config.yml'


def load_config(yml_file):
    with open(yml_file) as json_data_file:
        data = yaml.load(json_data_file, yaml.FullLoader)
    return data

config = load_config(config_file)
