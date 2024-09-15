import json
import os
import math
from jinja2 import Environment, FileSystemLoader
import re
import html

TIPS_PER_PAGE = 15

def slugify(text):
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'\s+', '-', slug)
    return slug

def format_content(content):
    def replace_code_block(match):
        code = html.escape(match.group(1).strip())
        lines = code.split('\n')
        formatted_lines = [f'<span class="line">{line}</span>' for line in lines]
        formatted_code = '\n'.join(formatted_lines)
        return f'<pre><code class="language-php">{formatted_code}</code></pre>'

    # Replace ```php...``` blocks
    content = re.sub(r'```php(.*?)```', replace_code_block, content, flags=re.DOTALL)

    # Replace inline `code`
    content = re.sub(r'`([^`]+)`', lambda m: f'<code>{html.escape(m.group(1))}</code>', content)

    # Replace newlines with <br> tags, but not within <pre> blocks
    content = re.sub(r'(?<!>)\n(?!<)(?![^<]*</pre>)', '<br>', content)

    return content

# Load the tips
with open('tips.json', 'r') as f:
    tips = json.load(f)

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader('templates'))
tip_template = env.get_template('tip_template.html')
index_template = env.get_template('index_template.html')

# Create directories if they don't exist
os.makedirs('tips', exist_ok=True)
os.makedirs('pages', exist_ok=True)

# Generate individual tip pages
for tip in tips:
    slug = slugify(tip['summary'])
    tip_dir = f'tips/{tip["id"]}-{slug}'
    os.makedirs(tip_dir, exist_ok=True)

# Generate paginated index pages
total_pages = math.ceil(len(tips) / TIPS_PER_PAGE)

for page in range(1, total_pages + 1):
    start_index = (page - 1) * TIPS_PER_PAGE
    end_index = start_index + TIPS_PER_PAGE
    page_tips = tips[start_index:end_index]

    output = index_template.render(
        tips=page_tips,
        current_page=page,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages
    )

    if page == 1:
        with open('index.html', 'w') as f:
            f.write(output)

    with open(f'pages/page_{page}.html', 'w') as f:
        f.write(output)

print(f"Generated {total_pages} paginated index pages.")

# Update the tips.json file with permalinks
with open('tips.json', 'w') as f:
    json.dump(tips, f, indent=2)

print("Updated tips.json with permalinks.")