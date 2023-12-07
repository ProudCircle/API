import yaml

class Config:
    _config = None

    @classmethod
    def load_config(cls, config_file_path='config.yaml'):
        print('Loading configuration file...')
        if cls._config is None:
            with open(config_file_path, 'r') as file:
                cls._config = yaml.safe_load(file)
        return cls._config

    @classmethod
    def get(cls, key):
        return cls._config.get(key)


config = Config.load_config()
