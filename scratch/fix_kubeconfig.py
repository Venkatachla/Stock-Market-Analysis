import os

kubeconfig_path = os.path.expanduser("~/.kube/config")
with open(kubeconfig_path, 'rb') as f:
    data = f.read()

# Try to decode as UTF-16 LE, then UTF-8, then strip nulls
try:
    text = data.decode('utf-16')
    print("Decoded as UTF-16")
except:
    try:
        text = data.decode('utf-8')
        print("Decoded as UTF-8")
    except:
        print("Forcing decode and stripping nulls")
        text = data.decode('ascii', errors='ignore').replace('\0', '')

# Ensure it starts with 'apiVersion' (skip any BOM or garbage)
if 'apiVersion' in text:
    start_index = text.find('apiVersion')
    text = text[start_index:]
    
    with open(kubeconfig_path + '.fixed', 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print(f"Fixed file written to {kubeconfig_path}.fixed")
else:
    print("Could not find apiVersion in content")
