import os
import pyautogui as pg


HASH_LENGTH_LIMIT = 32  # must be 16/24/32
MAX_NUMBER_TO_GENERATE = 1000000000000
SERVER_PORT = 123
MAXIMUM_PACKET_SIZE = 4096
MAIN_SERVER_ADDRESS = ('192.168.1.20', SERVER_PORT)
DEFAULT_TIMEFRAME_FOR_CONNECTIONS_SCAN = 120  # in seconds
DOS_PREVENTION_MAX_CONNECTION_COUNTER = 20  # max number of connections in <DEFAULT_TIMEFRAME_FOR_CONNECTIONS_SCAN> secs
NUMBER_OF_NODES_TO_OFFER_CLIENT = 3  # number of possibly close nodes to find and offer to client for data allocation
NODE_COMMUNICATION_PORT = 640
SERVER_SOCKET_TIMEOUT = 2.5  # in seconds
CURRENT_PATH = str(os.path.dirname(os.path.abspath(__file__)))
NODE_DATA_STORAGE_PATH = f'{CURRENT_PATH}\\node_implementation\\node_data\\node-storage.txt'
MAX_AVAILABLE_TO_USED_STORAGE_RATIO = 2
NODE_STATUS_UPDATING_CYCLE = 300  # in seconds
STORAGE_COPIES = 3
DELTA_BETWEEN_CONNECTION_HANDLING = 0.1  # in seconds
LOGO_PATH = CURRENT_PATH + '\\OrionDB_transparent_logo.png'
SCREEN_SIZE = pg.size()
INITIAL_STORAGE_SPACE_TARGET = 1000000  # under x bytes of storage space, all nodes are approved
