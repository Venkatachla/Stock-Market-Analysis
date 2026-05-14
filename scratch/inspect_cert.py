import yaml
import base64
import os

path = os.path.expanduser("~/.kube/config")
with open(path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

ca_data = config['clusters'][0]['cluster']['certificate-authority-data']
decoded = base64.b64decode(ca_data)

print(f"Decoded length: {len(decoded)}")
print(f"Starts with: {decoded[:20]}")
print(f"Ends with: {decoded[-20:]}")

with open('ca.crt', 'wb') as f:
    f.write(decoded)
