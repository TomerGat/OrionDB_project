from network_protocol_implementation.encrypted_socket import EncryptedSocket
from final_values import MAIN_SERVER_ADDRESS
from data_structures import NetworkMemberTypes, PacketTypes
from hash import sha_function
from network_protocol_implementation.request_structure import Packet


def initial_server_connect():
    """
    :return: true token (after exchange with server), socket (already connected to server)
    """
    # create socket to connect to server
    server_socket = EncryptedSocket()

    # send connection request to main server
    server_socket.connect(MAIN_SERVER_ADDRESS)

    # receive session token from server
    packet = Packet(request_encoded=server_socket.recv())
    token = packet.token
    true_token = str(sha_function(token))

    return server_socket, true_token


def request_additional_storage_space(storage_space_size, node_id, confirmation_code):
    """
    :param storage_space_size: additional storage space allocation requested
    :param node_id: node id that is requesting to allocate memory
    :param confirmation_code: confirmation code from memory space allocation approval
    :return: return confirmation
    """
    server_socket, true_token = initial_server_connect()

    # send request
    packet = Packet(request_type=PacketTypes.REQUEST_ADDITIONAL_MEMORY_SPACE, sender_type=NetworkMemberTypes.STORAGE_NODE,
                    token=true_token, data={'requested space': storage_space_size, 'node id': node_id, 'confirmation code': confirmation_code})
    server_socket.send(packet.encode())

    # receive confirmation
    packet = Packet(request_encoded=server_socket.recv())
    confirmation = packet.data['answer']
    server_socket.close()
    return confirmation


def get_node_approval(requested_storage_space):
    """
    :param requested_storage_space: storage space allocation requested
    :return: approval (boolean), confirmation code
    """
    server_socket, true_token = initial_server_connect()

    # send request
    packet = Packet(request_type=PacketTypes.NEW_NODE_APPROVAL_REQUEST, sender_type=NetworkMemberTypes.CLIENT,
                    token=true_token, data={'credentials': None, 'requested space': requested_storage_space})
    server_socket.send(packet.encode())

    # receive confirmation
    packet = Packet(request_encoded=server_socket.recv())
    confirmation = packet.data['answer']
    confirmation_code = packet.data['confirmation code']
    server_socket.close()

    return confirmation, confirmation_code


def open_node_account(username, password, storage_space, confirmation_code):
    """
    :param username: account username
    :param password: account password
    :param storage_space: requested storage space
    :param confirmation_code: confirmation code (after requesting node approval)
    :return: connection string to account if confirmed, else None is returned
    """
    server_socket, true_token = initial_server_connect()

    # send request to open account
    credentials = {'username': username, 'password': password}
    packet = Packet(request_type=PacketTypes.NEW_NODE_CONNECTION, sender_type=NetworkMemberTypes.STORAGE_NODE,
                    token=true_token, data={'credentials': credentials, 'available storage': storage_space, 'confirmation code': confirmation_code})
    server_socket.send(packet.encode())

    # receive disconnect request and close server
    packet = Packet(request_encoded=server_socket.recv())
    server_socket.close()

    return f'oriondb.node//{username}={password}' if packet.data['answer'] else None


def open_account(username, password):
    """
    :param username: account username
    :param password: account password
    :return: onnection string to account if confirmed, else None is returned
    """
    server_socket, true_token = initial_server_connect()

    # send request to open account
    credentials = {'username': username, 'password': password}
    packet = Packet(request_type=PacketTypes.OPEN_ACCOUNT, sender_type=NetworkMemberTypes.CLIENT, token=true_token,
                    data={'credentials': credentials})
    server_socket.send(packet.encode())
    # receive disconnect request and close server
    packet = Packet(request_encoded=server_socket.recv())
    server_socket.close()

    return f'oriondb.account//{username}={password}' if packet.data['answer'] else None
