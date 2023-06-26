from network_protocol_implementation.encrypted_socket import EncryptedSocket
from userside_final_values import MAIN_SERVER_ADDRESS, NODE_COMMUNICATION_PORT
from network_protocol_implementation.request_structure import Packet
from hash import sha_function
from data_structures import PacketTypes, NetworkMemberTypes
import socket
from node_storage import NodeStorage
from general_system_functions import get_node_approval, request_additional_storage_space, initial_server_connect
import threading
from util_functions import get_key_for_lowest_value


class NetworkNode:
    def __init__(self, credentials):
        # Create an encrypted socket connection to the server
        self.server_socket = EncryptedSocket()
        # save credentials for later use
        self.credentials = credentials
        # flag to continue/stop running of node server
        self.connected = True
        # send connection request to main server
        self.server_socket.connect(MAIN_SERVER_ADDRESS)
        # receive session token from server
        packet = Packet(request_encoded=self.server_socket.recv())
        token = packet.token
        true_token = str(sha_function(token))
        self.session_token = true_token
        # send identification packet
        packet = Packet(request_type=PacketTypes.NODE_CONNECTION, sender_type=NetworkMemberTypes.STORAGE_NODE,
                        token=self.session_token, data={'credentials': credentials})
        self.server_socket.send(packet.encode())
        # receive answer from server for identification and token verification
        packet = Packet(request_encoded=self.server_socket.recv())
        answer = packet.data['answer']
        if not answer:
            self.connected = False
            self.server_socket.close()
            return
        self.node_id = packet.data['node id']
        # create a node storage instance
        self.storage = NodeStorage(self.node_id)
        # create p2p socket to send/receive data to/from other nodes/clients
        self.p2p_socket = EncryptedSocket()
        # open thread to listen to server
        listen_thread = threading.Thread(target=self.listen_from_server)
        listen_thread.start()

    def listen_from_server(self):
        # listen for connections (only from main server)
        # node server socket is only activated when prompted by main server
        self.server_socket.settimeout(0.5)
        while self.connected:
            try:
                packet = Packet(request_encoded=self.server_socket.recv())
                # check session token
                if packet.token != self.session_token:
                    continue  # Server communication was invalid

                # handle different request types from server
                if packet.request_type == PacketTypes.SEND_DATA_FROM_STORAGE:
                    self._handle_data_transfer(packet)

                elif packet.request_type == PacketTypes.BE_READY_FOR_DATA:
                    self._handle_data_allocation(packet)

                elif packet.request_type == PacketTypes.DELETE_DB:
                    self._delete_db(packet)

                elif packet.request_type == PacketTypes.STATUS_UPDATE_REQUEST:
                    self.server_socket.send(Packet().encode())

            except socket.timeout:
                continue
            except Exception as e:
                print(f'Exception "{e}" for connection with server.')
                return

    def _handle_data_allocation(self, packet):
        source_ip = packet.data['ip address']
        db_id = packet.data['db id']
        self.p2p_socket.bind((socket.gethostbyname(socket.gethostname()), NODE_COMMUNICATION_PORT))
        self.p2p_socket.listen()
        client_address = (None, None)
        client_socket = None
        while client_address[0] != source_ip:
            client_socket, client_address = self.p2p_socket.accept()

        if client_socket is None:
            self.p2p_socket.close()
            self.p2p_socket = EncryptedSocket()
            return

        # receive data from client and add to node storage
        packet = Packet(request_encoded=client_socket.recv(receive_all_data=True))
        db_data = packet.data  # {collection name: {item id: item data}}
        for col_name in db_data.keys():
            self.storage.delete_collection(db_id, col_name)
            if len(list(db_data[col_name].keys())) != 0:  # check if collection is empty (was deleted by user)
                self.storage.insert_data(db_id, col_name, list(db_data[col_name].values()))

        # send confirmation to client
        packet = Packet(request_type=PacketTypes.DATA_RECEIVED_CONFIRM, sender_type=NetworkMemberTypes.STORAGE_NODE, token=self.node_id)
        client_socket.send(packet.encode())

        # reset p2p socket and close client socket
        client_socket.close()
        self.p2p_socket.close()
        self.p2p_socket = EncryptedSocket()

    def _delete_db(self, packet):
        # get necessary data
        db_id = packet.data['db id']
        token = packet.token

        # respond to server and confirm
        confirm = (token == self.session_token)
        packet = Packet(data={'answer': confirm})
        self.server_socket.send(packet.encode())

        if not confirm:
            return

        # delete db
        self.storage.delete_database(db_id)

    def _handle_data_transfer(self, packet):
        db_id = packet.data['db id']
        target_ip = packet.data['target']

        # connect to client, get requested data, send data to client
        self.p2p_socket.connect((target_ip, NODE_COMMUNICATION_PORT))
        data = self.storage.get_db_data(db_id)
        packet = Packet(request_type=PacketTypes.REQUESTED_DATA_PACKET, sender_type=NetworkMemberTypes.STORAGE_NODE,
                        data=data, token=self.node_id)
        self.p2p_socket.send(packet.encode())

        # receive confirmation from client/other node
        _ = Packet(request_encoded=self.p2p_socket.recv())

        # reset p2p socket
        self.p2p_socket.close()
        self.p2p_socket = EncryptedSocket()

    def request_additional_memory_allocation(self, data_size):
        # get approval for data allocation
        confirmation, confirmation_code = get_node_approval(data_size)
        if not confirmation:
            raise Exception('Additional storage allocation not approved')

        # call general system function to get additional space
        final_confirmation = request_additional_storage_space(data_size, self.node_id, confirmation_code)

        # return confirmation
        return final_confirmation

    def relocate_data(self, db_id):
        # connect to server
        temp_socket, true_token = initial_server_connect()

        # send db information to server
        db_info = self.storage.get_db_details(db_id)
        packet = Packet(request_type=PacketTypes.DATA_RELOCATION, sender_type=NetworkMemberTypes.STORAGE_NODE,
                        data={'db info': db_info, 'db id': db_id, 'node id': self.node_id, 'credentials': self.credentials},
                        token=true_token)
        temp_socket.send(packet.encode())

        # receive data on target node and send data
        packet = Packet(request_type=temp_socket.recv())
        if packet.token != true_token:
            raise Exception('Invalid server communication, please try again later.')

        target_node_ip = packet.data['target node ip']
        target_node_id = packet.data['target node id']
        self.p2p_socket.connect((target_node_ip, NODE_COMMUNICATION_PORT))
        db_data = self.storage.get_db_data(db_id)  # {collection: {item id: item data}}
        packet = Packet(request_type=PacketTypes.DATA_ALLOCATION, sender_type=NetworkMemberTypes.STORAGE_NODE,
                        data=db_data, token=target_node_id)
        self.p2p_socket.send(packet.encode())

        # receive confirmation from target node
        # receive confirmation from node
        self.p2p_socket.settimeout(2)
        confirm = True
        try:
            _ = Packet(request_encoded=self.p2p_socket.recv())
        except socket.timeout:
            confirm = False

        # send confirmation to server
        packet = Packet(request_type=PacketTypes.DATA_RELOCATION_FINAL_RESPONSE, sender_type=NetworkMemberTypes.STORAGE_NODE,
                        data={'answer': confirm})
        self.server_socket.send(packet.encode())

        # reset p2p socket
        self.p2p_socket.close()
        self.p2p_socket = EncryptedSocket()

        # if confirmed, delete data from storage
        if confirm:
            pass

    def lower_allocated_memory_space(self, memory_to_free):
        # find dbs to relocate in order to lower memory space as requested
        stored_dbs = {}  # {db id: db data size}
        for db_id in self.storage.list_stored_db_ids():
            stored_dbs[db_id] = self.storage.get_db_data_size(db_id)

        # add smallest dbs until enough memory is freed
        data_size_to_relocate = 0
        db_ids_to_relocate = []
        while data_size_to_relocate < memory_to_free:
            db_id = get_key_for_lowest_value(stored_dbs)
            db_ids_to_relocate.append(db_id)
            data_size_to_relocate += stored_dbs[db_id]

        for db_id in db_ids_to_relocate:
            self.relocate_data(db_id)

        # send notification to server about lowering total memory space
        packet = Packet(PacketTypes.REQUEST_LOWERING_MEMORY_SPACE, sender_type=NetworkMemberTypes.STORAGE_NODE,
                        data={'memory to free': memory_to_free}, token=self.session_token)
        self.server_socket.send(packet.encode())

    def withdraw_as_node(self, credentials):
        # start by relocating all data
        stored_db_ids = self.storage.list_stored_db_ids()
        for db_id in stored_db_ids:
            self.relocate_data(db_id)

        # notify server about node_withdrawal
        packet = Packet(request_type=PacketTypes.WITHDRAW_AS_NODE, sender_type=NetworkMemberTypes.STORAGE_NODE,
                        data={'credentials': credentials, 'node id': self.node_id}, token=self.session_token)
        self.server_socket.send(packet.encode())

        # delete storage txt file
        self.storage.delete_storage()

        # disconnect
        self.disconnect()

    def disconnect(self):
        # send disconnect packet
        packet = Packet(request_type=PacketTypes.NODE_REQUESTING_DISCONNECT, sender_type=NetworkMemberTypes.STORAGE_NODE,
                        token=self.session_token)
        self.server_socket.send(packet.encode())

        # receive confirmation packet
        packet = Packet(request_encoded=self.server_socket.recv())
        if packet.request_type == PacketTypes.DISCONNECT_CONFIRMED_BY_SERVER:
            self.connected = False
            self.server_socket.close()
            return
        else:
            self.connected = False
            self.server_socket.close()
            raise Exception('System Error!')

    def __del__(self):
        if self.connected:
            self.disconnect()
