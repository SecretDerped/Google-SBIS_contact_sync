import logging
from job import main_job

console_out = logging.StreamHandler()
file_log = logging.FileHandler("application.log", mode="w")
logging.basicConfig(handlers=(file_log, console_out), level=logging.WARNING,
                    format='[%(asctime)s | %(levelname)s]: %(message)s')


if __name__ == "__main__":
    main_job()