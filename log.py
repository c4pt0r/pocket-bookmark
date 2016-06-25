import config
import logging
import sys

logger = logging.getLogger("app")
logger.setLevel(config.LOG_LEVEL)

ch = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter("[%(asctime)s] [%(filename)s:%(lineno)s] [%(levelname)s] %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)
