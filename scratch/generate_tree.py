import os

def generate_tree(dir_path, f, prefix=''):
    ignore_dirs = {'.git', 'venv', 'node_modules', '__pycache__', '.pytest_cache', '.ruff_cache', '.github', 'dist', 'build', '.vscode', '.idea', 'coverage'}
    
    try:
        entries = os.listdir(dir_path)
    except PermissionError:
        return
        
    entries.sort()
    
    filtered_entries = []
    for entry in entries:
        if entry in ignore_dirs:
            continue
        filtered_entries.append(entry)
        
    for i, entry in enumerate(filtered_entries):
        path = os.path.join(dir_path, entry)
        is_last = i == (len(filtered_entries) - 1)
        
        connector = '└── ' if is_last else '├── '
        f.write(f'{prefix}{connector}{entry}\n')
        
        if os.path.isdir(path):
            new_prefix = prefix + ('    ' if is_last else '│   ')
            generate_tree(path, f, new_prefix)

if __name__ == '__main__':
    with open('project_structure.txt', 'w', encoding='utf-8') as f:
        f.write('Stock-Market-Analysis/\n')
        generate_tree('.', f)
