import json

from random import randint
from discord import Member, Embed

from ...utils import levelapi
from ...utils import ConfigurationError

from discord.ext import tasks
from discord.ext import commands

class TestCog(levelapi.LevelingAPI, commands.Cog, name='Leveling'):
    def __init__(self, bot):
        self.bot = bot

        try:
            levelapi.LevelingAPI.__init__(self, self.bot.log)
        except ConfigurationError:
            raise ConfigurationError('Leveling API Configuration File Not Found')

    @commands.Cog.listener()
    async def on_ready(self):
        await super().getAPIConfig()
        self.reconfigure.start()

    def cog_unload(self):
        self.reconfigure.cancel()

    @tasks.loop(minutes=15)
    async def reconfigure(self):
        self.bot.log.debug('discord', 'Checking Leveling Cog Configuration...')

        raw_config = await self.bot.fetch_config('leveling-cog')
        current = getattr(self, 'config', None)

        config = json.loads(raw_config["settings"])

        if current is None or config != current:
            hook_url = config['log_channel']

            e = Embed(
                description = 'Updating Leveling Cog Configuration ...',
                color = 0x00ff00
            )

            self.config = config

            await self.bot.send_webhook(url=hook_url, message=e)

        self.bot.log.trace('discord', 'Leveling Cog Configuration Up to Date')
        self.bot.log.debug('apis', 'Checking Leveling API Configuration ...')

        await super().getAPIConfig()

        self.bot.log.trace('apis', 'Leveling API Configuration Up to Date')

    @commands.group(name='xp')
    @commands.guild_only()
    async def xp(self, ctx):
        if not ctx.invoked_subcommand:
            return await ctx.message.delete()

    @xp.command(name='search', aliases=['lookup', 'profile'])
    async def guild_search_cmd(self, ctx, user: Member = None):
        if not user:
            user = ctx.author

        profile = await super().fetch_guild_user(guildId=ctx.guild.id, userId=user.id)

        embed = LevelingEmbeds.guild_report(data=profile)
        return await ctx.author.send(embed=embed)

    '''
        - xp rank|find
        - xp top|top10
        - xp grant|award (REQUIRES MANAGE_ROLES)
        - xp ban|blacklist (REQUIRES MANAGE_ROLES)
        - xp unban|whitelist (REQUIRES MANAGE_ROLES)
        - xp infractions (REQUIRES MANAGE_ROLES)
    '''

    @xp.group(name='global')
    async def globalxp(self, ctx):
        if not ctx.invoked_subcommand:
            return await ctx.message.delete()

    @globalxp.command(name='search', aliases=['lookup', 'profile'])
    async def global_search_cmd(self, ctx, user: Member = None):
        if not user:
            user = ctx.author

        profile = await super().fetch_global_user(userId=user.id)

        embed = LevelingEmbeds.global_report(data=profile)
        return await ctx.author.send(embed=embed)

    '''
        - xp global rank|find
        - xp global top|top10
        - xp global grant|award (REQUIRES DEVELOPER STATUS)
    '''


    @commands.command()
    async def subtest(self, ctx):
        self.reconfigure.start()

def setup(bot):
    bot.add_cog(TestCog(bot))
