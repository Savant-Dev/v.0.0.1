import json
import asyncio

from os.path import exists

from . import config_directory
from ..api import database


class Uploader(database.Connector):
    ''' Updates Database Configurations with a Local File '''

    def __init__(self, name: str):
        self.name = name

        super().__init__('config-installer')

    async def upload(self) -> bool:
        path = config_directory + self.name

        if not os.path.exists(path):
            raise FileNotFoundError(f'Unable to Locate: {path}')

        with open(path, 'r') as f:
            config_file = json.load(f)
            f.close()

        config = json.dumps(config_file)
        query = 'INSERT INTO configs (name, settings) VALUES ($1, $2)'
        args = (self.name, config)

        status = await super().insertone(query, args)

        return status

async def start(name: str):
    module = Uploader(name)
    try:
        status = module.upload()
    except FileNotFoundError as exc:
        print(exc)

    else:
        if status:
            print(f'Uploaded Configuration File {name}')
        else:
            print(f'Failed to Upload Configuration File {name}')
    return

if __name__ == '__main__':
    fp = input('Please Enter the Name of the File you wish to upload: ')
    filename = fp.lower() + '.json'

    asyncio.run(start(filename))
    
