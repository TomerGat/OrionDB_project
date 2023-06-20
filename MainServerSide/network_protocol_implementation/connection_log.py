from util_functions import get_precise_time, get_numeral_date_representation
from final_values import DEFAULT_TIMEFRAME_FOR_CONNECTIONS_SCAN
from data_structures import Pipeline


class Timestamp:
    def __init__(self):
        self.year, self.month, self.day, self.hour, self.minute, self.second = get_precise_time()


class ConnectionLog:
    def __init__(self):
        self.connections = []

    def add_connection(self):
        self.connections.append(Timestamp())

    def count_recent_connections(self, timeframe=DEFAULT_TIMEFRAME_FOR_CONNECTIONS_SCAN):
        connections_pipeline = Pipeline()
        connections_pipeline.load_list_into_pipeline(self.connections)
        counter = 0
        current_time_numeral = get_numeral_date_representation(Timestamp())
        while not connections_pipeline.is_empty():
            last_connection = connections_pipeline.pop()
            numeral_date = get_numeral_date_representation(last_connection)
            time_delta = numeral_date - current_time_numeral
            if time_delta < timeframe:
                counter += 1
        return counter
