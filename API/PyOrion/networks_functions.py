import subprocess
import re


def calculate_ttl(client_ip):
    try:
        # Run the ping command to the client address with a timeout of 1 second
        ping_process = subprocess.Popen(['ping', '-n', '1', client_ip], stdout=subprocess.PIPE)
        output, _ = ping_process.communicate()

        # Parse the output using regular expressions to extract the TTL
        ttl_pattern = r'TTL=(\d+)'
        ttl_values = re.findall(ttl_pattern, output.decode())

        ttl_values = [int(ttl) for ttl in ttl_values]
        if ttl_values:
            return ttl_values[0]
        else:
            raise Exception("Failed to determine TTL.")

    except Exception as e:
        raise Exception("Error calculating TTL: {}".format(str(e)))
