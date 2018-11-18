#!/usr/bin/env python3
def get_default_config(conf_path="default_config.dict"):
    with open(conf_path, "r", encoding="UTF-8") as conf:
        return eval(conf.read())