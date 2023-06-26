from util_functions import validate_string
from hash import hash_function
from main_server_implementation.main_data_directory import MainDataDirectory


class NodeAccount:
    def __init__(self, username, password):
        valid = validate_string(username) and validate_string(password)
        if not valid:
            raise Exception('Invalid credentials')
        self.username = username
        self.password = hash_function(password)
        connection_string = password.join(self.generate_empty_connection_string().split('<password>'))
        confirm = MainDataDirectory().add_account(self, connection_string)
        if not confirm:
            raise Exception('Account credentials already assigned')

    def generate_empty_connection_string(self):
        string = f'oriondb.node//{self.username}=<password>'
        return string


class ClientAccount:
    def __init__(self, username, password):
        valid = validate_string(username) and validate_string(password)
        if not valid:
            raise Exception('Invalid credentials')
        self.username = username
        self.password = hash_function(password)
        self.databases_owned = {}  # {db name: db id}
        # add account data to main data director
        connection_string = password.join(self.generate_empty_connection_string().split('<password>'))
        confirm = MainDataDirectory().add_account(self, connection_string)
        if not confirm:
            raise Exception('Account credentials already assigned')

    def generate_empty_connection_string(self):
        connection_string = f'oriondb.account//{self.username}=<password>'
        return connection_string
