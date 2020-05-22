from os import environ
from multiprocessing import Process

from .log import logger
from .bot import connect
from .api import ServerPing


log = logger.getLogger(level='DEBUG')


class ProcessAllocation():
    ''' Starts all the Applications in their own Process '''

    tokens = {}

    @classmethod
    def fetch_tokens(cls) -> None:
        for key in ['discord_token', ]:
            try:
                token = environ[key]
            except KeyError:
                log.warn('startup', f'Unable to Locate Token for {key}')
                token = False

            app_name = key.split('_')[0]
            cls.tokens[app_name] = token

    @classmethod
    def initialize(cls) -> None:
        log.info('startup', 'Loading Application Processes ...')

        log.trace('startup', 'Ensuring Server Connection ...')
        status = ServerPing.start(log)

        if not status:
            log.critical('startup', 'Exiting Application ...')
            # Return Here to Exit Application (or call sys.exit)

        if cls.tokens['discord']:
            bot = Process(target=connect, args=(cls.tokens['discord'], log))
            log.info('startup', 'Spawning Discord Application ...')

            bot.start()
        else:
            log.critical('startup', 'Discord Application Failed to Start - No Token Found')

        # Spawn Website Process
        # Continue Main Process with Resource Monitoring
