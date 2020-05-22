from os import listdir
from os.path import abspath
from discord.ext import commands

from ..utils import ConfigurationNotFound


class ExtensionHandler():

    @classmethod
    def _getAvailableCogs(cls):
        invalid_extensions = ['__init__.py', '__pycache__']
        directory = abspath(__file__).replace('__init__.py', '')

        cogs = ['applications.bot.cogs.' + file[:-3] for file in listdir(directory) if file not in invalid_extensions]

        return cogs

    @classmethod
    def register_all(cls, bot: commands.Bot):
        available = cls._getAvailableCogs()

        for extension in available:
            try:
                bot.load_extension(extension)

            except commands.ExtensionAlreadyLoaded:
                continue
            except commands.NoEntryPointError:
                bot.log.error('discord', f'{extension} is missing a setup() function')

            except commands.ExtensionFailed as error:
                if isinstance(error.original, ConfigurationNotFound):
                    bot.log.error('discord', f'Configuration File Not Found for: {extension}')
                else:
                    bot.log.error('discord', f'{extension} Failed - {error.original}')

            else:
                bot.log.debug('discord', f'Loaded Extension: {extension}')

        bot.log.info('discord', f'Initialized {len(bot.cogs)}/{len(available)} Available Extensions')

    @classmethod
    def unregister_all(cls, bot: commands.Bot):
        available = cls._getAvailableCogs()

        for extension in available:
            try:
                bot.unload_extension(extension)

            except commands.ExtensionNotLoaded:
                continue
            else:
                bot.log.debug('discord', f'Unloaded Extension: {extension}')

        bot.log.info('discord', f'Unloaded {len(available) - len(bot.cogs)}/{len(available)} Available Cogs')
