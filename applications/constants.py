import os
import yaml

from enum import Enum
from pathlib import Path
from typing import Dict, List

log = None

default_path = ""
config_path = ""


def set_logger(logger: Any):
    global log

    log = logger


def env_constructor(loader, node):
    default = None

    if node.id == 'scaler':
        value = loader.construct_scaler(node)
        key = str(value)

    else:
        value = loader.construct_sequence(node)

        if len(value) >= 2:
            key = value[0]
            default = value[1]

        else:
            key = value[0]

    return os.getenv(key, default)

yaml.SafeLoader.add_constructor("!ENV", env_constructor)
yaml.SafeLoader.add_constructor("!REQUIRED_ENV", env_constructor)

with open('default-config.yml', encoding="UTF-8") as f:
    _config = yaml.safe_load(f)

if Path("config.yml").exists():
    with open("../config.yaml", encoding="UTF-8") as f:
        _config = yaml.safe_load(f)


class YAMLGetter(type):
    subsection = None

    def __getattr__(cls, name):
        name = name.lower()

        try:
            if cls.subsection:
                return _config[cls.section][cls.subsection][name]
            return _config[cls.section][name]

        except KeyError:
            if cls.subsection:
                path = '.'.join((cls.section, cls.subsection, name))
            else:
                path = '.'.join((cls.section, name))

            if log:
                log.critical('Configuration', f'Unable to Find YAML Path: {path}')
            else:
                print(f'Unable to Access YAML Path: {path}')
            raise

    def __getitem__(cls, name):
        return cls.__getattr__(name)

    def __iter__(cls):
        for name in cls.__annotations__:
            yield name, getattr(cls, name)


class Bot(metaclass=YAMLGetter):
    section = "bot"

    prefix: str
    token: str


class Filter(metaclass=YAMLGetter):
    section = "filter"

    word_watchlist: List[str]

    role_whitelist: List[int]
    channel_whitelist: List[int]


class Colors(metaclass=YAMLGetter):
    section = "style"
    subsection = "colors"

    soft_red: int
    soft_green: int
    soft_orange: int
    soft_yellow: int


class Emojis(metaclass=YAMLGetter):
    section = "style"
    subsection = "emojis"

    pencil: str
    check_mark: str
    cross_mark: str


class Icons(metaclass=YAMLGetter):
    section = "style"
    subsection = "icons"

    general_edit: str

    bulk_delete: str
    message_edit: str
    message_delete: str

    user_mute: str
    user_unmute: str
    user_updated: str
    user_verfied: str
    user_banned: str
    user_unbanned: str
    user_warned: str

    task_due: str
    task_expired: str
    task_submitted: str


class Channels(metaclass=YAMLGetter):
    section = "guild"
    subsection = "channels"

    welcome: int
    react_roles: int
    announcements: int

    event_logs: int
    message_logs: int
    moderator_logs: int

    bot_commands: int

    mods: int
    admins: int
    alerts: int

    log_channels: List[int]
    staff_channels: List[int]


class Roles(metaclass=YAMLGetter):
    section = "guild"
    subsection = "roles"

    muted: int
    blacklisted: int

    verified: int
    announcements: int

    owner: int
    admins: int
    moderators: int

    staff_roles: List[int]
    infraction_roles: List[int]

class Webhooks(metaclass=YAMLGetter):
    section = "guild"
    subsection = "webhoooks"

    developer_logs: str

class Event(Enum):
    guild_update = "guild_update"

    guild_role_create = "guild_role_create"
    guild_role_delete = "guild_role_delete"
    guild_role_update = "guild_role_update"

    guild_channel_create = "guild_channel_create"
    guild_channel_delete = "guild_channel_delete"
    guild_channel_update = "guild_channel_update"

    member_ban = "member_ban"
    member_unban = "member_unban"

    member_join = "member_join"
    member_remove = "member_remove"

    member_update = "member_update"

    message_edit = "message_edit"
    message_delete = "message_delete"

    voice_state_update = "voice_state_update"
