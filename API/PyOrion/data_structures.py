from networks_functions import calculate_ttl


class QueryTypes:  # different types of database queries
    FOR_VALUE_WITH_KEY = 0
    FOR_ITEM_WITH_PAIR = 1


class NodeStatus:
    AVAILABLE = 0
    NO_STORAGE = 1
    TEMPORARILY_OFFLINE = 2


class NetworkMemberTypes:
    MAIN_SERVER = 0
    STORAGE_NODE = 1
    CLIENT = 2


class PacketTypes:
    REQUEST_ADDITIONAL_MEMORY_SPACE = 0  # request to change amount of allocated memory space
    NEW_NODE_CONNECTION = 1
    REQUEST_FOR_NODE_APPROVAL = 2
    DATA_ALLOCATION = 3
    BE_READY_FOR_DATA = 4
    DATA_UPLOAD_REQUEST = 5
    REQUEST_LOWERING_MEMORY_SPACE = 6
    STATUS_UPDATE_REQUEST = 7
    CLIENT_CONNECTION = 8
    CLIENT_REQUESTING_DISCONNECT = 9
    DELETE_DB = 11
    SERVER_REQUESTING_DISCONNECT = 12
    TOKEN_GENERATED = 13
    OPEN_ACCOUNT = 14
    NODE_CONNECTION = 15
    VERIFICATION_ANSWER = 16
    DATA_DOWNLOAD_REQUEST = 17
    DISCONNECT_CONFIRMED_BY_SERVER = 18
    NODE_REQUESTING_DISCONNECT = 19
    NEW_NODE_APPROVAL_REQUEST = 20
    APPROVAL_ANSWER = 21
    DATA_RECEIVED_CONFIRM = 22  # confirmation from client to node / from node to client
    SEND_DATA_FROM_STORAGE = 23
    DATA_DOWNLOAD_FINAL_RESPONSE = 24  # confirmation/complaint to server after download
    REQUESTED_DATA_PACKET = 25
    DATA_UPLOAD_INSTRUCTIONS = 26
    DATA_UPLOAD_FINAL_RESPONSE = 27
    DATA_RELOCATION = 28
    DATA_RELOCATION_INSTRUCTIONS = 29
    DATA_RELOCATION_FINAL_RESPONSE = 30
    WITHDRAW_AS_NODE = 31


class Pipeline:
    def __init__(self):
        self._data = []

    def push(self, obj):
        self._data.append(obj)

    def pop(self):
        obj = self._data.pop(0)
        return obj

    def get_first(self):
        return self._data[0]

    def is_empty(self):
        return len(self._data) == 0

    def load_list_into_pipeline(self, data):
        self._data.extend(data)


class NodeData:  # maybe add server to node ttl in data
    def __init__(self, address, total_storage, status=NodeStatus.AVAILABLE):
        self.total_storage = total_storage
        self.data_stored = 0
        self.address = address
        self.status = status
        self.ttl = calculate_ttl(address[0])
