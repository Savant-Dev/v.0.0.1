from colorama import init
from colorama import Fore
from colorama import Style
from os.path import abspath
from datetime import datetime

levels = {
    'TRACE': 0,
    'DEBUG': 1,
    'INFO': 2,
    'WARNING': 3,
    'ERROR': 4,
    'CRITICAL': 5,
}

class LoggerModule():
    ''' Customized Colored Output Logger '''

    def __init__(self, level: int):
        init()

        self.level = level

        directory = abspath(__file__).replace('logger.py', 'data/')
        self.logs = { key: directory + key for key in ['events', 'errors'] }

    def _write(self, message: str, *, error: bool=False) -> None:
        with open(self.logs['events'], 'a+') as log:
            log.write(message)

        if error:
            with open(self.logs['errors'], 'a+') as log:
                log.write(message)

    def _output(self, level: int, *, message: str) -> None:
        if level >= self.level:
            print(message)

    @staticmethod
    def _getTimeStamp() -> str:
        now = datetime.now()
        stamp = now.strftime('%m-%d-%y @ %H:%M:%S:%f')[:-3]

        return stamp

    def trace(self, locale: str, message: str) -> None:
        timestamp = self._getTimeStamp()

        file_output = f"[TRACE] {timestamp} ({locale}) --> {message} \n"
        color_output = f"{Fore.CYAN}[TRACE]{Style.RESET_ALL} {timestamp} ({locale}) --> {message}"

        self._write(file_output)
        self._output(0, message=color_output)

    def debug(self, locale: str, message: str) -> None:
        timestamp = self._getTimeStamp()

        file_output = f"[DEBUG] {timestamp} ({locale}) --> {message} \n"
        color_output = f"{Fore.GREEN}[DEBUG]{Style.RESET_ALL} {timestamp} ({locale}) --> {message}"

        self._write(file_output)
        self._output(1, message=color_output)

    def info(self, locale: str, message: str) -> None:
        timestamp = self._getTimeStamp()

        file_output = f"[INFO] {timestamp} ({locale}) --> {message} \n"
        color_output = f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {timestamp} ({locale}) --> {message}"

        self._write(file_output)
        self._output(2, message=color_output)

    def warn(self, locale: str, message: str) -> None:
        timestamp = self._getTimeStamp()

        file_output = f"[WARNING] {timestamp} ({locale}) --> {message} \n"
        color_output = f"{Fore.MAGENTA}[WARNING]{Style.RESET_ALL} {timestamp} ({locale}) --> {message}"

        self._write(file_output, error=True)
        self._output(3, message=color_output)

    def error(self, locale: str, message: str) -> None:
        timestamp = self._getTimeStamp()

        file_output = f"[ERROR] {timestamp} ({locale}) --> {message} \n"
        color_output = f"{Fore.YELLOW}[ERROR]{Style.RESET_ALL} {timestamp} ({locale}) --> {message}"

        self._write(file_output, error=True)
        self._output(4, message=color_output)

    def critical(self, locale: str, message: str) -> None:
        timestamp = self._getTimeStamp()

        file_output = f"[CRITICAL] {timestamp} ({locale}) --> {message} \n"
        color_output = f"{Fore.RED}[CRITICAL]{Style.RESET_ALL} {timestamp} ({locale}) --> {message}"

        self._write(file_output, error=True)
        self._output(5, message=color_output)


def getLogger(level: str) -> LoggerModule:
    try:
        log_level = levels[level]
    except KeyError:
        log_level = levels['TRACE']

    return LoggerModule(log_level)
