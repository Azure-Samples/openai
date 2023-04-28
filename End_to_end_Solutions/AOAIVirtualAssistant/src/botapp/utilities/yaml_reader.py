import yaml


class YAMLReader:
    @staticmethod
    def read_yaml(file_path) -> dict:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)