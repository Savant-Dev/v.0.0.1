import socket

from typing import Any, Optional, Tuple
from ..constants import WebServer

# Configure Database Server
access_port = WebServer.port
network_address = WebServer.address


class ServerPing():
    ''' Pings the Database Server to ensure Connection '''

    @classmethod
    def start(cls, log: Any) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            try:
                sock.connect((network_address, access_port))
                status = True
            except socket.timeout:
                log.critical('database', f'Server Failed to Respond - {network_address}/{access_port}')
                status = False
            except socket.error:
                log.critical('database', f'Server ({network_address}/{access_port}) is Offline')
                status = False
            else:
                log.trace('database', f'Connection Established ({network_address}/{access_port})')

            sock.close()

        return status



class ConfigurationError(Exception):
    def __init__(self, reason: Optional[str]):
        self.reason = reason
    def __str__(self):
        return getattr(self, 'reason', 'Unable to Locate Configuration File')
