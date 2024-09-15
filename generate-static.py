import json
import os
from jinja2 import Environment, FileSystemLoader
import re
import html

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
template = env.get_template('tip_template.html')

# Create a directory for the static pages if it doesn't exist
os.makedirs('tips', exist_ok=True)

# Generate a static page for each tip
for tip in tips:
    slug = slugify(tip['summary'])
    tip_dir = f'tips/{tip["id"]}-{slug}'
    os.makedirs(tip_dir, exist_ok=True)

    # Format the content
    tip['formatted_content'] = format_content(tip['content'])

    # Generate the HTML content
    output = template.render(tip=tip)

    # Write the HTML file
    with open(f'{tip_dir}/index.html', 'w') as f:
        f.write(output)

    # Update the tip with its permalink
    tip['permalink'] = f'/tips/{tip["id"]}-{slug}/'

print(f"Generated {len(tips)} static tip pages.")

# Generate the index page
index_template = env.get_template('index_template.html')
index_output = index_template.render(tips=tips)
with open('index.html', 'w') as f:
    f.write(index_output)

print("Generated index page.")

# Update the tips.json file with permalinks
with open('tips.json', 'w') as f:
    json.dump(tips, f, indent=2)

print("Updated tips.json with permalinks.")