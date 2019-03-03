import requests


# Sends stop to a container
def send_stop(dns_name, secret_key):
    resp = requests.get('http://{}/stop'.format(dns_name), params={'secret_key': secret_key})
    resp.raise_for_status()


# Wait for a container to indicate that it is stopped.
def wait_for_stopped(dns_name, secret_key):
    try:
        while True:
            resp = requests.get('http://{}/is_stopped'.format(dns_name), params={'secret_key': secret_key})
            if resp.text == 'true':
                return
    except requests.exceptions.ConnectionError:
        return


# Returns status information from a container.
def fetch_info(dns_name):
    resp = requests.get('http://{}'.format(dns_name))
    resp.raise_for_status()
    return resp.json()
