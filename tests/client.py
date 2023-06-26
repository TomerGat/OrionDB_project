import socket
from network_protocol_implementation.request_structure import Packet
from data_structures import PacketTypes, NetworkMemberTypes
from network_protocol_implementation.encrypted_socket import EncryptedSocket
import time
from util_functions import dict_to_str, str_to_dict


my_socket = socket.socket()
my_socket.connect(('127.0.0.1', 123))
print("Socket connected to server")

data = {
    'key1': True,
    'dict': {'first': 1, 2: None}
}
print(dict_to_str(data))
print(str_to_dict(dict_to_str(data)))
packet = Packet(request_type=PacketTypes.DATA_ALLOCATION, sender_type=NetworkMemberTypes.CLIENT, data=data)
my_socket.send(packet.encode())
