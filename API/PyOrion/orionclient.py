from encrypted_socket import EncryptedSocket
from final_values import MAIN_SERVER_ADDRESS, NODE_COMMUNICATION_PORT, STORAGE_COPIES
from request_structure import Packet
from hash import sha_function
from data_structures import NetworkMemberTypes, PacketTypes
from database import DB
import os
from networks_functions import calculate_ttl
from util_functions import get_key_for_highest_value
import socket


class OrionClient:
    def __init__(self, credentials):
        # create data structure to hold account databases
        self.account_dbs = {}  # {db name: db id}

        # setup for flags and other variables
        self.cache = {}  # cache databases that are downloaded {db name: db object}
        self.connected = True

        # create data structure to hold initialized local databases and downloaded databases
        self.local_dbs = {}  # {db name: db object}

        # Create an encrypted socket to connect to the p2p network
        self.p2p_socket = EncryptedSocket()

        # Create an encrypted socket connection to the server
        self.server_socket = EncryptedSocket()

        # send connection request to main server
        self.server_socket.connect(MAIN_SERVER_ADDRESS)

        # receive session token from server
        packet = Packet(request_encoded=self.server_socket.recv())
        token = packet.token
        true_token = str(sha_function(token))
        self.session_token = true_token

        # send identification packet
        packet = Packet(request_type=PacketTypes.CLIENT_CONNECTION, sender_type=NetworkMemberTypes.CLIENT,
                        token=self.session_token, data={'credentials': credentials})
        self.server_socket.send(packet.encode())

        # receive answer from server for identification and token verification
        packet = Packet(request_encoded=self.server_socket.recv())
        answer = packet.data['answer']
        self.account_dbs = packet.data['account dbs'] if packet.data['account dbs'] is not None else {}
        if not answer:
            self.server_socket.close()
            self.connected = False
            raise Exception('Credentials invalid')
        if packet.token != self.session_token:
            self.disconnect()

    def __getitem__(self, db_name):  # download db to client, get from cache, or create local db
        if db_name not in self.account_dbs:
            if db_name in self.local_dbs.keys():
                db = self.local_dbs[db_name]
            else:
                db = DB(db_name)
                self.local_dbs[db_name] = db
            return db
        if db_name in self.cache.keys():
            return self.cache[db_name]
        db = self._download_data(db_name, self.account_dbs[db_name])
        return db

    def __delitem__(self, db_name):
        db_id = None
        # if db is local, delete it
        if db_name in self.local_dbs.keys():
            del self.local_dbs[db_name]
            return
        elif db_name in self.account_dbs.keys():
            db_id = self.account_dbs[db_name]
        else:
            raise Exception('Database "{}" not found.'.format(db_name))

        # send request to server
        packet = Packet(request_type=PacketTypes.DELETE_DB, sender_type=NetworkMemberTypes.CLIENT, data={'db id': db_id},
                        token=self.session_token)
        self.server_socket.send(packet.encode())

    def update_system_data(self):  # update all data (call upload data function for every local/account db)
        db_names = list(self.local_dbs.keys())
        db_names.extend(list(self.cache.keys()))
        for db_name in db_names:
            self.upload_data(db_name)

    def upload_data(self, db_name, _second_attempt=False):  # upload an updated database to the system
        # get db data
        if db_name in self.cache.keys():
            db = self.cache[db_name]
        elif db_name in self.local_dbs.keys():
            db = self.local_dbs[db_name]
        else:
            raise Exception('Database "{}" does not exist locally.'.format(db_name))
        db_info = db.get_db_details()  # {collection name: {items: item data size}}

        # create final dict with all necessary data for upload request
        db_id = self.account_dbs[db_name] if db_name in self.account_dbs.keys() else None
        data = {'db name': db_name, 'db id': db_id, 'db data': db_info}
        # add Merkle tree representation for each collection
        collection_hashes = dict(
            zip(db.list_collections(), [collection.generate_merkle_tree() for collection in db.collections.values()]))
        data['collection hashes'] = collection_hashes

        # send db info to server with upload request
        packet = Packet(request_type=PacketTypes.DATA_UPLOAD_REQUEST, sender_type=NetworkMemberTypes.CLIENT,
                        data=data, token=self.session_token)
        self.server_socket.send(packet.encode())

        # get response from server (also check if response is server requesting disconnect)
        packet = Packet(request_encoded=self.server_socket.recv(receive_all_data=True))
        if packet.request_type == PacketTypes.SERVER_REQUESTING_DISCONNECT:
            self.server_socket.close()
            self.p2p_socket.close()
            self.connected = False
            return

        # continue with upload process - find best nodes out of list sent from server
        db_id = packet.data['db id']  # get db id in case db was new upload
        initial_best_target_nodes = packet.data['nodes']  # {node id: node ip address}

        if len(list(initial_best_target_nodes.keys())) == 0:
            raise Exception('Insufficient storage space for upload')

        best_target_nodes = {}  # {node id: node ip address}
        if len(initial_best_target_nodes) > STORAGE_COPIES:
            ttl_per_node = {}  # {node id: ttl}
            for node_id in initial_best_target_nodes.keys():
                ttl = calculate_ttl(initial_best_target_nodes[node_id])
                ttl_per_node[node_id] = ttl

            # select best nodes according to ttl data
            initial_best_target_nodes_temp = initial_best_target_nodes
            for _ in range(STORAGE_COPIES):
                key = get_key_for_highest_value(initial_best_target_nodes)
                best_target_nodes[key] = initial_best_target_nodes[key]
                del initial_best_target_nodes_temp[key]

        # send selected nodes to server
        packet = Packet(request_type=PacketTypes.DATA_UPLOAD_INSTRUCTIONS, sender_type=NetworkMemberTypes.CLIENT,
                        data={'nodes': best_target_nodes}, token=self.session_token)
        self.server_socket.send(packet.encode())

        # wait for server to send start instruction
        packet = Packet(request_encoded=self.server_socket.recv())
        if packet.token != self.session_token:
            raise Exception('Invalid authentication from server, please try again later.')
        if packet.request_type == PacketTypes.DISCONNECT_CONFIRMED_BY_SERVER:
            self.server_socket.close()
            self.p2p_socket.close()
            self.connected = False
            return

        # send a copy of data to each node and receive confirmation from each
        confirmed_transfers = dict(
            zip(
                list(best_target_nodes.keys()),
                [False for _ in range(len(list(best_target_nodes.keys())))]
            )
        )
        db_data = db.to_dict()  # {collection name: {item id: item data}}
        # isolate only collections that were requested by server
        updated_collections = packet.data['updated items']
        new_db_data = {}  # {collection name: {item id: item data}}
        for col_name in updated_collections:
            if col_name in db_data:
                new_db_data[col_name] = db_data[col_name]
            else:
                new_db_data[col_name] = {}

        for node_id, node_address in best_target_nodes.items():
            self.p2p_socket.connect((node_address, NODE_COMMUNICATION_PORT))
            # change db into dictionary format and send to node
            packet = Packet(request_type=PacketTypes.DATA_ALLOCATION, sender_type=NetworkMemberTypes.CLIENT,
                            data=new_db_data, token=node_id)
            self.p2p_socket.send(packet.encode())

            # receive confirmation from node
            self.p2p_socket.settimeout(2)
            confirm = True
            try:
                _ = Packet(request_encoded=self.p2p_socket.recv())
            except socket.timeout:
                confirm = False
            confirmed_transfers[node_id] = confirm

        # send confirmation to server
        final_confirmation = True
        if False in confirmed_transfers.values():
            final_confirmation = False
        packet = Packet(request_type=PacketTypes.DATA_UPLOAD_FINAL_RESPONSE, sender_type=NetworkMemberTypes.CLIENT,
                        data={'answer': final_confirmation}, token=self.session_token)
        self.server_socket.send(packet.encode())

        # reset p2p socket
        self.p2p_socket.close()
        self.p2p_socket = EncryptedSocket()

        # if process was not confirmed, rerun (once, then display system error)
        if not final_confirmation:
            if not _second_attempt:
                self.upload_data(db_name, _second_attempt=True)
            else:
                raise Exception('System Error! Insufficient active nodes, please try again later.')

        # update client data
        self.account_dbs[db_name] = db_id
        if db_id in self.local_dbs:
            del self.local_dbs[db_id]
            self.cache[db_name] = db

    def _download_data(self, db_name, db_id, send_request_packet=True):
        if send_request_packet:
            # send request for data
            packet = Packet(request_type=PacketTypes.DATA_DOWNLOAD_REQUEST, sender_type=NetworkMemberTypes.CLIENT,
                            token=self.session_token, data={'db name': db_name, 'db id': db_id})
            self.server_socket.send(packet.encode())

        # get data on addresses to listen to from server
        packet = Packet(request_encoded=self.server_socket.recv())
        if packet.token != self.session_token:
            raise Exception('Invalid authentication from server, please try again later.')
        if packet.request_type == PacketTypes.DISCONNECT_CONFIRMED_BY_SERVER:
            self.server_socket.close()
            self.p2p_socket.close()
            self.connected = False
            return

        source_whitelist = packet.data['whitelist']

        # receive all data
        all_data_received = False
        self.p2p_socket.bind((str(os.path.dirname(os.path.abspath(__file__))), NODE_COMMUNICATION_PORT))
        self.p2p_socket.listen()
        received_db = DB(db_name)
        while not all_data_received:
            node_socket, node_address = self.p2p_socket.accept()

            # verify source address and receive packet
            if node_address[0] not in source_whitelist.keys():
                continue
            packet = Packet(request_encoded=node_socket.recv(receive_all_data=True))

            # verify source with node id (added to packet as token)
            node_id = packet.token
            if node_id != source_whitelist[node_address[0]]:
                continue

            # delete current source from source list
            del source_whitelist[node_address[0]]

            # after source verification, add data from source node to new local DB
            db_data = packet.data  # {collection name: {item id: item data}
            for collection_name in db_data.keys():
                if collection_name not in received_db.collections.keys():
                    received_db.create_collection(collection_name)
                received_db[collection_name].insert_items(list(db_data[collection_name].values()))

            # send confirmation to node
            packet = Packet(request_type=PacketTypes.DATA_RECEIVED_CONFIRM, sender_type=NetworkMemberTypes.CLIENT,
                            token=node_id)  # use node id to verify source
            node_socket.send(packet.encode())

            # check if there are remaining sources
            if len(list(source_whitelist.keys())) == 0:
                all_data_received = True

        # check if data is missing according to item count from server. if items are missing, send complaint packet to server
        # in issue case, server tells all relevant storage nodes to send data, this function is called again with send_request_packet as False
        # if there is an issue and send_request_packet is False, raise Exception (node is probably not currently active, should not happen)

        data_download_confirmation = True
        item_counter = received_db.get_item_count()
        if item_counter != packet.data['item count']:
            data_download_confirmation = False

        # send confirmation to server
        packet = Packet(request_type=PacketTypes.DATA_DOWNLOAD_FINAL_RESPONSE, sender_type=NetworkMemberTypes.CLIENT,
                        data={'answer': data_download_confirmation}, token=self.session_token)
        self.server_socket.send(packet.encode())

        if not data_download_confirmation:
            if send_request_packet:
                self._download_data(db_name, db_id, send_request_packet=False)
            else:
                raise Exception('System Error! Insufficient active nodes, please try again later.')

        # add db to cache, reset p2p socket, return db
        self.cache[db_name] = received_db
        self.p2p_socket = EncryptedSocket()
        return received_db

    def disconnect(self):  # send a disconnect request, receive confirmation for disconnect from server, close socket
        # set connected flag to False
        self.connected = False

        # send disconnect packet
        packet = Packet(request_type=PacketTypes.CLIENT_REQUESTING_DISCONNECT, sender_type=NetworkMemberTypes.CLIENT,
                        token=self.session_token)
        self.server_socket.send(packet.encode())

        # receive confirmation packet
        packet = Packet(request_encoded=self.server_socket.recv())
        if packet.request_type == PacketTypes.DISCONNECT_CONFIRMED_BY_SERVER:
            self.server_socket.close()
            return
        else:
            self.server_socket.close()
            raise Exception('System Error!')

    def __del__(self):
        if self.connected:
            self.disconnect()
