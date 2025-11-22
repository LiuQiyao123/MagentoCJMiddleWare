import os
import re
import html

def html_to_markdown(content):
    # Extract main content
    match = re.search(r'<div class="theme-default-content content__default">(.*?)</div>\s*<footer', content, re.DOTALL)
    if match:
        content = match.group(1)
    
    # Decode HTML entities
    content = html.unescape(content)
    
    # Headers
    content = re.sub(r'<h1.*?>(.*?)</h1>', r'# \1\n', content)
    content = re.sub(r'<h2.*?>(.*?)</h2>', r'## \1\n', content)
    content = re.sub(r'<h3.*?>(.*?)</h3>', r'### \1\n', content)
    content = re.sub(r'<h4.*?>(.*?)</h4>', r'#### \1\n', content)
    
    # Links (remove anchors inside headers first)
    content = re.sub(r'<a href="#.*?" class="header-anchor">#</a>', '', content)
    content = re.sub(r'<a href="(.*?)".*?>(.*?)</a>', r'[\2](\1)', content)
    
    # Code blocks
    content = re.sub(r'<div class="language- extra-class"><pre class="language-text"><code>(.*?)</code></pre></div>', r'```\n\1\n```\n', content, flags=re.DOTALL)
    
    # Tables (Simplified conversion)
    def parse_table(match):
        table_html = match.group(0)
        rows = re.findall(r'<tr.*?>(.*?)</tr>', table_html, re.DOTALL)
        md_table = []
        for i, row in enumerate(rows):
            cols = re.findall(r'<t[dh].*?>(.*?)</t[dh]>', row, re.DOTALL)
            cols = [re.sub(r'<.*?>', '', c).strip() for c in cols]
            md_table.append('| ' + ' | '.join(cols) + ' |')
            if i == 0:
                md_table.append('| ' + ' | '.join(['---'] * len(cols)) + ' |')
        return '\n'.join(md_table) + '\n'

    content = re.sub(r'<table.*?>.*?</table>', parse_table, content, flags=re.DOTALL)
    
    # Paragraphs and breaks
    content = re.sub(r'<p>(.*?)</p>', r'\1\n\n', content)
    content = re.sub(r'<br\s*/?>', '\n', content)
    
    # Lists
    content = re.sub(r'<li>(.*?)</li>', r'- \1\n', content)
    content = re.sub(r'<ul>(.*?)</ul>', r'\1\n', content, flags=re.DOTALL)
    
    # Blockquotes
    content = re.sub(r'<blockquote>(.*?)</blockquote>', r'> \1\n', content, flags=re.DOTALL)
    
    # Clean up remaining tags
    content = re.sub(r'<.*?>', '', content)
    
    # Fix multiple newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content

files = ['auth.html', 'shopping.html', 'product.html', 'error_codes.html']
output_file = 'CJ_API_DOCS.md'

with open(output_file, 'w', encoding='utf-8') as out:
    out.write('# CJ Dropshipping API Documentation\n\n')
    out.write('> Auto-generated from official documentation\n\n')
    
    for fname in files:
        if os.path.exists(fname):
            print(f"Processing {fname}...")
            with open(fname, 'r', encoding='utf-8') as f:
                raw_html = f.read()
                markdown = html_to_markdown(raw_html)
                out.write(markdown)
                out.write('\n\n---\n\n')
        else:
            print(f"Warning: {fname} not found")

print(f"Documentation generated at {output_file}")

