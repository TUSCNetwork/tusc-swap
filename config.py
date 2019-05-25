import yaml

__all__ = ["cfg"]

with open("configs/local_config.yaml", 'r') as yamlfile:
    cfg = yaml.safe_load(yamlfile)

