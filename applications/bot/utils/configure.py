import json

from typing import Optional, Union

from ...api import database


class ConfigWizard(database.Connector):
    ''' Grabs the Configuration for a specified package '''

    def __init__(self, name: str):
        self.name = name

        super().__init__('discord-bot', None)

    @staticmethod
    def is_valid(encoded: str) -> bool:
        try:
            json.loads(encoded)
        except ValueError:
            return False

        return True

    @classmethod
    def ensure_encoding(cls, config: Union[str, dict]) -> str:
        if isinstance(config, dict):
            return json.dumps(config)

        elif isinstance(config, str):
            if self.is_valid(config):
                return config
            else:
                raise ValueError('Improperly Constructed JSON string')

        else:
            raise TypeError('New Configuration must be either encoded JSON string or dictionary')

    @classmethod
    async def detect_changes(cls, before: Optional[dict], after: dict) -> list:

        def fresh_config(key: str) -> dict:
            change = {
                "attribute": key,
                "before": "Not Set",
                "after": after[key]
            }

            return change

        def compare_values(key: str) -> dict:
            change = {
                "attribute": key,
                "after": after[key],
                "before": before[key]
            }

            return change

        if not before:
            return [fresh_config(key) for key in after]

        return [compare_values(key) for key in after if after[key] != before[key]]


    async def fetch_config(self) -> Optional[dict]:
        query = 'SELECT settings FROM configs WHERE name = $1'
        args = (self.name, )

        result = await super().fetchone(query, args)

        if result:
            config = json.loads(result['settings'])
            return config

        return None

    async def update_config(self, new: Union[dict, str]) -> bool:
        statement = 'UPDATE configs SET settings = $1 WHERE name = $2'

        try:
            config = self.ensure_encoding(new)

        except ValueError as e:
            raise e
        except TypeError as e:
            raise e

        else:
            args = (config, self.name)
            return await super().executeone(statement, args)
