from final_values import SERVER_PORT, DOS_PREVENTION_MAX_CONNECTION_COUNTER, SERVER_SOCKET_TIMEOUT, \
    NODE_STATUS_UPDATING_CYCLE, DELTA_BETWEEN_CONNECTION_HANDLING
import socket
import threading
from main_server_implementation.main_data_directory import MainDataDirectory
from data_structures import Pipeline, PacketTypes, NetworkMemberTypes, NodeStatus
from network_protocol_implementation.request_structure import Packet
from hash import sha_function
from network_protocol_implementation.encrypted_socket import EncryptedSocket
from account import ClientAccount, NodeAccount
from network_protocol_implementation.connection_log import ConnectionLog
from algo import find_nodes_with_database, get_closest_available_nodes
from network_protocol_implementation.networks_functions import calculate_ttl
import time
import random
from util_functions import check_credentials_format, generate_random_number

"""
make sure that all data is added to MainDataDirectory() when adding/removing new nodes/accounts
"""


class OrionMainServer:
    _instance = None  # define empty instance variable to contain single instance of class after first initialization

    # create data variables for singleton class
    address = (socket.gethostbyname(socket.gethostname()), SERVER_PORT)
    server_socket = EncryptedSocket()
    run = None
    pipeline = Pipeline()  # request pipeline
    connection_logs = {}  # {client address: connection log}
    flag = {}  # {client address: run/stop server flag}
    connected_sockets = []  # list of currently connected sockets
    node_session_tokens = {}  # {node address: session token}
    approval_codes = set()  # set of approval codes
    node_packet_queue = {}  # {node id: list of packets that could not be sent because node was offline}

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start_server(self):
        if self.run:
            raise Exception('Server already starting')
        self.run = True
        print('OrionDB main server running at {}:{}'.format(*self.address))
        self.server_socket.bind(self.address)
        self.server_socket.listen()
        self.server_socket.settimeout(SERVER_SOCKET_TIMEOUT)
        receive_connections_thread = threading.Thread(target=self.receive_connections)
        receive_connections_thread.start()
        pipeline_handling_thread = threading.Thread(target=self.handle_pipeline)
        pipeline_handling_thread.start()
        status_updating_thread = threading.Thread(target=self.handle_node_status_updates)
        status_updating_thread.start()

    def receive_connections(self):
        while self.run:
            time.sleep(DELTA_BETWEEN_CONNECTION_HANDLING)
            try:
                client_socket, client_address = self.server_socket.accept()
                print('\nNew connection from {}'.format(client_address))

                # add connection to connection log
                if client_address not in self.connection_logs.keys():
                    self.connection_logs[client_address] = ConnectionLog()
                self.connection_logs[client_address].add_connection()

                # check number of connections in last x seconds to prevent dos attacks
                connection_counter = self.connection_logs[client_address].count_recent_connections()
                if connection_counter > DOS_PREVENTION_MAX_CONNECTION_COUNTER:
                    client_socket.close()
                    print('Connection from {} closed'.format(client_address))
                else:
                    self.flag[client_address] = True
                    connection_thread = threading.Thread(target=self.handle_client,
                                                         args=(client_socket, client_address))
                    connection_thread.start()
                    self.connected_sockets.append(client_socket)
            except socket.timeout:
                continue
            except Exception as e:
                print(f'Exception "{e}" while receiving connections')

    def handle_client(self, client_socket, client_address):  # function receives packets from client and adds them to pipeline
        # start by creating session token and exchanging with client:
        token = MainDataDirectory().generate_session_token()
        true_token = sha_function(token)
        MainDataDirectory().update_session_token(token, true_token)
        packet = Packet(request_type=PacketTypes.TOKEN_GENERATED, sender_type=NetworkMemberTypes.MAIN_SERVER,
                        token=token)
        client_socket.send(packet.encode())

        # receive initial identification packet with credentials
        packet_encoded = client_socket.recv()
        packet = Packet(request_encoded=packet_encoded)
        credentials = packet.data[
            'credentials']  # credentials - username, password if creating account / connection string if connecting to account/node
        account = None
        account_id = None
        node_id = None
        account_dbs = None

        # check session token
        correct_token = (packet.token == true_token)

        # check for pre-verification requests (for actions that cannot be done from within a client instance)
        # check if packet is an approval request
        if packet.request_type == PacketTypes.NEW_NODE_APPROVAL_REQUEST:
            requested_data_size = packet.data['requested space']
            approval = MainDataDirectory().get_new_node_approval(int(requested_data_size))
            # create and save approval code (to later prove approval for node creation)
            confirmation_code = sha_function(str(generate_random_number()))
            self.approval_codes.add(confirmation_code)
            # send back response
            if not approval:
                confirmation_code = 0
            packet = Packet(request_type=PacketTypes.APPROVAL_ANSWER, sender_type=NetworkMemberTypes.MAIN_SERVER,
                            data={'answer': approval, 'confirmation code': confirmation_code}, token=true_token)
            client_socket.send(packet.encode())
            # disconnect after responding to approval
            MainDataDirectory().remove_session_token(true_token)
            del self.flag[client_address]
            self.connected_sockets.remove(client_socket)
            client_socket.close()
            print('Connection from {} closed'.format(client_address))
            return

        # check if packet is a memory allocation request
        elif packet.request_type == PacketTypes.REQUEST_ADDITIONAL_MEMORY_SPACE:
            requested_data_size = packet.data['requested space']
            node_id_temp = packet.data['node id']
            approval_code = packet.data['confirmation code']
            answer = approval_code in self.approval_codes
            if approval_code in self.approval_codes:
                self.approval_codes.remove(approval_code)
            # if request approved, add memory space to MDD
            if answer:
                MainDataDirectory().nodes[node_id_temp][0].total_storage += requested_data_size
            # send back response
            packet = Packet(request_type=PacketTypes.APPROVAL_ANSWER, sender_type=NetworkMemberTypes.MAIN_SERVER,
                            data={'answer': answer}, token=true_token)
            client_socket.send(packet.encode())
            # disconnect after responding to approval
            MainDataDirectory().remove_session_token(true_token)
            del self.flag[client_address]
            self.connected_sockets.remove(client_socket)
            client_socket.close()
            print('Connection from {} closed'.format(client_address))
            return

        # check if packet is a new account/node
        if packet.request_type == PacketTypes.OPEN_ACCOUNT or packet.request_type == PacketTypes.NEW_NODE_CONNECTION:
            confirm = True
            if packet.request_type == PacketTypes.OPEN_ACCOUNT:
                try:
                    ClientAccount(credentials['username'], credentials['password'])
                except Exception as _:
                    confirm = False
            elif packet.request_type == PacketTypes.NEW_NODE_CONNECTION:
                confirmation_code = packet.data['confirmation code']
                if confirmation_code in self.approval_codes:
                    NodeAccount(credentials['username'], credentials['password'])
                    storage = packet.data['available storage']
                    MainDataDirectory().add_node(client_address, client_socket, storage)
                    self.approval_codes.remove(confirmation_code)
                else:
                    confirm = False

            # send response
            packet = Packet(data={'answer': confirm}, token=true_token)
            client_socket.send(packet.encode())

            # disconnect client and remove session token
            MainDataDirectory().remove_session_token(true_token)
            del self.flag[client_address]
            if client_address in self.node_session_tokens:
                del self.node_session_tokens[client_address]
            self.connected_sockets.remove(client_socket)
            client_socket.close()
            print('\nConnection from {} closed'.format(client_address))
            return

        else:
            # verify account credentials
            # check connection string format
            valid_credentials = check_credentials_format(credentials)
            if not valid_credentials:
                confirm = False
            else:
                confirm = True
                if packet.sender_type == NetworkMemberTypes.CLIENT:
                    # verification for clients
                    try:
                        account_type = credentials.split('//')[0].split('.')[1]
                        if account_type != 'account':
                            confirm = False
                        else:
                            account_id = MainDataDirectory().account_credentials[credentials]
                            account = MainDataDirectory().accounts[account_id][0]
                            # get all databases owned by account
                            databases_owned = account.databases_owned
                            account_dbs = {}  # {db name: db id}
                            for db_name in databases_owned:
                                account_dbs[db_name] = databases_owned[db_name][0]
                    except KeyError:
                        confirm = False
                        print('Incorrect credentials for connection from address: {}'.format(client_address))
                    except Exception as e:
                        print(f'Exception {e} while verifying account')
                        confirm = False
                elif packet.sender_type == NetworkMemberTypes.STORAGE_NODE:
                    # verification for nodes
                    try:
                        account_type = credentials.split('//')[0].split('.')[1]
                        if account_type != 'node':
                            confirm = False
                        else:
                            account_id = MainDataDirectory().account_credentials[credentials]
                            confirm = (credentials in MainDataDirectory().account_credentials.keys()
                                       and account_id in MainDataDirectory().accounts.keys())
                            if not confirm:
                                confirm = False
                            else:
                                self.node_session_tokens[client_address] = true_token
                                node_id = MainDataDirectory().node_addresses[client_address[0]]
                    except KeyError:
                        confirm = False
                        print('Incorrect credentials for connection from address: {}'.format(client_address))
                    except Exception as e:
                        print(f'Exception {e} while verifying node account')
                        confirm = False
                else:
                    raise Exception('System Error')

            # set flag according to verification answer
            self.flag[client_address] = confirm

            # send confirmation packet to client
            answer = confirm and correct_token
            packet = Packet(request_type=PacketTypes.VERIFICATION_ANSWER, sender_type=NetworkMemberTypes.MAIN_SERVER,
                            token=true_token, data={'answer': answer, 'node id': node_id, 'account dbs': account_dbs})
            client_socket.send(packet.encode())

        # receive additional request packets and add to pipeline
        while self.run and self.flag[client_address]:
            try:
                packet_encoded = client_socket.recv()
                packet = Packet(request_encoded=packet_encoded)
                received_token = packet.token
                if received_token == true_token:
                    self.pipeline.push({'socket': client_socket, 'address': client_address, 'packet': packet,
                                        'account': account, 'account dbs': account_dbs, 'token': true_token,
                                        'account id': account_id})
                else:
                    break  # break while loop if token is incorrect
            except socket.timeout:
                continue
            except Exception as e:
                print(f'Exception "{e}" for connection with client: {client_address}')
                return

        # disconnect client and remove session token
        MainDataDirectory().remove_session_token(true_token)
        del self.flag[client_address]
        if client_address in self.node_session_tokens:
            del self.node_session_tokens[client_address]
        self.connected_sockets.remove(client_socket)

        if answer:  # if answer if False, verification answer was already disconnect notice
            packet = Packet(request_type=PacketTypes.SERVER_REQUESTING_DISCONNECT,
                            sender_type=NetworkMemberTypes.MAIN_SERVER, token=true_token)
            client_socket.send(packet.encode())

        client_socket.close()
        print('\nConnection from {} closed'.format(client_address))

    def handle_node_status_updates(self):
        # send requests for status updates, receive status updates and change data in main data director, update active nodes list in MainDataDirectory()
        while self.run:
            self.wait_for_run_flag(NODE_STATUS_UPDATING_CYCLE)
            nodes = MainDataDirectory().nodes  # {node id: (node data object, node socket)}
            active_node_ids = []
            for node_id in nodes:
                # send status check to node and check if response is received
                connected = True
                packet = Packet(request_type=PacketTypes.STATUS_UPDATE_REQUEST)
                node_socket = MainDataDirectory().nodes[node_id][1]
                node_socket.send(packet.encode())
                node_socket.settimeout(2)
                try:
                    _ = Packet(request_encoded=node_socket.recv())
                except socket.timeout:
                    connected = False

                # check if node has remaining storage
                available_storage = nodes[node_id][0].total_storage - nodes[node_id][0].data_stored
                if available_storage <= 0 and connected:
                    new_status = NodeStatus.NO_STORAGE
                else:
                    new_status = NodeStatus.AVAILABLE if connected else NodeStatus.TEMPORARILY_OFFLINE

                # update node status in MainDataDirectory()
                MainDataDirectory().nodes[node_id][0].status = new_status
                if new_status == NodeStatus.AVAILABLE and node_id not in active_node_ids:
                    active_node_ids.append(node_id)

            # update MDD data on active nodes
            MainDataDirectory().active_nodes = active_node_ids
            # resolve queues
            for node_id in active_node_ids:
                if node_id in self.node_packet_queue:
                    node_socket = MainDataDirectory().nodes[node_id][1]
                    for packet in self.node_packet_queue[node_id]:
                        node_socket.send(packet)
                        time.sleep(1)

    def handle_pipeline(self):
        """
        pipeline entry data:
        {'socket': client_socket, 'address': client_address, 'packet': packet,
        'account': account, 'account dbs': account_dbs, 'token': true_token,
        'account id': account_id}
        :return: nothing
        """
        while self.run:
            if self.pipeline.is_empty():
                continue
            pipeline_entry = self.pipeline.pop()
            packet = pipeline_entry['packet']
            request_type = packet.request_type
            # continue with handling according to type of packet
            if request_type == PacketTypes.CLIENT_REQUESTING_DISCONNECT or request_type == PacketTypes.NODE_REQUESTING_DISCONNECT:
                self.handle_disconnect(pipeline_entry['socket'], pipeline_entry['address'], pipeline_entry['token'])
                continue

            elif request_type == PacketTypes.DATA_DOWNLOAD_REQUEST:
                # check that db name/id is valid and owned by accessed account
                if (pipeline_entry['packet'].data['db name'] not in pipeline_entry['account'].databases_owned.keys()) or \
                        (pipeline_entry['packet'].data['db id'] !=
                         pipeline_entry['account'].databases_owned[pipeline_entry['packet'].data['db name']][0]):
                    self.handle_disconnect(pipeline_entry['socket'], pipeline_entry['address'], pipeline_entry['token'],
                                           disconnect_completely=False)
                    continue
                self.handle_download(pipeline_entry['socket'], pipeline_entry['address'], pipeline_entry['token'],
                                     pipeline_entry['packet'].data['db id'])
                continue

            elif request_type == PacketTypes.DATA_RELOCATION:
                self.handle_data_relocation(pipeline_entry['socket'], pipeline_entry['address'],
                                            pipeline_entry['token'],
                                            pipeline_entry['packet'])
                continue

            elif request_type == PacketTypes.DELETE_DB:
                self.handle_db_delete(pipeline_entry['packet'])

            elif request_type == PacketTypes.DATA_UPLOAD_REQUEST:
                self.handle_upload(pipeline_entry['socket'], pipeline_entry['address'], pipeline_entry['token'],
                                   pipeline_entry['packet'], pipeline_entry['account id'])
                continue

            elif request_type == PacketTypes.WITHDRAW_AS_NODE:
                self.handle_node_withdrawal(pipeline_entry['packet'], pipeline_entry['address'])
                continue

            elif request_type == PacketTypes.REQUEST_LOWERING_MEMORY_SPACE:
                if pipeline_entry['packet'].token == self.node_session_tokens[pipeline_entry['address']]:
                    memory_to_free = pipeline_entry['packet'].data['memory to free']
                    MainDataDirectory().nodes[0].total_storage -= memory_to_free
                continue

    def handle_download(self, client_socket, client_address, token, db_id):
        # create list of source nodes
        source = {}  # {node ip address: node id}
        db_storage_data = MainDataDirectory().db_storage_division[db_id]  # {collection name: {node id: [item ids]}}
        db_data = MainDataDirectory().database_data[db_id]  # {collection name: {item id: data size}}
        nodes_data = MainDataDirectory().nodes  # {node id: (node data object, node socket)}

        # run algorithm to find shortest combination of nodes that contain all data
        node_ids = find_nodes_with_database(db_id)
        for node_id in node_ids:
            source[nodes_data[node_id][0].address[0]] = node_id

        # if a certain node contains a full collection, add to source list
        for collection_name in db_storage_data.keys():
            item_count = len(list(db_data[collection_name].keys()))
            for node_id in db_storage_data[collection_name].keys():
                if len(db_storage_data[collection_name][node_id]) == item_count:
                    source[nodes_data[node_id][0].address[0]] = node_id

        # send source list and other data to client
        packet = Packet(request_type=PacketTypes.BE_READY_FOR_DATA, sender_type=NetworkMemberTypes.MAIN_SERVER,
                        data={'whitelist': nodes_data, 'item count': MainDataDirectory().count_db_items(db_id)},
                        token=token)
        client_socket.send(packet.encode())

        # send instructions to source nodes
        for node_id in source.values():
            node_token = self.node_session_tokens[MainDataDirectory().nodes[node_id][0].address]
            packet = Packet(request_type=PacketTypes.SEND_DATA_FROM_STORAGE, sender_type=NetworkMemberTypes.MAIN_SERVER,
                            data={'target': client_address[0], 'db id': db_id}, token=node_token)
            node_socket = MainDataDirectory().nodes[node_id][1]
            node_socket.send(packet.encode())

        # receive confirmation from client, redo actions with all nodes if data is missing
        packet = Packet(request_encoded=client_socket.recv())
        confirmation = packet.data['answer']
        if confirmation and token == packet.token:
            return
        elif token != packet.token:
            self.handle_disconnect(client_socket, client_address, token)

        # resend node ids to client, this time send all possible node ids
        # create source list
        for collection_name in db_storage_data.keys():
            for node_id in db_storage_data[collection_name].keys():
                source[nodes_data[node_id][0].address[0]] = node_id

        # send source list and other data to client (second round)
        packet = Packet(request_type=PacketTypes.BE_READY_FOR_DATA, sender_type=NetworkMemberTypes.MAIN_SERVER,
                        data={'whitelist': nodes_data, 'item count': MainDataDirectory().count_db_items(db_id)},
                        token=token)
        client_socket.send(packet.encode())

        # send instructions to source nodes (second round)
        for node_id in source.values():
            # send instructions, add node id as token to prove source is a trusted network element
            packet = Packet(request_type=PacketTypes.SEND_DATA_FROM_STORAGE, sender_type=NetworkMemberTypes.MAIN_SERVER,
                            data={'target': client_address, 'db id': db_id}, token=node_id)
            node_socket = MainDataDirectory().nodes[node_id][1]
            node_socket.send(packet.encode())

        # receive confirmation from client (second round -> answer not relevant
        _ = Packet(request_encoded=client_socket.recv())
        return

    def handle_data_relocation(self, source_node_socket, source_node_address, token, packet):
        # get necessary data
        uploaded_data_details = packet.data
        db_id = uploaded_data_details['db id']
        source_node_id = packet.data['source node']
        db_info = uploaded_data_details['db info']  # {collection name: {item id: item data size}}

        # determine size of necessary data allocation
        data_size = 0
        for col_name in db_info.keys():
            for item_id, item_size in db_info[col_name].items():
                data_size += item_size

        # randomly select new node to transfer data to
        target_node_id = None
        nodes_checked_counter = 0
        while target_node_id is None or source_node_id == target_node_id or nodes_checked_counter == len(
                MainDataDirectory().nodes.keys()) or (
                MainDataDirectory().nodes[target_node_id][0].total_storage - MainDataDirectory().nodes[target_node_id][
            0].data_stored < data_size):
            target_node_id = random.choice(MainDataDirectory().nodes.keys())
            nodes_checked_counter += 1

        # send be-ready notification to target node
        packet = Packet(request_type=PacketTypes.BE_READY_FOR_DATA, sender_type=NetworkMemberTypes.MAIN_SERVER,
                        data={'source node ip': source_node_address[0]}, token=self.node_session_tokens[target_node_id])
        node_socket = MainDataDirectory().nodes[target_node_id][1]
        node_socket.send(packet.encode())

        # send target node address to source node
        packet = Packet(request_type=PacketTypes.DATA_RELOCATION_INSTRUCTIONS,
                        sender_type=NetworkMemberTypes.MAIN_SERVER,
                        data={'target node id': target_node_id,
                              'target node ip': MainDataDirectory().nodes[target_node_id][0].address[0]}, token=token)
        source_node_socket.send(packet.encode())

        # receive confirmation from source node
        packet = Packet(request_encoded=source_node_socket.recv())
        confirmation = packet.data['answer']
        if not confirmation:
            return

        # update data in MDD
        # update 'db_storage_division'
        db_storage_division = MainDataDirectory().db_storage_division[db_id]  # {collection name: {node id: [item ids]}}
        for col_name in db_storage_division.keys():
            keys, values = list(db_storage_division[col_name].keys()), list(db_storage_division[col_name].values())
            index = keys.index(source_node_id)
            keys[index] = target_node_id
        MainDataDirectory().db_storage_division[db_id] = db_storage_division
        # update 'node_storage_data'
        node_storage_data = MainDataDirectory().node_storage_data  # {node id: {id of stored db: {name of stored collection: count of stored items}}}
        stored_db_data = node_storage_data[source_node_id][db_id]
        node_storage_data[target_node_id][db_id] = stored_db_data
        del node_storage_data[source_node_id][db_id]
        MainDataDirectory().node_storage_data = node_storage_data
        # update node data objects
        MainDataDirectory().nodes[source_node_id][0].data_stored -= data_size
        MainDataDirectory().nodes[target_node_id][0].data_stored += data_size

    def handle_node_withdrawal(self, packet, node_address):
        # get necessary data from pipeline entry
        node_id = packet.data['node id']
        credentials = packet.data['credentials']
        account_id = MainDataDirectory().account_credentials[credentials]

        # recheck token
        if packet.token != self.node_session_tokens[node_id]:
            return

        # verify credentials
        try:
            confirm = credentials in MainDataDirectory().account_credentials.keys()
            confirm = confirm and MainDataDirectory().node_addresses[node_address[0]] == node_id
        except KeyError:
            return
        if not confirm:
            return

        # delete all node/account data from MDD
        MainDataDirectory().remove_account(account_id, credentials)
        MainDataDirectory().remove_node(node_id, node_address)

    def handle_db_delete(self, packet):
        # get necessary data
        db_id = packet.data['db id']

        # get storage nodes that are holding db, also save data on memory space to later update MDD
        storing_nodes = {}  # {node id: storage space of db in node}
        storage_division = MainDataDirectory().db_storage_division[db_id]  # {collection name: {node id: [item ids]}}
        database_data = MainDataDirectory().database_data[db_id]  # {collection name: {item id: item data size}}
        for col_name in storage_division.keys():
            for node_id in storage_division[col_name]:
                storing_nodes[node_id] = 0
                for item_id in storage_division[col_name][node_id]:
                    storing_nodes[node_id] += database_data[col_name][item_id]

        # notify nodes about deleting db and receive confirmation from each
        for node_id in storing_nodes.keys():
            # get node socket and send notification
            node_socket = MainDataDirectory().nodes[node_id][1]
            node_socket.settimeout(1)
            confirm = None
            sent_packet = None
            try:
                sent_packet = Packet(request_type=PacketTypes.DELETE_DB, sender_type=NetworkMemberTypes.MAIN_SERVER,
                                     data={'db id': db_id},
                                     token=self.node_session_tokens[node_id])
                node_socket.send(sent_packet.encode())
            except socket.timeout:
                confirm = False

            if confirm is None:
                # receive confirmation
                packet = Packet(request_encoded=node_socket.recv())
                confirm = packet.data['answer']

                # if request not confirmed, add packet to node queue
                if not confirm:
                    if node_id not in self.node_packet_queue:
                        self.node_packet_queue[node_id] = []
                    self.node_packet_queue[node_id].append(sent_packet)

        # update MDD data
        try:
            # update 'db_storage_division'
            del MainDataDirectory().db_storage_division[db_id]
            # update 'database_data'
            del MainDataDirectory().database_data[db_id]
            # update 'collection_hashes'
            del MainDataDirectory().collection_hashes[db_id]
            # update 'node_storage_data'
            for node_id in storing_nodes.keys():
                del MainDataDirectory().node_storage_data[node_id][db_id]
            # update node data objects in 'nodes'
            nodes = MainDataDirectory().nodes
            for node_id in storing_nodes.keys():
                nodes[node_id][0].data_stored -= storing_nodes[node_id]
        except KeyError:
            pass

    def handle_upload(self, client_socket, client_address, token, packet, account_id):
        # get necessary data
        uploaded_data_details = packet.data
        db_id = uploaded_data_details['db id']
        updated_items = {}  # final data to send client - {collection name: {updated item id: item data size}}
        uploaded_collection_hashes = uploaded_data_details['collection hashes']  # {collection name: collection hash}
        uploaded_item_ids = uploaded_data_details['db data']  # {collection name: {item id: item data size}}

        # start by checking if uploaded db already exists
        if db_id is None:
            # handle case: new DB
            updated_items = uploaded_data_details['db data']  # every item in new db is considered updated (new)
            # initialize MainDataDirectory() data
            db_id = MainDataDirectory().generate_db_id()
            MainDataDirectory().accounts[account_id][1][uploaded_data_details['db name']] = db_id
            MainDataDirectory().accounts[account_id][0].databases_owned['db name'] = db_id
            MainDataDirectory().node_storage_data[db_id] = {}
            MainDataDirectory().db_storage_division[db_id] = {}
        else:
            # compare current collection hashes to uploaded collection hashes and find collections with updated data
            current_collection_hashes = MainDataDirectory().collection_hashes[db_id]
            changed_collection_names = []  # list of collections with updated hashes

            # check if new collections exist, new collections are automatically added to list of updated collections
            for col_name in uploaded_collection_hashes.keys():
                if col_name not in current_collection_hashes.keys():
                    changed_collection_names.append(col_name)

            # check if existing collections are changed
            for col_name in current_collection_hashes.keys():
                if col_name not in uploaded_collection_hashes.keys():
                    changed_collection_names.append(col_name)
                else:
                    if current_collection_hashes[col_name] != uploaded_collection_hashes[col_name]:
                        if col_name not in changed_collection_names:
                            changed_collection_names.append(col_name)

            # find items with updated data
            # add all items from changed collections
            for col_name in changed_collection_names:
                if col_name not in uploaded_item_ids.keys():
                    updated_items[col_name] = {None: None}
                else:
                    updated_items[col_name] = uploaded_item_ids[col_name]

        # find nodes to store updated items/collections
        best_nodes_ids = get_closest_available_nodes(client_address)
        nodes = MainDataDirectory().nodes  # {node id: (node data object, node socket)}
        best_nodes_ip_addresses = [nodes[node_id][0].address[0] for node_id in best_nodes_ids]

        # send node addresses and details on updated data to client
        data = {'nodes': dict(zip(best_nodes_ids, best_nodes_ip_addresses)), 'updated data': updated_items,
                'db id': db_id}
        packet = Packet(request_type=PacketTypes.DATA_UPLOAD_INSTRUCTIONS, sender_type=NetworkMemberTypes.MAIN_SERVER,
                        data=data, token=token)
        client_socket.send(packet.encode())

        # get selected nodes from client
        packet = Packet(request_encoded=client_socket.recv(receive_all_data=True))
        if packet.token != token:
            self.handle_disconnect(client_socket, client_address, token)
            return
        selected_nodes = packet.data['nodes']  # {node id: node ip address}

        # send be-ready notifications to nodes
        nodes = MainDataDirectory().nodes  # {node id: (node data object, node socket)}
        for node_id in selected_nodes.keys():
            node_socket = nodes[node_id][1]
            node_token = self.node_session_tokens[MainDataDirectory().nodes[node_id][0].address]
            packet = Packet(request_type=PacketTypes.BE_READY_FOR_DATA, sender_type=NetworkMemberTypes.MAIN_SERVER,
                            data={'ip address': client_address[0], 'db id': db_id}, token=node_token)
            node_socket.send(packet.encode())

        # send start notification to client
        packet = Packet(request_type=PacketTypes.DATA_UPLOAD_INSTRUCTIONS, sender_type=NetworkMemberTypes.MAIN_SERVER,
                        token=token)
        client_socket.send(packet.encode())

        # get confirmation from client
        packet = Packet(request_encoded=client_socket.recv())
        confirmation = packet.data['answer']

        # send client confirmation to nodes, if upload was not confirmed, nodes do not save data
        for node_id in selected_nodes.keys():
            node_socket = nodes[node_id][1]
            node_token = self.node_session_tokens[MainDataDirectory().nodes[node_id][0].address]
            packet = Packet(request_type=PacketTypes.DATA_UPLOAD_FINAL_RESPONSE,
                            sender_type=NetworkMemberTypes.MAIN_SERVER,
                            data={'answer': confirmation}, token=node_token)
            node_socket.send(packet.encode())

        # update data in MainDataDirectory() to match new upload (if upload is confirmed)
        if not confirmation:
            return

        # update MainDataDirectory() data
        # update 'database_data'
        database_data = uploaded_data_details['db info']
        MainDataDirectory().database_data[db_id] = database_data
        # update 'collection_hashes'
        MainDataDirectory().collection_hashes = uploaded_collection_hashes
        # update 'node_storage_data'
        current_node_storage_data = MainDataDirectory().node_storage_data  # {node id: {id of stored db: {name of stored collection: count of stored items}}}
        for node_id in selected_nodes.keys():
            node_db_data = current_node_storage_data[node_id][db_id]
            for col_name in updated_items.keys():
                if col_name not in node_db_data.keys():
                    node_db_data[col_name] = 0
                node_db_data[col_name] += len(list(updated_items[col_name].keys()))
            current_node_storage_data[node_id][db_id] = node_db_data
        MainDataDirectory().node_storage_data = current_node_storage_data
        # update 'db_storage_division'
        current_db_storage_division = MainDataDirectory().db_storage_division[
            db_id]  # {collection name: {node id: [item ids]}}
        for col_name in updated_items.keys():
            if col_name not in current_db_storage_division.keys():
                current_db_storage_division[col_name] = {}
            for node_id in selected_nodes.keys():
                if node_id not in current_db_storage_division[col_name]:
                    current_db_storage_division[col_name][node_id] = []
                current_db_storage_division[col_name][node_id].extend(list(updated_items[col_name].keys()))
        MainDataDirectory().db_storage_division[db_id] = current_db_storage_division
        # update NodeData objects in MDD.nodes
        nodes = MainDataDirectory().nodes  # {node id: (node data object, node socket)}
        new_data_counter = 0
        for col_name in updated_items.keys():  # {collection name: {updated item id: item data size}}
            for item_id, data_size in updated_items[col_name].items():
                new_data_counter += data_size
        for node_id, obj_and_socket in selected_nodes.items():
            obj_and_socket[0].data_stored += new_data_counter
        MainDataDirectory().nodes = nodes

    def handle_disconnect(self, client_socket, client_address, token, disconnect_completely=True):
        # send disconnect confirmation
        packet = Packet(request_type=PacketTypes.DISCONNECT_CONFIRMED_BY_SERVER,
                        sender_type=NetworkMemberTypes.MAIN_SERVER, token=token)
        client_socket.send(packet.encode())

        # stop thread and disconnect socket
        if disconnect_completely:
            self.flag[client_address] = False
            self.connected_sockets.remove(client_socket)
            client_socket.close()
            print('Connection from {} closed'.format(client_address))

    def wait_for_run_flag(self, seconds):
        """
        :param seconds: number of seconds to wait while checking flag every second
        :return: None
        """
        counter = 0
        while counter < seconds and self.run:
            time.sleep(0.99999999)
            counter += 1
        return

    def stop_server(self):
        self.run = False
        for sock in self.connected_sockets:
            sock.close()
            print('OrionDB main server closed')
