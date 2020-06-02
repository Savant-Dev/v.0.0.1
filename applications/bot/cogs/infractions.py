from typing import Optional
from discord.ext import commands
from discord import Member, Message

from ...constants import Webhooks
from ..utils.embeds import ModerationEmbeds


class InfractionCog(commands.Cog):
    ''' Easy Moderation Tracking Implementation '''

    def __init__(self, bot):
        self.bot = bot


    @commands.group(name='mod')
    @commands.has_permissions(manage_messages=True)
    async def moderation(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.message.delete()

    @moderation.command(name='purge', aliases=['clear', ])
    async def bulk_message_delete(self, ctx, quantity: int, filter: Optional[Member]) -> None:

        def bulk_check(message: Message) -> bool:
            if filter:
                return message.author.id == filter.id
            else:
                return True

        deleted = await ctx.channel.purge(limit=quantity, check=bulk_check)
        embed = ModerationEmbeds.BulkDelete(searched=quantity, amount=len(deleted), author=filter)

        return await ctx.send(embed=embed, delete_after=5)


def setup(bot):
    bot.add_cog(InfractionCog(bot))
