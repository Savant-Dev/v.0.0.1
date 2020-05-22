import asyncio
import discord

from typing import Optional
from discord.ext import tasks
from discord.ext import commands

from ...api import leveling
from ..utils.embeds import LevelingEmbeds



class LevelingCog(leveling.API, commands.Cog):
    ''' Interface for Leveling/Leaderboards in Discord '''

    def __init__(self, bot):
        self.bot = bot

        leveling.API.__init__(self, self.bot.log)


    # Extension Configuration

    async def configure(self):
        self.bot.log.trace('discord', 'Configuring Leveling Extension ...')

        pulled = await self.bot.update_extension('leveling-cog')

        self.config = pulled
        embed = discord.Embed(
            color = 0x00ff00,
            description = 'Configured Leveling Extension'
        )

        self.bot.log.debug('discord', 'Successfully Configured Leveling Extension')
        return await self.bot.dispatch_webhook(url=self.bot.developer_log, message=embed)

    async def reconfigure(self):
        self.bot.log.trace('discord', 'Reconfiguring Leveling Extension ...')

        pulled = await self.bot.update_extension('leveling-cog')
        changing = [{key: value} for key, value in pulled.items() if self.config[key] != value]

        if len(changing) > 0:
            embed = discord.Embed(
                title = 'Updated Leveling Extension',
                color = 0x00ff00,
                description = '\n'.join([f"{key}: {self.config[key]} --> {changing[key]}" for key in changing])
            )

            self.config = pulled
            await self.bot.dispatch_webhook(url=self.bot.developer_log, message=embed)
            return self.bot.log.trace('discord', 'Leveling Extension has been Updated - Check Developer Logs')

        else:
            return self.bot.log.trace('discord', 'Skipping Leveling Extension ... No changes found')

    # End Region

    # Region: Command Interfaces

    @commands.group(name='xp')
    @commands.guild_only()
    async def xp(self, ctx):
        if not ctx.invoked_subcommand:
            return await ctx.message.delete()

    @xp.command(name='search')
    async def guild_search(self, ctx, member: Optional[discord.Member]):
        if not member:
            member = ctx.author

        profile = await super().fetch_guild_user(guildId=ctx.guild.id, userId=member.id)
        embed = LevelingEmbeds.report_guild(profile, member=member)

        return await ctx.send(embed=embed)

    @xp.group(name='global')
    async def global_xp(self, ctx):
        if not ctx.invoked_subcommand:
            return await ctx.message.delete()

    @global_xp.command(name='search')
    async def global_search(self, ctx, member: Optional[discord.Member]):
        if not member:
            member = ctx.author

        profile = await super().fetch_global_user(userId=member.id)
        embed = LevelingEmbeds.report_global(profile, member=member)

        return await ctx.send(embed=embed)

    # Moderator Only Commands
    @xp.command(name='add')
    async def add_user(self, ctx, member: discord.Member):
        try:
            await super().insert_guild_user(guildId=ctx.guild.id, userId=member.id)
        except leveling.UserOverwriteError:
            embed = LevelingEmbeds.UserAlreadyExists(member)
            return await ctx.send(embed=embed)

        self.bot.log.trace('discord', f'Manually Created Record for {member.id} in {ctx.guild.id}')

        try:
            await super().insert_global_user(userId=member.id)
            self.bot.log.debug('discord', f'Manually Created Global Record for {member.id}')
        except leveling.UserOverwriteError:
            self.bot.log.trace('discord', f'Failed to Create Global Record for {member.id} - Record Already Exists')

        embed = LevelingEmbeds.ManuallyAdded(member, member=member)

        return await ctx.send(embed=embed)

    @xp.command(name='force')
    async def overwrite_user(self, ctx, member: discord.Member, experience: int):
        data = (ctx.guild.id, member.id, experience, 0)
        await super().force_insert(data, guild=True)


def setup(bot):
    bot.add_cog(LevelingCog(bot))
