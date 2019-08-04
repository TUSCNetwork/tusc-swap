import yaml
import os

__all__ = ["cfg"]

with open(os.path.join(os.getcwd(), "configs/my_config_DO_NOT_UPLOAD.yaml"), 'r') as yamlfile:
    cfg = yaml.safe_load(yamlfile)

