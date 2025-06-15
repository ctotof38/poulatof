#!/usr/bin/env python

import argparse
import json
from elements.logger import Logger
from elements.email_sender import EmailSender


def read_config_file(file):
    with open(file, 'r') as f:
        line = f.read()
        return json.loads(line)


default_config_file = "chicken.json"
configuration = None
RASPBERRY_TEMP = "/sys/class/thermal/thermal_zone0/temp"


def get_cpu_temperature_sysfile(logger):
    try:
        with open(RASPBERRY_TEMP, "r") as f:
            temp_str = f.read().strip()
            temp_milli_celsius = int(temp_str)
            return temp_milli_celsius / 1000.0
    except FileNotFoundError:
        logger.error(f"file not found: {RASPBERRY_TEMP}")
        return None
    except Exception as e:
        logger.error(f"can't read temperature: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help=u'configuration file, default is chicken.json', required=False)
    parser.add_argument('-d', '--debug', action='store_true', help=u'activate debug log', required=False)
    parameters = parser.parse_args()

    try:
        if parameters.config:
            configuration = read_config_file(parameters.config)
        else:
            configuration = read_config_file(default_config_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        print("can't find configuration file, or bad content, try option -h !")
        exit(1)

    logger = Logger(configuration)
    temp = get_cpu_temperature_sysfile(logger)

    email = EmailSender(configuration, logger)

    email.send_message(f"temperature: {temp} °c", "start door management")
