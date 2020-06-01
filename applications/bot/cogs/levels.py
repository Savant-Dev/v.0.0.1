import asyncio
import discord

from typing import Optional
from discord.ext import tasks
from discord.ext import commands

from .. import utils
from ...api import leveling
from ..utils.embeds import LevelingEmbeds


class LevelingCog(leveling.API, commands.Cog):
    ''' Interface for Leveling/Leaderboards in Discord '''

    def __init__(self, bot):
        self.bot = bot
        self.config = None
        self.fresh_config = True

        leveling.API.__init__(self, self.bot.log)

    def cog_unload(self):
        self.reconfigure_task.cancel()

    # Extension Configuration

    async def configure(self):
        self.bot.log.trace('discord', 'Configuring Leveling Extension ...')

        pulled = await self.bot.update_extension('leveling-cog')
        self.config = pulled

        await super().update_config()

        embed = LevelingEmbeds.Configured()
        await self.bot.dispatch_webhook(url=self.bot.developer_log, message=embed)

        return self.bot.log.debug('discord', 'Successfully Configured Leveling Extension')

    async def reconfigure(self):
        if self.fresh_config:
            self.bot.log.debug('discord', 'Fresh Configuration Detected - Skipping Loop ...')
            self.fresh_config = False
            return

        self.bot.log.trace('discord', 'Reconfiguring Leveling Extension ...')

        await super().update_config()

        pulled = await self.bot.update_extension('leveling-cog')

        if self.config:
            changing = [{key: value} for key, value in pulled.items() if self.config[key] != value]
        else:
            changing = [{key: value} for key, value in pulled.items()]

        if len(changing) > 0:
            embed = LevelingEmbeds.UpdatedConfig(changed=changing)
            await self.bot.dispatch_webhook(url=self.bot.developer_log, message=embed)

            self.config = pulled
            self.bot.log.trace('discord', 'Leveling Extension has been Updated - Check Developer Logs')

        else:
            return self.bot.log.trace('discord', 'Skipping Leveling Extension ... No changes found')

    @tasks.loop(minutes=30.0)
    async def reconfigure_task(self):
        await self.reconfigure()


    @commands.Cog.listener()
    async def on_ready(self):
        await self.configure()
        self.reconfigure_task.start()

    # End Region

    # Region: Command Interfaces
    # SubRegion: `!xp` Base Commands

    @commands.group(name='xp')
    @commands.guild_only()
    async def xp(self, ctx, target: Optional[discord.Member]):
        if not ctx.invoked_subcommand:
            await ctx.invoke(self.guild_search, target)

    @xp.command(name='search')
    @utils.channel_restricted(['bot-commands', ])
    async def guild_search(self, ctx, member: Optional[discord.Member]):
        if not member:
            member = ctx.author

        profile = await super().fetch_guild_user(guildId=ctx.guild.id, userId=member.id)
        embed = LevelingEmbeds.ReportGuildXP(profile, member=member)

        return await ctx.send(embed=embed)

    @xp.command(name='top10', aliases=["top", ])
    @utils.channel_restricted(['bot-commands', ])
    async def guild_top10(self, ctx):
        profiles = await super().fetch_guild_ranks(guildId=ctx.guild.id, limit=10)
        embed = LevelingEmbeds.GuildTop10(profiles)

        return await ctx.send(embed=embed)

    @xp.command(name='rank')
    @utils.channel_restricted('bot-commands')
    async def guild_ranking(self, ctx, user: Optional[discord.Member]):
        if not user:
            user = ctx.author

        position = await super().fetch_guild_ranks(guildId=ctx.guild.id, userId=user.id)
        embed = LevelingEmbeds.GuildRanking(user, position)

        return await ctx.send(embed=embed)

    # End SubRegion
    # SubRegion: `!xp global` Base Commands

    @xp.group(name='global')
    @utils.channel_restricted('bot-commands')
    async def global_xp(self, ctx, target: Optional[discord.Member]):
        if not ctx.invoked_subcommand:
            await ctx.invoke(self.global_search, target)

    @global_xp.command(name='search')
    async def global_search(self, ctx, member: Optional[discord.Member]):
        if not member:
            member = ctx.author

        profile = await super().fetch_global_user(userId=member.id)
        embed = LevelingEmbeds.ReportGlobalXP(profile, member=member)

        return await ctx.send(embed=embed)

    @global_xp.command(name='top10', aliases=["top", ])
    async def global_top10(self, ctx):
        profiles = await super().fetch_global_ranks(limit=10)
        embed = LevelingEmbeds.GlobalTop10(profiles)

        return await ctx.send(embed=embed)

    @global_xp.command(name='rank')
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def global_ranking(self, ctx, user: Optional[discord.Member]):
        if not user:
            user = ctx.author

        position = await super().fetch_global_ranks(userId=user.id)
        embed = LevelingEmbeds.GlobalRanking(user, position)

        return await ctx.send(embed=embed)

    # End SubRegion
    # SubRegion: `!xp` Moderator Commands

    @xp.command(name='ban', aliases=["block", ])
    @commands.has_permissions(manage_roles=True)
    async def infract_xpban(self, ctx, user: discord.Member, duration: Optional[str], *, reason: str):
        '''
            Ties into Infraction API or Infraction Cog?
            Prevents User from gaining XP by adding a "Blacklisted" Role
            Schedules the role_remove event for datetime.now() + timedelta(duration)

            Requirements:
                - Infraction API Method
                - Scheduling API (W.I.P)
        '''

    @xp.command(name='unban', aliases=["unblock", ])
    @commands.has_permissions(manage_roles=True)
    async def revoke_xpban(self, ctx, user: discord.Member):
        '''
            Ties into Infraction API or Infraction Cog to Remove Infraction from DB?
            Removes the Blacklisted Role and cancels the scheduled role_remove event

            Requirements:
                - Infraction API Method (ability to remove infractions)
                - Scheduling API (W.I.P)
        '''

    # End SubRegion
    # SubRegion: Developer Only Commands

    @xp.command(name='add')
    @utils.developer_only()
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

    @xp.command(name='force', aliases=["overwrite", "edit"])
    @utils.developer_only()
    async def overwrite_user(self, ctx, member: discord.Member, experience: int):
        data = (ctx.guild.id, member.id, experience, 0)
        await super().force_insert(data, guild=True)

        await ctx.invoke(self.guild_search, member)


    @xp.command(name='reconfigure', aliases=['configure', 'refresh'])
    @utils.developer_only()
    async def refresh_configuration(self, ctx):
        self.bot.log.debug('discord', f'Leveling Extension is being reconfigured by: {ctx.author}')

        changed = await self.reconfigure()

        if not changed:
            embed = LevelingEmbeds.NoChanges()
        else:
            embed = LevelingEmbeds.Reconfigured()

        return await ctx.send(embed=embed)




def setup(bot):
    bot.add_cog(LevelingCog(bot))
