import sys


def log_error(logger, error, msg, result):
    logger.error(msg)
    logger.debug('Error: {}'.format(sys.exc_info()[0]))
    logger.debug(str(error))
    result['status'] = "KO"
