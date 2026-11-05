import requests
import json
import re
from datetime import datetime
import xml.sax.saxutils as saxutils

BLOG_FEED_URL = 'https://nilranbow.blogspot.com/feeds/posts/default?alt=json&max-results=150'
OUTPUT_FILE = 'feed.xml'

def parse_iso8601(dt_str):
    """Parse ISO8601 string to RFC 822 format required by RSS 2.0."""
    try:
        # Handles offsets like 2026-11-05T05:00:00.000-08:00
        # Clean fractional seconds if any
        dt_clean = re.sub(r'\.\d+', '', dt_str)
        # Parse timezone offset
        if '+' in dt_clean[10:] or '-' in dt_clean[10:]:
            # Python 3.7+ fromisoformat handles offsets
            dt = datetime.fromisoformat(dt_clean)
        else:
            dt = datetime.strptime(dt_clean.replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
        return dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
    except Exception:
        return datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

def clean_html(raw_html):
    """Extract clean text excerpt from HTML, removing style and script blocks."""
    no_style = re.sub(r'<(style|script)[^>]*>.*?</\1>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', no_style)
    clean = ' '.join(clean.split())
    if len(clean) > 350:
        clean = clean[:347] + '...'
    return clean

def build_rss_feed():
    print(f"Fetching posts from {BLOG_FEED_URL}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    r = requests.get(BLOG_FEED_URL, headers=headers)
    if r.status_code != 200:
        raise RuntimeError(f"Failed to fetch Blogger JSON: status {r.status_code}")
    
    data = r.json()
    feed = data.get('feed', {})
    entries = feed.get('entry', [])
    print(f"Total entries found: {len(entries)}")

    items_xml = []
    
    for e in entries:
        title = e.get('title', {}).get('$t', '').strip()
        links = e.get('link', [])
        post_url = None
        for l in links:
            if l.get('rel') == 'alternate':
                post_url = l.get('href')
                break
        
        if not post_url:
            continue
            
        published_str = e.get('published', {}).get('$t', '')
        rfc_date = parse_iso8601(published_str)
        
        content = e.get('content', {}).get('$t', '')
        summary = e.get('summary', {}).get('$t', '')
        
        raw_text = summary if summary else content
        snippet = clean_html(raw_text)
        
        # Find images in content
        imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
        first_img = None
        if imgs:
            first_img = imgs[0]
            # Upgrade thumbnail resolutions to full 1600px / 1280px
            first_img = re.sub(r'/s\d+(-c)?/', '/s1600/', first_img)
            first_img = re.sub(r'/w\d+-h\d+/', '/s1600/', first_img)
        elif 'media$thumbnail' in e:
            thumb_url = e['media$thumbnail'].get('url', '')
            first_img = re.sub(r'/s\d+(-c)?/', '/s1600/', thumb_url)
            
        if not first_img:
            # Skip items without images because Pinterest requires images
            continue
            
        # Determine image MIME type
        img_type = "image/png"
        if first_img.lower().endswith(('.jpg', '.jpeg')):
            img_type = "image/jpeg"
        elif first_img.lower().endswith('.webp'):
            img_type = "image/webp"

        escaped_title = saxutils.escape(title)
        escaped_url = saxutils.escape(post_url)
        escaped_img = saxutils.escape(first_img)
        
        item_block = f"""    <item>
      <title>{escaped_title}</title>
      <link>{escaped_url}</link>
      <guid isPermaLink="true">{escaped_url}</guid>
      <pubDate>{rfc_date}</pubDate>
      <description><![CDATA[<p><img src="{first_img}" alt="{title}" /></p><p>{snippet}</p>]]></description>
      <content:encoded><![CDATA[<p><img src="{first_img}" alt="{title}" /></p><p>{snippet}</p>]]></content:encoded>
      <enclosure url="{escaped_img}" type="{img_type}" length="150000" />
      <media:content url="{escaped_img}" medium="image" type="{img_type}" width="1280" height="720">
        <media:title>{escaped_title}</media:title>
        <media:description>{saxutils.escape(snippet)}</media:description>
      </media:content>
      <media:thumbnail url="{escaped_img}" width="1280" height="720" />
    </item>"""
        items_xml.append(item_block)
        
    now_rfc = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:content="http://purl.org/rss/1.0/modules/content/" 
     xmlns:media="http://search.yahoo.com/mrss/" 
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>NilRanbow - AI &amp; Tech Trends</title>
    <link>https://nilranbow.blogspot.com/</link>
    <description>Daily deep dives into the future of artificial intelligence, creative technology, and practical tools.</description>
    <language>en-us</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <atom:link href="https://nilranbow.blogspot.com/feeds/posts/default?alt=rss" rel="self" type="application/rss+xml" />
{chr(10).join(items_xml)}
  </channel>
</rss>
"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(xml_content)
        
    print(f"Successfully generated {OUTPUT_FILE} with {len(items_xml)} image-enriched items.")

if __name__ == '__main__':
    build_rss_feed()
