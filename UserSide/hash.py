import math
import hashlib
from userside_final_values import HASH_LENGTH_LIMIT


def digit_count(num: int) -> int:
    str_num = str(num)
    counter = 0
    for ch in str_num:
        counter += 1
    return counter


def multiple(vec: list) -> int:
    mul = 1
    for i in vec:
        mul *= i
    return mul


def sum_vec(vec: list) -> int:
    s = 0
    for i in vec:
        s += i
    return s


def limit_hash_length(num: int) -> int:
    while digit_count(num) < HASH_LENGTH_LIMIT:
        num *= 10
    return num % (10**HASH_LENGTH_LIMIT)


def hash_function(param) -> int:
    """
    :param param: input
    :return: hash value of input
    """
    input_str = sha_function(str(param))
    ascii_values = [ord(ch) for ch in input_str]
    values = []
    for i in range(len(ascii_values)):
        values.append((i * 123854 ^ ascii_values[i] * 984) | (multiple(ascii_values)))
    val = ((sum_vec(values) + 2587465) & (123 + 951456 * (multiple(values)) + 456 * sum_vec(values)))
    if val < 0:
        val = val ^ (sum_vec(ascii_values) + 95813)
    factor = (((sum_vec(values) + 15984354) | (multiple(values) + 10000009814008)) & ((sum_vec(ascii_values) + 87515557) ^ (multiple(ascii_values) * 8558224)))
    new_val = abs(val ^ factor)
    shifts = 64 - math.floor(math.log10(new_val)) + 1
    new_val = new_val << shifts if shifts >= 0 else new_val >> abs(shifts)
    new_val += shifts  # minimize collisions from previous line
    return limit_hash_length(abs(new_val))


def sha_function(input_str):
    # Concatenate the input
    input_bytes = bytes(input_str, 'utf-8')

    # Hash the input using SHA-256
    hashed = hashlib.sha256(input_bytes).hexdigest()

    # Convert the first 8 bytes of the hash to an integer
    # hashed_int = int.from_bytes(hashed[:8], byteorder='big')

    # Truncate or pad the integer to the desired length
    return str(hashed)
