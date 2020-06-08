import os
import yaml

from typing import List
from pathlib import Path
from dotenv import load_dotenv
from collections.abc import Mapping


custom_path = os.path.abspath(__file__).replace('constants.py', 'config.yml')
default_path = os.path.abspath(__file__).replace('constants.py', 'default-config.yml')


def env_constructor(loader, node):
    default = None
    load_dotenv()

    if node.id == 'scalar':
        value = loader.construct_scalar(node)
        key = str(value)

    else:
        value = loader.construct_sequence(node)

        if len(value) >= 2:
            key = value[0]
            default = value[1]

        else:
            key = value[0]

    return os.getenv(key, default)

def ensure_settings(default, user):
    for key, value in default.items():
        if key not in user:
            continue

        if isinstance(value, Mapping):
            if not any(isinstance(subvalue, Mapping) for subvalue in value.values()):
                default[key].update(user[key])
            ensure_settings(default[key], user[key])

        else:
            default[key] = user[key]


yaml.SafeLoader.add_constructor("!ENV", env_constructor)
yaml.SafeLoader.add_constructor("!REQUIRED_ENV", env_constructor)


with open(default_path, encoding="UTF-8") as f:
    loaded_config = yaml.safe_load(f)
    f.close()

if Path(custom_path).exists():
    with open(custom_path, encoding="UTF-8") as f:
        customized = yaml.safe_load(f)
        f.close()

    ensure_settings(loaded_config, customized)

print('Loaded Configuration...')


class YAMLGetter(type):
    category = None
    section = None
    subsection = None

    def __getattr__(cls, name):
        name = name.lower()

        try:
            if cls.subsection:
                return loaded_config[cls.category][cls.section][cls.subsection][name]

            elif cls.section:
                return loaded_config[cls.category][cls.section][name]

            else:
                return loaded_config[cls.category][name]

        except KeyError as exception:
            path = '.'.join([getattr(cls, attribute, '[NULL]') for attribute in ['name', 'section', 'subsection']])
            print(f'Unable to Find Configuration name: {path}')

            raise exception

    def __getitem__(cls, name):
        return cls.__getattr__(name)

    def __iter__(cls):
        for name in cls.__annotations__:
            yield name, getattr(cls, name)


class BotConfig(metaclass=YAMLGetter):
    category = "discord"
    section = "bot"

    prefix: str
    token: str

    webhook_name: str
    webhook_icon: str

    developer_ids: List[int]

class FilterConfig(metaclass=YAMLGetter):
    category = "discord"
    section = "filter"

    watchlist: List[str]

    whitelisted_roles: List[str]
    whitelisted_channels: List[str]


class Channels(metaclass=YAMLGetter):
    category = "discord"
    section = "guild"
    subsection = "channels"

    welcome: int
    react_roles: int
    announcements: int

    event_logs: int
    message_logs: int
    moderator_logs: int

    sandbox: int
    mail_inbox: int

    mod_lobby: int
    admin_lobby: int
    staff_alerts: int

    log_channels: List[int]
    staff_channels: List[int]


class Roles(metaclass=YAMLGetter):
    category = "discord"
    section = "guild"
    subsection = "roles"

    muted: int
    blacklisted: int

    verified: int
    announcements: int

    owner: int
    admins: int
    moderators: int

    developer: int

    staff_roles: List[int]
    infraction_roles: List[int]


class Webhooks(metaclass=YAMLGetter):
    category = "discord"
    section = "guild"
    subsection = "webhooks"

    mail_inbox: str

    event_logs: str
    message_logs: str
    moderator_logs: str

    developer_logs: str


class Colors(metaclass=YAMLGetter):
    category = "discord"
    section = "style"
    subsection = "colors"

    soft_red: int
    soft_green: int
    soft_yellow: int
    soft_orange: int


class Emojis(metaclass=YAMLGetter):
    category = "discord"
    section = "style"
    subsection = "emojis"

    pencil: str
    check_mark: str
    cross_mark: str


class Icons(metaclass=YAMLGetter):
    category = "discord"
    section = "style"
    subsection = "icons"

    updated: str

    bulk_delete: str
    message_edit: str
    message_delete: str

    user_mute: str
    user_unmute: str

    user_ban: str
    user_unban: str

    user_warned: str

    user_updated: str
    user_verfied: str

    task_expired: str
    task_submitted: str
    task_completed: str


class WebServer(metaclass=YAMLGetter):
    category = "apis"
    section = "webserver"

    port: int
    address: str

    database: str


class EventConfig(metaclass=YAMLGetter):
    category = "apis"
    section = "events"

    guild_updated: int
    channel_created: int
    channel_updated: int

    message_edited: int
    message_deleted: int
    channel_deleted: int

    user_updated: int
    member_unmuted: int
    member_updated: int
    member_unbanned: int

    member_muted: int
    member_warned: int
    member_kicked: int
    member_banned: int

    aggressive: List[str]


class Boosts(metaclass=YAMLGetter):
    category = "apis"
    section = "leveling"
    subsection = "boosts"

    values: List[int]
    bounds: List[int]

    name = 'Boosts'


class Leagues(metaclass=YAMLGetter):
    category = "apis"
    section = "leveling"
    subsection = "leagues"

    names: List[str]
    bounds: List[int]

    name = 'Leagues'


class Prestiges(metaclass=YAMLGetter):
    category = "apis"
    section = "leveling"
    subsection = "prestiges"

    names: List[str]
    bounds: List[int]

    name = 'Prestiges'

class Levels(metaclass=YAMLGetter):
    category = "apis"
    section = "leveling"
    subsection = "levels"

    base: List[int]
    master: List[int]
    elite: List[int]

    name = 'Levels'
