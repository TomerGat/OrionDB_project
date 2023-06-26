import socket
from network_protocol_implementation.request_structure import Packet
from network_protocol_implementation.encrypted_socket import EncryptedSocket
import time
import multiprocessing


server_socket = socket.socket()
server_socket.bind(('127.0.0.1', 123))
server_socket.listen()
print("Server is up and running")
(client_socket, client_address) = server_socket.accept()
print("Client connected")
packet_encoded = client_socket.recv(4096)
packet = Packet(request_encoded=packet_encoded)
print(packet.data)
