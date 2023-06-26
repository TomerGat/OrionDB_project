import random
from final_values import MAX_NUMBER_TO_GENERATE
import datetime


def validate_string(text: str) -> bool:
    word = str(text)
    if len(word) == 0:
        return False
    valid = True
    non_valid = [':', '(', '{', ')', '}', ',', '^', '<', '>', '+', '*', '/', '%', '=', '|', ';']
    counter = 0
    while counter < len(word):
        ch = word[counter]
        if ch in non_valid:
            valid = False
            break
        else:
            counter += 1
    return valid


def dict_to_str(data):  # not using json dumps/loads because json function convert all keys to str
    def _dict_to_string_helper(data):
        if isinstance(data, dict):
            items = []
            for key, value in data.items():
                if isinstance(key, str):
                    key_str = f'"{key}"'
                else:
                    key_str = str(key)
                if isinstance(value, dict):
                    items.append(f'{key_str}:{{{_dict_to_string_helper(value)}}}')
                elif isinstance(value, str):
                    items.append(f'{key_str}:"{value}"')
                elif value is None:
                    items.append(f'{key_str}:"."')
                elif isinstance(value, (int, float, bool)):
                    items.append(f'{key_str}:{value}')
                else:
                    raise ValueError(f"Unsupported value type for {key}:{value}, value type is {type(value).__name__}")
            return ",".join(items)
        else:
            raise ValueError("Input must be a dictionary.")

    return "{" + _dict_to_string_helper(data) + "}"


def str_to_dict(data):  # redo recursively
    def _string_to_dict_helper(data_str):
        stack = []
        result = {}
        key = ""
        value = ""

        for char in data_str:
            if char == "{":
                stack.append(result)
                stack.append(key)
                stack.append(value)
                result = {}
                key = ""
                value = ""
            elif char == "}":
                if value:
                    result[key] = value

                prev_value = stack.pop()
                prev_key = stack.pop()
                prev_result = stack.pop()
                prev_result[prev_key] = result
                result = prev_result
                key = prev_key
                value = prev_value
            elif char == ":":
                key = value
                value = ""
            elif char == ",":
                if value:
                    result[key] = value
                    key = ""
                    value = ""
            else:
                value += char
        if value:
            result[key] = value

        return result

    if data.startswith("{") and data.endswith("}"):
        return resolve_data_types(_string_to_dict_helper(data[1:-1]))
    else:
        raise ValueError("Invalid string format. Input must be enclosed in curly brackets.")


def resolve_data_types(data):
    def _resolve_type_helper(var):
        if var[0] == '"':
            if var == '"."':
                return None
            new = var[1:-1]
        else:
            if var[0] == 'T':
                return True
            elif var[0] == 'F':
                return False
            else:
                if '.' in var:
                    new = float(var)
                else:
                    new = int(var)
        return new

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result_key, result_value = key, value
            result_key = _resolve_type_helper(key)
            if isinstance(value, dict):
                result_value = resolve_data_types(value)
            else:
                result_value = _resolve_type_helper(value)
            result[result_key] = result_value

        return result
    else:
        raise Exception('Input must be a dictionary')


def generate_random_number():
    num = random.randint(0, MAX_NUMBER_TO_GENERATE)
    return num


def search_for_key(data: {}, search_key):  # search for key in dict
    for key in data.keys():
        if key == search_key:
            return data[key]
        elif type(data[key]).__name__ == 'dict':
            value = search_for_key(data[key], search_key)
            if value is not None:
                return value
    return None


def get_key_for_highest_value(numbers_dict: {any: int}):
    numbers = list(numbers_dict.values())
    highest = numbers[0]
    for num in numbers:
        if num > highest:
            highest = num
    for key, value in numbers_dict.items():
        if value == highest:
            return key
    return None


def get_key_for_lowest_value(numbers_dict: {any: int}):
    numbers = list(numbers_dict.values())
    lowest = numbers[0]
    for num in numbers:
        if num < lowest:
            highest = num
    for key, value in numbers_dict.items():
        if value == lowest:
            return key
    return None


def get_precise_time():
    now = str(datetime.datetime.now())
    year = int(now[0:4])
    month = int(now[5:7])
    day = int(now[8:10])
    hour = int(now[11:13])
    minute = int(now[14:16])
    second = float(now[17:21])
    return [year, month, day, hour, minute, second]


def get_numeral_date_representation(timestamp):
    return float(
        timestamp.year * 365 * 24 * 60 * 60 +
        timestamp.month * 30 * 24 * 60 * 60 +
        timestamp.day * 24 * 60 * 60 +
        timestamp.hour * 60 * 60 +
        timestamp.minute * 60 +
        timestamp.second
    )


def check_credentials_format(string):
    valid = string.count('.') == 1 and string.count('//') == 1 and string.count('=') == 1
    return valid


def selection_sort(numbers):
    if len(numbers) <= 1:
        return numbers

    # find the minimum element in the unsorted part of the array
    min_idx = 0
    for i in range(1, len(numbers)):
        if numbers[i] < numbers[min_idx]:
            min_idx = i

    # swap the minimum element with the first element
    numbers[0], numbers[min_idx] = numbers[min_idx], numbers[0]

    # recursively sort the remaining part of the array
    return [numbers[0]] + selection_sort(numbers[1:])


def format_for_xml(string):
    new_string = 'OPENER'.join(string.split('{'))
    final_string = 'CLOSER'.join(new_string.split('}'))
    last = 'KEYTOVALUE'.join(final_string.split(':'))
    valid = 'QOUTE'.join(last.split('"'))
    final_valid = 'COMMA'.join(valid.split(','))
    to_return = 'DOT'.join('UNDER'.join(final_valid.split('_')).split('.'))
    return to_return


def format_from_xml(string):
    new_string = '{'.join(string.split('OPENER'))
    final_string = '}'.join(new_string.split('CLOSER'))
    last = ':'.join(final_string.split('KEYTOVALUE'))
    valid = '"'.join(last.split('QOUTE'))
    final_valid = ','.join(valid.split('COMMA'))
    to_return = '.'.join('_'.join(final_valid.split('UNDER')).split('DOT'))
    return to_return
