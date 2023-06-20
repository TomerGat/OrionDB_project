from client_implementation.orionclient import OrionClient
from node_implementation.network_node import NetworkNode


class UserData:
    _instance = None

    # class data
    account_type = None  # node/client
    connector = None  # OrionClient / NetworkNode instance
    redirected_flag = False
    response_string = ''
    username = None
    password = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def initialize_connector(self, connection_string):
        confirm = True
        try:
            ac_type = connection_string.split('//')[0].split('.')[1]
            if ac_type == 'account':
                self.connector = OrionClient(connection_string)
            else:
                self.connector = NetworkNode(connection_string)
            if not self.connector.connected:
                confirm = False
        except Exception as e:
            print(e)
            self.response_string = 'Invalid login credentials. Please try again.'
            confirm = False
        return confirm


def generate_string(username, password, ac_type):
    return f'oriondb.{ac_type}//{username}={password}'
