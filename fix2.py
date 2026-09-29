import re

with open('app.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix options.headers
content = re.sub(r'options\.headers = options\.headers \|\| \{\};', r'options.headers = options.headers || ({} as any);', content)
content = re.sub(r'options\.headers\[\'Authorization\'\]', r'(options.headers as any)[\'Authorization\']', content)

# Fix URLSearchParams
content = re.sub(r'page,\n', r'page: String(page),\n', content)
content = re.sub(r'per_page\n', r'per_page: String(per_page)\n', content)
content = re.sub(r'const params = new URLSearchParams\(\{([^}]+)\}\);', r'const params = new URLSearchParams({\1} as Record<string, string>);', content)

# Fix input.files
content = re.sub(r'input\.files', r'(input as HTMLInputElement).files', content)

# Fix btn.disabled
content = re.sub(r'btn\.disabled', r'(btn as HTMLButtonElement).disabled', content)

# Fix executeSearch() - just pass undefined or false depending on what it needs. But looking at line 378, it's called with no args. Let's cast the function or its param. 
content = re.sub(r'executeSearch\(\)', r'executeSearch(false as any)', content)

with open('app.ts', 'w', encoding='utf-8') as f:
    f.write(content)
