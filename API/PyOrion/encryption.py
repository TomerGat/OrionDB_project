from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from hash import sha_function
from util_functions import generate_random_number


def generate_encryption_key() -> str:
    random_num = generate_random_number()
    key = sha_function(str(random_num))
    return key


def encrypt(plaintext, key):
    cipher = AES.new(key.encode(), AES.MODE_CBC)
    cipher_text = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode()
    encrypted_data = base64.b64encode(cipher_text).decode()
    return iv + encrypted_data


def decrypt(cipher_text, key) -> str:
    iv = base64.b64decode(cipher_text[:24])
    encrypted_data = base64.b64decode(cipher_text[24:])
    cipher = AES.new(key.encode(), AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
    return decrypted_data.decode()
