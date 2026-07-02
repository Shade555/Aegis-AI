import os

for root, dirs, files in os.walk('sentinel-backend'):
    if any(x in root for x in ['node_modules', '.venv', '.git', 'dist', '.next', '__pycache__', 'alembic']):
        continue
    for f in files:
        if not f.endswith('.py'): continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        if 'sentinel' in content:
            content = content.replace('sentinel', 'aegis')
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)
print('Done frontend too')
for root, dirs, files in os.walk('sentinel-frontend'):
    if any(x in root for x in ['node_modules', '.venv', '.git', 'dist', '.next', '__pycache__']):
        continue
    for f in files:
        if not (f.endswith('.ts') or f.endswith('.tsx')): continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        if 'sentinel' in content:
            content = content.replace('sentinel', 'aegis')
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)
print('Done!')
