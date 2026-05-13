import os

path = os.path.expanduser("~/.kube/config")
with open(path, 'rb') as f:
    data = f.read()

# Try to find 'apiVersion' and extract the rest
# Since we know it was UTF-16, let's try to decode it properly first
try:
    # Remove any nulls if it was partially corrupted UTF-16
    raw_text = data.decode('utf-16', errors='ignore')
    if 'apiVersion' not in raw_text:
        # Maybe it's already UTF-8 but has garbage
        raw_text = data.decode('utf-8', errors='ignore')
except:
    raw_text = data.decode('ascii', errors='ignore')

# Keep only printable ASCII and whitespace
clean_text = "".join(c for c in raw_text if ord(c) < 128)

# Find apiVersion
start = clean_text.find('apiVersion:')
if start != -1:
    clean_text = clean_text[start:]
    # Remove the garbage at the end
    end = clean_text.rfind('==') # Base64 usually ends with = or ==
    if end != -1:
        # Find the next newline after the last ==
        next_nl = clean_text.find('\n', end)
        if next_nl != -1:
            clean_text = clean_text[:next_nl+1]
        else:
            clean_text = clean_text[:end+2]

with open(path + '.final', 'w', encoding='utf-8', newline='\n') as f:
    f.write(clean_text)
print("Wrote clean kubeconfig to .final")
