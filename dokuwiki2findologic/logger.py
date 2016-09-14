import logging

logger = logging.getLogger('dokuwiki2findologic')
logger.setLevel(logging.ERROR)

handler = logging.StreamHandler()
format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
handler.setFormatter(logging.Formatter(format))
logger.addHandler(handler)


def set_level(level):
    """
    Sets the level of the dokuwiki2findologic logger.

    :param level: The level to set.
    :return: The previous level.
    """
    previous_level = logger.getEffectiveLevel()
    logger.setLevel(level)
    return previous_level
