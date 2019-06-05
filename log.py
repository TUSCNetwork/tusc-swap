import logging

__all__ = ["setup_custom_logger"]


def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    s_handler = logging.StreamHandler()
    s_handler.setFormatter(formatter)
    f_handler = logging.FileHandler(filename=name + '.log')
    f_handler.setFormatter(formatter)

    inner_logger = logging.getLogger(name)
    inner_logger.setLevel(logging.DEBUG)
    inner_logger.addHandler(s_handler)
    inner_logger.addHandler(f_handler)

    return inner_logger
