import re

with open('app.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix document.getElementById(...).property
content = re.sub(r'document\.getElementById\(([\'"][^\'"]+[\'"])\)\.value', r'(document.getElementById(\1) as HTMLInputElement).value', content)
content = re.sub(r'document\.getElementById\(([\'"][^\'"]+[\'"])\)\.files', r'(document.getElementById(\1) as HTMLInputElement).files', content)
content = re.sub(r'document\.getElementById\(([\'"][^\'"]+[\'"])\)\.reset\(\)', r'(document.getElementById(\1) as HTMLFormElement).reset()', content)
content = re.sub(r'document\.getElementById\(([\'"][^\'"]+[\'"])\)\.disabled', r'(document.getElementById(\1) as HTMLButtonElement).disabled', content)

# Fix variable properties (e.g. input.value) by casting them inline if they fail.
# It's better to just add "any" to the types in the function signatures or use specific casting for typical names
content = re.sub(r'(\b\w+Input\b)\.value', r'(\1 as HTMLInputElement).value', content)
content = re.sub(r'(\b\w+Input\b)\.files', r'(\1 as HTMLInputElement).files', content)
content = re.sub(r'(\b\w+Btn\b)\.disabled', r'(\1 as HTMLButtonElement).disabled', content)
content = re.sub(r'(\be\.target\b)\.value', r'(\1 as HTMLInputElement).value', content)

# Write back
with open('app.ts', 'w', encoding='utf-8') as f:
    f.write(content)
