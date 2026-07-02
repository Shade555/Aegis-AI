import os

files_to_update = [
    r'DEVELOPMENT.md',
    r'README.md',
    r'sentinel-backend\src\sentinel\main.py',
    r'sentinel-backend\src\sentinel\__init__.py',
    r'sentinel-backend\src\sentinel\application\agent\base.py',
    r'sentinel-backend\src\sentinel\application\agent\templates\report.html.j2',
    r'sentinel-backend\src\sentinel\application\ai\prompts.py',
    r'sentinel-backend\src\sentinel\domain\events.py',
    r'sentinel-backend\src\sentinel\infrastructure\database\models.py',
    r'sentinel-backend\src\sentinel\interface\api\exceptions.py',
    r'sentinel-backend\tests\conftest.py',
    r'sentinel-frontend\src\app\globals.css',
    r'sentinel-frontend\src\app\layout.tsx',
    r'sentinel-frontend\src\app\(auth)\sign-in\[[...sign-in]]\page.tsx',
    r'sentinel-frontend\src\app\(auth)\sign-up\[[...sign-up]]\page.tsx',
    r'sentinel-frontend\src\components\execution\AIAssistantPanel.tsx',
    r'sentinel-frontend\src\components\layout\Footer.tsx',
    r'sentinel-frontend\src\components\layout\Header.tsx'
]

for f in files_to_update:
    if not os.path.exists(f): continue
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace('Sentinel AI', 'Aegis AI')
    content = content.replace('Sentinel', 'Aegis')
    content = content.replace('sentinel', 'aegis')
    content = content.replace('Autonomous Multi-Agent AI Security Engineer', 'Autonomous AI Security Intelligence')
    content = content.replace('Autonomous AI Security Engineer', 'Autonomous AI Security Intelligence')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print('Done!')
