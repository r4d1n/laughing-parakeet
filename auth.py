import base64, json, requests

with open('config.json', 'r') as f:
    config = json.load(f)

def get_twitter_token():
    client_key = config['twitter']['client_key']
    client_secret = config['twitter']['client_secret']

    key_secret = '{}:{}'.format(client_key, client_secret).encode('ascii')
    b64_encoded_key = base64.b64encode(key_secret)
    b64_encoded_key = b64_encoded_key.decode('ascii')

    base_url = 'https://api.twitter.com/'
    auth_url = '{}oauth2/token'.format(base_url)

    auth_headers = {
        'Authorization': 'Basic {}'.format(b64_encoded_key),
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }

    auth_data = {
        'grant_type': 'client_credentials'
    }

    auth_resp = requests.post(auth_url, headers=auth_headers, data=auth_data)
    auth_json = auth_resp.json()
    print('Successful Twitter Auth result: {}'.format(auth_json))
    return auth_json['access_token']
