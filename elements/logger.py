import logging
from logging.handlers import RotatingFileHandler


# -------------------------------------------------
# Object initialized at startup to provide a
# rotate file mechanism
# default size : 100 ko
# default file : 5
# -------------------------------------------------
class Logger:
    def __init__(self, configuration=None, max_size=100000, count=5):
        self.logger = logging.getLogger()
        self.handler = None
        self.configure_log_format(configuration, max_size, count)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    # read log_level from configuration file. Default is WARNING
    def configure_log_format(self, config, max_size, count):
        try:
            conf = config['log_level']
            if 'debug' in conf:
                self.logger.setLevel(logging.DEBUG)
            elif 'info' in conf:
                self.logger.setLevel(logging.INFO)
            elif 'warning' in conf:
                self.logger.setLevel(logging.WARNING)
            elif 'error' in conf:
                self.logger.setLevel(logging.ERROR)
        except (KeyError, TypeError):
            self.logger.setLevel(logging.WARNING)

        if not self.handler:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            try:
                self.handler = RotatingFileHandler(config['log_file'], maxBytes=max_size, backupCount=count)
                self.handler.setFormatter(formatter)
                self.logger.addHandler(self.handler)
            except (KeyError, TypeError):
                # no log if no log_file configuration
                pass
