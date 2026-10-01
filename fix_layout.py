with open('style.css', 'r', encoding='utf-8') as f:
    css = f.read()

bad_css = '''/* Corporate UI fixes - hide click hint when login is hidden */
.login-hidden ~ .app-container {
    display: block;
}'''
css = css.replace(bad_css, '')

with open('style.css', 'w', encoding='utf-8') as f:
    f.write(css)

js_path = 'app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

if "document.getElementById('clickHint').style.display = 'none';" not in js:
    js = js.replace("document.getElementById('appScreen').style.display = 'flex';", "document.getElementById('appScreen').style.display = 'flex';\n    if(document.getElementById('clickHint')) document.getElementById('clickHint').style.display = 'none';")

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Layout fixed")
