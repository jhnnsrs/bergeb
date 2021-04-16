import logging

def setLogging(log_level, log_stream=False):
    LOGFORMAT = "  s%(levelname)-8s%(reset)s | %(message)s%(reset)s"
    file = logging.FileHandler("logs.txt")
    logging.root.setLevel(log_level)
    file.setLevel(log_level)


    
    logger = logging.getLogger()
    logger.setLevel(log_level)

    if log_stream:
        stream = logging.StreamHandler()
        logging.root.setLevel(log_level)
        stream.setLevel(log_level)

        try:
            from colorlog import ColoredFormatter
            LOGFORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(message)s%(reset)s"
            formatter = ColoredFormatter(LOGFORMAT)
            stream.setFormatter(formatter)
        except:
            pass

        logger.addHandler(stream)

    logger.addHandler(file)
