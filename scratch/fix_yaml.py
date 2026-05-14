import os
import yaml

path = os.path.expanduser("~/.kube/config")
with open(path, 'rb') as f:
    data = f.read()

# Try to decode and find the end of the YAML
text = data.decode('utf-8', errors='ignore')
# Remove anything that isn't a valid Base64 character in the data blocks
# But easier: just find the last valid character of the YAML
# YAML usually ends with a newline or a specific key.
# In our case, it ends with the client-key-data.

# Use a regex to find the last valid Base64 padding or character
import re
# Find the last occurrence of a typical Base64 footer or end of line
# Actually, let's just use the YAML parser to find where it breaks and truncate there.
try:
    yaml.safe_load(text)
    print("YAML is already valid")
except yaml.YAMLError as exc:
    print(f"YAML Error: {exc}")
    if hasattr(exc, 'problem_mark'):
        mark = exc.problem_mark
        print(f"Error at line {mark.line}, column {mark.column}")
        # Truncate at the problem mark if it's at the end
        lines = text.splitlines()
        if mark.line < len(lines):
            # Try to fix the line
            line = lines[mark.line]
            # Remove non-base64 characters from the end of the line
            line = re.sub(r'[^A-Za-z0-9+/=].*$', '', line)
            lines[mark.line] = line
            # Remove any lines after this if they look like junk
            text = "\n".join(lines[:mark.line+1])
            with open(path + '.fixed2', 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
            print("Wrote fixed2")
