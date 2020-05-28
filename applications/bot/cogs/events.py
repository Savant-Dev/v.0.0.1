from discord.ext import commands
from discord import Message, Member, Role

from ...constants import Webhooks


class EventLogging(commands.Cog):
    ''' Logs Passive Events in the Server '''

    def __init__(self, bot):
        self.bot = bot
        self.log = bot.log


    @staticmethod
    def build_event():
        details = {
            "User": None,
            "Guild": None,
            "Reason": None,
            "Duration": None,
            "Moderator": None,
            "log_channel": None,
        }

        return details

    @commands.Cog.listener()
    async def on_message_edit(self, before: Message, after: Message):
        if not before.guild or not after.guild:
            return
        if before.author.bot:
            return
        if before.embeds != after.embeds:
            return

        event = self.build_event()

        event["User"] = before.author

        clean_before = before.content.replace('```', '')
        clean_after = after.content.replace('```', '')

        if clean_before.startswith('`'):
            clean_before = ' ' + clean_before
        if clean_after.startswith('`'):
            clean_after = ' ' + clean_after
        if clean_before.endswith('`'):
            clean_before += ' '
        if clean_after.endswith('`'):
            clean_after += ' '

        if len(before.content) > 750 or len(after.content) > 750:
            event["Reason"] = (
                f"**Original:** ```{clean_before}```\n"
                f"**Updated:** {after.jump_url}"
            )

        else:
            event["Reason"] = (
                f"**Original:** ```{clean_before}``` \n"
                f"**Updated:** ```{clean_after}```"
            )

        event["log_channel"] = Webhooks.message_logs

        await self.bot.log_event('message_edited', event_details=event)

    @commands.Cog.listener()
    async def on_message_delete(self, message: Message):
        if not message.guild:
            return
        if message.author.bot:
            return

        event = self.build_event()

        event["User"] = message.author
        event["Reason"] = (
            f"**Original:** ```{message.content}```"
        )

        event["log_channel"] = Webhooks.message_logs

        await self.bot.log_event('message_deleted', event_details=event)


def setup(bot):
    bot.add_cog(EventLogging(bot))
