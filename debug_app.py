with open("api/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i in range(2135, 2155):
    if i < len(lines):
        print(f"{i+1}: {repr(lines[i])}")
