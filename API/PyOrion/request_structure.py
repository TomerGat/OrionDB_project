from PyOrion.util_functions import str_to_dict, dict_to_str

"""
client to server request types:
1. query - client requesting the main_server to tell nodes to send data
2. data upload - client wants to upload data, requests info about nodes to which client can send data
3. join network - new client wants to join network to be able to access data on it / upload to it
4. node status update - node availability or connectivity status changes and updates

server to node request types:
1. send data - server is requesting node to send data to a client/other node
2. receive - server is instructing node to be ready to receive data from client/other node
3. update status - requesting node to update on availability or connectivity status

client/node to node request types:
1. take data - node is sending you data, be in receive mode
"""


# generic object to send over network for all types of network traffic
class Packet:
    def __init__(self, request_encoded=None, request_type=None, sender_type=None, data=None, token=None):
        self.request_type = request_type
        self.sender_type = sender_type
        self.data = data
        self.token = token
        if request_encoded is not None:
            self.decode(request_encoded)

    def encode(self):
        packet_str = ';'.join([str(self.request_type),
                               str(self.sender_type),
                               str(None) if self.data is None else dict_to_str(self.data),
                               str(self.token)])
        encoded_packet = packet_str.encode()
        return encoded_packet

    def decode(self, packet_encoded):
        packet_str = packet_encoded.decode()
        packet_data = packet_str.split(';')
        self.request_type = None if packet_data[0] == str(None) else int(packet_data[0])
        self.sender_type = None if packet_data[1] == str(None) else int(packet_data[1])
        self.data = None if packet_data[2] == str(None) else str_to_dict(packet_data[2])
        self.token = None if packet_data[3] == str(None) else packet_data[3]
