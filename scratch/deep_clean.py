import yaml
import base64
import re
import os

path = os.path.expanduser("~/.kube/config")
with open(path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

def clean_b64(name, data):
    if not data: return data
    # Remove all whitespace and illegal characters
    cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', data)
    try:
        base64.b64decode(cleaned)
        print(f"Field {name} is valid Base64 after cleaning")
        return cleaned
    except Exception as e:
        print(f"Field {name} is STILL invalid: {e}")
        # Try to fix padding
        while len(cleaned) % 4 != 0:
            cleaned += '='
        try:
            base64.b64decode(cleaned)
            print(f"Field {name} fixed with padding")
            return cleaned
        except:
            return cleaned

if 'clusters' in config:
    for cl in config['clusters']:
        if 'certificate-authority-data' in cl['cluster']:
            cl['cluster']['certificate-authority-data'] = clean_b64('ca', cl['cluster']['certificate-authority-data'])

if 'users' in config:
    for u in config['users']:
        if 'client-certificate-data' in u['user']:
            u['user']['client-certificate-data'] = clean_b64('client-cert', u['user']['client-certificate-data'])
        if 'client-key-data' in u['user']:
            u['user']['client-key-data'] = clean_b64('client-key', u['user']['client-key-data'])

with open(path + '.fixed3', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, default_flow_style=False)
print("Wrote fixed3")
