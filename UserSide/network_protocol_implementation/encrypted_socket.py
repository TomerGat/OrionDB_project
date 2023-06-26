import socket
from network_protocol_implementation.encryption import encrypt, decrypt, generate_encryption_key
from hash import hash_function
from userside_final_values import HASH_LENGTH_LIMIT, MAXIMUM_PACKET_SIZE


class EncryptedSocket(socket.socket):
    def __init__(self, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0, fileno=None):
        super().__init__(family, type, proto, fileno)

    def send(self, encoded_data, flags=0):
        # decode data
        data = encoded_data.decode()

        # generate incomplete encryption to pass over communication
        key = generate_encryption_key()

        # create true encryption key with hash function
        true_key = str(hash_function(key))

        # handle situation in which key is of incorrect length
        if len(str(true_key)) != HASH_LENGTH_LIMIT:
            while len(str(true_key)) != HASH_LENGTH_LIMIT:
                # generate incomplete encryption to pass over communication
                key = generate_encryption_key()

                # create true encryption key with hash function
                true_key = str(hash_function(key))

        # encrypt data with true encryption key
        encrypted_data = encrypt(data, true_key)

        # add key to encrypted data
        final_data = key + '<DELIMITER>' + encrypted_data

        # add size of data to string so receiving socket can receive all data
        buffer_size = str(len(final_data) + len(str(len(final_data))) + len('<DELIMITER>'))

        final_data = buffer_size + '<DELIMITER>' + final_data

        # send encrypted data
        super().send(final_data.encode(), flags)

    def recv(self, bufsize=MAXIMUM_PACKET_SIZE, flags=0, receive_all_data=False):
        # receive data
        data_length_and_data_and_key = super().recv(bufsize, flags).decode()

        # check if enough data was received to include buffer size and encryption key
        if data_length_and_data_and_key.count('<DELIMITER>') < 2:
            if receive_all_data:
                remaining_buffer_size = 128
                data_length_and_data_and_key += super().recv(remaining_buffer_size, flags).decode()
            else:
                raise Exception('Buffer size is not sufficient for encrypted communication')

        # extract the key and encrypted data
        length, key, encrypted_data = data_length_and_data_and_key.split('<DELIMITER>')

        # create true key with hash function
        true_key = str(hash_function(key))

        # if receive_all_data is set to true, check if incoming data is larger than buffer and receive rest of data
        if receive_all_data and int(length) > bufsize:
            remaining_data = int(length) - bufsize
            while remaining_data > 0:
                buffer = bufsize if bufsize < remaining_data else remaining_data
                encrypted_data += super().recv(buffer, flags).decode()
                remaining_data -= buffer

        # decode data with decrypt function
        data = decrypt(encrypted_data, true_key)

        return data.encode()

    def accept(self):
        # Accept the connection and get the client socket and address
        client_socket, client_address = super().accept()

        # Create an instance of EncryptedSocket using the client socket
        encrypted_client_socket = EncryptedSocket(
            family=self.family,
            type=self.type,
            proto=self.proto,
            fileno=client_socket.detach()  # Detach the file descriptor from the client socket
        )

        # Set the client socket options on the encrypted socket
        encrypted_client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        return encrypted_client_socket, client_address
