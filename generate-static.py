import json
import os
from jinja2 import Environment, FileSystemLoader
import re

def slugify(text):
    # Convert to lowercase and remove non-word characters
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    return slug

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
    # Create a slug from the summary
    slug = slugify(tip['summary'])

    # Create a directory for this tip
    tip_dir = f'tips/{tip["id"]}-{slug}'
    os.makedirs(tip_dir, exist_ok=True)

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