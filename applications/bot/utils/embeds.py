from discord import Embed, Member
from typing import Optional, Any, List

from ...constants import Colors

# Embed Configuration
username = "Project S"
avatar_url = "https://cdn.discordapp.com/attachments/697344429932937226/697344547381968976/Logo_-_Standalone.png"

footer = "Provided By SimplySavant"
footer_icon = (
    "https://cdn.discordapp.com/attachments/697344429932937226/697345663486263336/1200px-Python-logo-notext.svg.png"
)


class LevelingEmbeds():
    color = Colors.soft_green

    @classmethod
    def format(cls, embed: Embed, *, user: Optional[Member]) -> Embed:
        embed.set_author(name=username, icon_url=avatar_url)
        embed.set_footer(text=footer, icon_url=footer_icon)
        if user:
            embed.set_thumbnail(url=user.avatar_url)

        # Set Timestamp
        return embed

    @classmethod
    def Configured(cls) -> Embed:
        embed = Embed(
            title = 'Extension Status Updated',
            color = cls.color,
            description = 'Leveling Extension has been Configured'
        )

        return cls.format(embed, user=None)

    @classmethod
    def UpdatedConfig(cls, changed: List[dict]) -> Embed:
        embed = Embed(
            title = 'Extension Status Updated',
            color = cls.color,
            description = 'New Leveling Configuration \n\n'
        )

        for change in changed:
            for key, value in change.items():
                embed.description += f'{key} --> {value} \n'


        return cls.format(embed, user=None)

    @classmethod
    def ReportGuildXP(cls, profile: Any, *, member: Member) -> Embed:
        embed = Embed(
            title = 'Guild XP Search Results',
            color = cls.color
        )

        embed.description = (
            f"Guild ID: {profile.guildId} \n"
            f"User ID: {profile.userId} \n\n"
            f"**Total Experience:** {profile.experience}\n"
            f"**Artificial Experience:** {profile.artificial} \n\n"
        )

        embed.add_field(
            name = "Level Statistics",
            value = (
                f"**Current Level:** {profile.level.current} \n"
                f"**Next Level:** {profile.level.next} \n"
                f"**XP Left:** {profile.level.remaining}"
            ),
            inline = True
        )

        embed.add_field(
            name = "Prestige Statistics",
            value = (
                f"**Current Prestige:** {profile.prestige.current} \n"
                f"**Next Promotion:** {profile.prestige.next} \n"
                f"**Remaining XP:** {profile.prestige.remaining}"
            ),
            inline = True
        )

        return cls.format(embed, user=member)

    @classmethod
    def ReportGlobalXP(cls, profile: Any, *, member: Member) -> Embed:
        embed = Embed(
            title = 'Global XP Search Results',
            color = cls.color
        )

        embed.description = (
            f"User ID: {profile.userId} \n"
            f"**Total Experience:** {profile.experience}\n\n"
        )

        embed.add_field(
            name = "League Statistics",
            value = (
                f"**Current League:** {profile.league.current} \n"
                f"**Next League:** {profile.league.next} \n"
                f"**XP Needed:** {profile.league.remaining}"
            ),
            inline = True
        )

        embed.add_field(
            name = "Boost Statistics",
            value = (
                f"**Currently Gaining:** {profile.boost.current} \n"
                f"**Next Raise:** {profile.boost.next} \n"
                f"**XP Needed:** {profile.boost.remaining}"
            ),
            inline = True
        )

        return cls.format(embed, user=member)

    @classmethod
    def UserAlreadyExists(cls, member: Member) -> Embed:
        embed = Embed(
            title = 'Unable to Add User',
            color = Color.soft_red
        )

        embed.description = (
            f"User ID: {member.id} already has a profile with this guild \n"
            f"If you experience errors, try restoring using the `!xp restore` command"
        )

        return cls.format(embed, user=None)

    @classmethod
    def ManuallyAdded(cls, member: Member) -> Embed:
        embed = Embed(
            title = 'Added User to Database',
            color = cls.color
        )

        embed.description = (
            f"Successfully Added {member.mention} to the Guild XP Database \n"
            f"If this user did not already have a Global Profile, it was also created."
        )

        return cls.format(embed, user=member)

    '''
        - GuildTop10
        - GuildRanking
        - GlobalTop10
        - GlobalRanking
        - Blacklisted
        - Whitelisted
        - NoChanges (for config)
        - Reconfigured (for config)
        - ProfileOverwrite (for logging)
    '''

class ModerationEmbeds():
    color = Colors.soft_orange

    @classmethod
    def format(cls, embed: Embed, *, user: Optional[Member]) -> Embed:
        embed.set_author(name=username, icon_url=avatar_url)
        embed.set_footer(text=footer, icon_url=footer_icon)
        if user:
            embed.set_thumbnail(url=user.avatar_url)

        # Set Timestamp
        return embed

    @classmethod
    def BulkDelete(cls, *, searched: int, amount: int, author: Optional[Member]) -> Embed:
        embed = Embed(
            title = 'Message Bulk Delete',
            color = cls.color
        )

        embed.description = (
            f"Messages Searched: {searched} \n"
            f"Messages Deleted: {amount} \n"
            f"Filtered By: {author}"
        )

        return cls.format(embed, user=None)

class CheckFailures():
    color = Colors.soft_red

    '''
        - DeveloperRestricted
        - PrivateCommand
        - ChannelRestriction(channels: List[Union[str, int]])
    '''
