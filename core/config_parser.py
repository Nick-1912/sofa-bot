import yaml
import os


class Configs:
    MAIN_CONFIG_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yaml')


class MainConfig(Configs):
    def __new__(cls, *args, **kwargs):
        with open(Configs.MAIN_CONFIG_PATH, 'r') as f:
            cfg = yaml.safe_load(f)
        return cfg


class SeleniumConfig(MainConfig):
    def __new__(cls, *args, **kwargs):
        temp_config = MainConfig()
        return temp_config['parsing methods']['selenium']


class UndetectedSeleniumConfig(MainConfig):
    def __new__(cls, *args, **kwargs):
        temp_config = MainConfig()
        return temp_config['parsing methods']['undetected selenium']


class OpenApiConfig(MainConfig):
    def __new__(cls, *args, **kwargs):
        temp_config = MainConfig()
        return temp_config['parsing methods']['open api']


class DatabaseConfig(MainConfig):
    def __new__(cls, *args, **kwargs):
        temp_config = MainConfig()
        return temp_config['database']


if __name__ == '__main__':
    temp_cfg = UndetectedSeleniumConfig()
    print(temp_cfg)
