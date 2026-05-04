import os
import re

router_dir = 'app/routers'
for filename in os.listdir(router_dir):
    if filename.endswith('.py'):
        path = os.path.join(router_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace @router.get("/") with @router.get("")
        new_content = re.sub(r'@router\.(get|post|put|delete)\("/",', r'@router.\1("",', content)
        new_content = re.sub(r'@router\.(get|post|put|delete)\(\'/\',', r'@router.\1(\'\',', new_content)
        
        if content != new_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {filename}")
