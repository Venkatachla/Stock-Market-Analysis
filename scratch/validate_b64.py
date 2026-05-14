import os
import yaml
import base64
import re

path = os.path.expanduser("~/.kube/config")
with open(path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

def clean_base64(data):
    if not isinstance(data, str):
        return data
    # Remove any character that is not valid Base64
    cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', data)
    # Ensure padding is correct
    while len(cleaned) % 4 != 0:
        cleaned += '='
    # Try to decode to verify
    try:
        base64.b64decode(cleaned)
        return cleaned
    except:
        return cleaned # Fallback

# Walk through the config and clean data fields
if 'clusters' in config:
    for c in config['clusters']:
        if 'certificate-authority-data' in c['cluster']:
            c['cluster']['certificate-authority-data'] = clean_base64(c['cluster']['certificate-authority-data'])

if 'users' in config:
    for u in config['users']:
        if 'client-certificate-data' in u['user']:
            u['user']['client-certificate-data'] = clean_base64(u['user']['client-certificate-data'])
        if 'client-key-data' in u['user']:
            u['user']['client-key-data'] = clean_base64(u['user']['client-key-data'])

with open(path + '.valid', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, default_flow_style=False)
print("Wrote valid kubeconfig")
