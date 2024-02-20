import logging

console_out = logging.StreamHandler()
file_log = logging.FileHandler("application.log", mode="w")
logging.basicConfig(handlers=(file_log, console_out), level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]: %(message)s')


def log_print(func):
    def _wrapper(*args, **kwargs):
        logging.info(f'Call - {func.__name__}{args} {kwargs}')
        result = func(*args, **kwargs)
        logging.info(f'Result - {func.__name__}{args} {kwargs}: {result}')
        return result
    return _wrapper

