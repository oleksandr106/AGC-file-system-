import os

def update_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

css_replacements = [
    ('--bg-primary: #f8fafc;', '--bg-primary: #f1f5f9;'),
    ('--bg-card: rgba(255, 255, 255, 0.9);', '--bg-card: #ffffff;'),
    ('--bg-sidebar: rgba(255, 255, 255, 0.95);', '--bg-sidebar: #ffffff;'),
    ('--border-focus: rgba(99, 143, 255, 0.4);', '--border-focus: #2563eb;'),
    ('--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);', '--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);'),
    ('--shadow-md: 0 4px 20px rgba(0, 0, 0, 0.08);', '--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.05);'),
    ('--shadow-lg: 0 10px 40px rgba(0, 0, 0, 0.1);', '--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.05);'),
    ('--radius-sm: 8px;', '--radius-sm: 4px;'),
    ('--radius-md: 12px;', '--radius-md: 6px;'),
    ('--radius-lg: 16px;', '--radius-lg: 8px;'),
    ('--radius-xl: 20px;', '--radius-xl: 12px;'),
    ('--accent-blue: #638fff;', '--accent-blue: #3b82f6;'),
    ('--accent-blue-subtle: rgba(99, 143, 255, 0.1);', '--accent-blue-subtle: rgba(59, 130, 246, 0.1);'),
    ('--accent-purple: #a78bfa;', '--accent-purple: #8b5cf6;'),
    ('--accent-purple-subtle: rgba(167, 139, 250, 0.1);', '--accent-purple-subtle: rgba(139, 92, 246, 0.1);'),
    ('--gradient-login: linear-gradient(135deg, #e0e7ff 0%, #f0e6ff 50%, #e0f2fe 100%);', '--gradient-login: #f1f5f9;')
]
update_file('style.css', css_replacements)

html_replacements = [('ph ', 'ph-fill ')]
update_file('index.html', html_replacements)
update_file('app.js', html_replacements)

print("Files updated successfully")
