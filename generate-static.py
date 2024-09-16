import json
import os
import math
from jinja2 import Environment, FileSystemLoader
import re
import html
from datetime import datetime
import markdown
from bs4 import BeautifulSoup

TIPS_PER_PAGE = 10
MAX_VISIBLE_PAGES = 5
BASE_URL = 'https://1000phptips.com'
SITE_NAME = '1000 PHP Tips - Quick tips and Courses for PHP Developers'

def slugify(text):
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'\s+', '-', slug)
    return slug

def generate_meta_description(content, max_length=160):
    # Remove HTML tags
    text = BeautifulSoup(content, 'html.parser').get_text()

    # Remove special characters and extra spaces
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Truncate to the specified max_length
    if len(text) > max_length:
        text = text[:max_length-3] + '...'

    return text

def format_content(content):
    # Convert Markdown to HTML
    html_content = markdown.markdown(content, extensions=['fenced_code', 'codehilite'])

    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all code blocks and add line numbers
    for pre in soup.find_all('pre'):
        code = pre.find('code')
        if code and code.string:
            lines = code.string.split('\n')
            formatted_lines = [f'<span class="line">{line}</span>' for line in lines]
            code.clear()
            code.extend(BeautifulSoup('\n'.join(formatted_lines), 'html.parser'))
        if code:
            if 'class' in code.attrs:
                code['class'].append('language-php')
            else:
                code['class'] = ['language-php']

    return str(soup)

def format_summary(summary):
    # Convert Markdown to HTML for summary
    html_summary = markdown.markdown(summary)

    # Remove paragraph tags that Markdown might have added
    html_summary = re.sub(r'^<p>(.*)</p>$', r'\1', html_summary)

    return html_summary

def get_pagination_range(current_page, total_pages):
    if total_pages <= MAX_VISIBLE_PAGES:
        return range(1, total_pages + 1)

    start = max(current_page - MAX_VISIBLE_PAGES // 2, 1)
    end = min(start + MAX_VISIBLE_PAGES - 1, total_pages)

    if end - start < MAX_VISIBLE_PAGES - 1:
        start = max(end - MAX_VISIBLE_PAGES + 1, 1)

    return range(start, end + 1)

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

# Prepare sitemap entries
sitemap_entries = []

# Generate individual tip pages
tip_pages_generated = 0
for tip in tips:
    slug = slugify(tip['summary'])
    tip_dir = f'tips/{tip["id"]}-{slug}'
    os.makedirs(tip_dir, exist_ok=True)

    # Format the content
    tip['formatted_content'] = format_content(tip['content'])

    # Format the summary
    tip['formatted_summary'] = format_summary(tip['summary'])

    # Generate meta description
    tip['meta_description'] = generate_meta_description(tip['formatted_content'])

    # Generate the HTML content
    output = tip_template.render(
        tip=tip,
        site_name=SITE_NAME,
        canonical_url=f"{BASE_URL}/tips/{tip['id']}-{slug}/",
        page_title=f"{tip['summary']} - {SITE_NAME}"  # Specific title for tip pages
    )

    # Write the HTML file
    with open(f'{tip_dir}/index.html', 'w') as f:
        f.write(output)

    # Update the tip with its permalink
    tip['permalink'] = f'/tips/{tip["id"]}-{slug}/'

    # Add entry to sitemap
    sitemap_entries.append({
        'loc': f"{BASE_URL}{tip['permalink']}",
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'monthly',
        'priority': '0.8'
    })

    tip_pages_generated += 1

print(f"Generated {tip_pages_generated} individual tip pages.")

# Generate paginated index pages
total_pages = math.ceil(len(tips) / TIPS_PER_PAGE)

for page in range(1, total_pages + 1):
    start_index = (page - 1) * TIPS_PER_PAGE
    end_index = start_index + TIPS_PER_PAGE
    page_tips = tips[start_index:end_index]

    # Determine the appropriate title for the page
    if page == 1:
        page_title = SITE_NAME  # Home page title
    else:
        page_title = f"Page {page} - {SITE_NAME}"  # Paginated pages title

    output = index_template.render(
        tips=page_tips,
        current_page=page,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages,
        pagination_range=get_pagination_range(page, total_pages),
        site_name=SITE_NAME,
        canonical_url=f"{BASE_URL}/{'pages/' + str(page) + '/' if page > 1 else ''}",
        meta_description=f"Page {page} of 1000 PHP Tips - Discover essential PHP programming tips and best practices.",
        page_title=page_title
    )

    if page == 1:
        with open('index.html', 'w') as f:
            f.write(output)
        # Add homepage to sitemap
        sitemap_entries.append({
            'loc': BASE_URL,
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': 'daily',
            'priority': '1.0'
        })
    else:
        os.makedirs(f'pages/{page}', exist_ok=True)
        with open(f'pages/{page}/index.html', 'w') as f:
            f.write(output)
        # Add paginated pages to sitemap
        sitemap_entries.append({
            'loc': f"{BASE_URL}/pages/{page}/",
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '0.7'
        })

print(f"Generated {total_pages} paginated index pages.")

# Update the tips.json file with permalinks
with open('tips.json', 'w') as f:
    json.dump(tips, f, indent=2)

print("Updated tips.json with permalinks.")

# Generate sitemap.xml
sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

for entry in sitemap_entries:
    sitemap_content += '  <url>\n'
    for key, value in entry.items():
        sitemap_content += f'    <{key}>{value}</{key}>\n'
    sitemap_content += '  </url>\n'

sitemap_content += '</urlset>'

with open('sitemap.xml', 'w') as f:
    f.write(sitemap_content)

print("Generated sitemap.xml")

# Generate robots.txt
robots_content = f"""User-agent: *
Allow: /
Sitemap: {BASE_URL}/sitemap.xml
"""

with open('robots.txt', 'w') as f:
    f.write(robots_content)

print("Generated robots.txt")

print(f"Total pages generated: {tip_pages_generated + total_pages}")
print("Generation complete!")