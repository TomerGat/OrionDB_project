from hash import sha_function
from data_structures import NodeData
from util_functions import generate_random_number
from MainServerSide.final_values import MAX_AVAILABLE_TO_USED_STORAGE_RATIO, INITIAL_STORAGE_SPACE_TARGET


class MainDataDirectory:
    _instance = None

    # create data variables for singleton class
    db_storage_division = {}  # {db id: {collection name: {node id: [item ids]}}}
    database_data = {}  # {db id: {collection name: {item id: item data size}}}
    nodes = {}  # {node id: (node data object, node socket)}
    collection_hashes = {}  # {db id: {collection name: collection hash}}
    node_storage_data = {}  # {node id: {id of stored db: {name of stored collection: count of stored items}}}
    active_nodes = []  # list of currently active node ids
    node_addresses = {}  # {node ip: node id}
    total_storage_space = 0
    total_data_saved = 0
    active_session_tokens = set()
    existing_node_ids = set()
    existing_account_ids = set()
    existing_db_ids = set()
    account_credentials = {}  # {credential string: account id}
    accounts = {}  # {account id: (account object, {db name: db id})}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def count_db_items(self, db_id):
        counter = 0
        for col in self.database_data[db_id].keys():
            counter += len(list(self.database_data[db_id][col].keys()))
        return counter

    def remove_session_token(self, token_to_remove):
        self.active_session_tokens.remove(token_to_remove)

    def update_data_storage_info(self):  # add updating for 'total_storage_space'
        total_data = sum([self.nodes[node_id][0].data_stored for node_id in self.nodes.keys()])
        total_storage = sum([self.nodes[node_id][0].total_storage for node_id in self.nodes.keys()])
        self.total_data_saved = total_data
        self.total_storage_space = total_storage

    def get_new_node_approval(self, requested_space):
        self.update_data_storage_info()
        # check if initial target has been reached
        if self.total_storage_space < INITIAL_STORAGE_SPACE_TARGET:
            return True

        # find maximum amount of memory space that can be extended
        available_memory = self.total_storage_space - self.total_data_saved
        maximum_free_memory = self.total_data_saved * MAX_AVAILABLE_TO_USED_STORAGE_RATIO
        maximum_new_memory = maximum_free_memory - available_memory
        if maximum_new_memory > requested_space:
            return True

        return False

    def update_session_token(self, before, after):
        self.active_session_tokens.remove(before)
        self.active_session_tokens.add(after)

    def remove_node(self, node_id, node_address):
        # update 'nodes'
        del self.nodes[node_id]
        # update 'node_storage_data'
        del self.node_storage_data[node_id]
        # update 'node_addresses
        del self.node_addresses[node_address[0]]
        # remove node id from set
        self.existing_node_ids.remove(node_id)

    def remove_account(self, account_id, credentials):
        # update 'account_credentials'
        del self.account_credentials[credentials]
        # update 'accounts'
        del self.accounts[account_id]
        # remove account id from set
        self.existing_account_ids.remove(account_id)

    def add_node(self, node_address, node_socket, available_storage):
        new_node_data = NodeData(node_address, available_storage)
        new_node_id = self.generate_node_id()
        self.nodes[new_node_id] = (new_node_data, node_socket)
        self.node_addresses[node_address[0]] = new_node_id
        self.node_storage_data[new_node_id] = {}

    def add_account(self, account, connection_string):
        if connection_string in self.account_credentials.keys():
            return False

        if 'account' in connection_string:
            if 'node'.join(connection_string.split('account')) in self.account_credentials.keys():
                return False
        else:
            if 'account'.join(connection_string.split('node')) in self.account_credentials.keys():
                return False

        account_id = self.generate_account_id()
        self.accounts[account_id] = (account, {})
        self.account_credentials[connection_string] = account_id
        return True

    def generate_db_id(self):
        random_num = generate_random_number()
        db_id = sha_function(str(random_num))
        if db_id not in self.existing_db_ids:
            self.existing_db_ids.add(db_id)
            return db_id
        return self.generate_db_id()

    def generate_account_id(self):
        random_num = str(generate_random_number())
        account_id = sha_function(random_num)
        if account_id not in self.existing_account_ids:
            self.existing_account_ids.add(account_id)
            return account_id
        return self.generate_account_id()

    def generate_node_id(self) -> str:
        random_num = str(generate_random_number())
        node_id = sha_function(random_num)
        if node_id not in self.existing_node_ids:
            self.existing_node_ids.add(node_id)
            return node_id
        return self.generate_node_id()

    def generate_session_token(self) -> str:
        random_num = str(generate_random_number())
        token = sha_function(random_num)
        if token not in self.active_session_tokens:
            self.active_session_tokens.add(token)
            return token
        return self.generate_session_token()
