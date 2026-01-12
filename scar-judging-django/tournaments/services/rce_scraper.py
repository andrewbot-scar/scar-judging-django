"""
RobotCombatEvents.com scraper service
Extracts robot images from registration pages
"""

import re
import requests
from bs4 import BeautifulSoup


def scrape_rce_robots(url):
    """
    Scrape robot images from a RobotCombatEvents registration page.
    
    Args:
        url: RobotCombatEvents competition URL
        
    Returns:
        Dict with:
            - success: bool
            - url: Original URL
            - robotCount: Number of robots found
            - robots: List of {name, resourceId, groupId, imageUrl}
    """
    if not url or 'robotcombatevents.com' not in url:
        raise ValueError('Valid RobotCombatEvents URL required')

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        raise Exception(f"Failed to fetch RCE page: {e}")

    soup = BeautifulSoup(html, 'html.parser')
    robots = []

    # Find all table rows
    for row in soup.find_all('tr'):
        # Skip header rows
        if row.find('th'):
            continue

        # Try to find resource link (robot name)
        resource_link = row.find('a', href=re.compile(r'/groups/\d+/resources/\d+'))
        if not resource_link:
            continue

        # Extract IDs from href
        href = resource_link.get('href', '')
        match = re.search(r'/groups/(\d+)/resources/(\d+)', href)
        if not match:
            continue

        group_id = match.group(1)
        resource_id = match.group(2)
        robot_name = resource_link.get_text(strip=True)

        # Try to find image
        img = row.find('img')
        image_url = None

        if img:
            img_src = img.get('src', '')
            
            # Skip RCE logo placeholders
            if 'rcelogo' in img_src.lower() or 'rce_logo' in img_src.lower():
                image_url = None
            elif img_src.startswith('http'):
                image_url = img_src
            elif img_src.startswith('/'):
                # Relative URL
                image_url = f"https://www.robotcombatevents.com{img_src}"

        robots.append({
            'name': robot_name,
            'resourceId': resource_id,
            'groupId': group_id,
            'imageUrl': image_url,
        })

    print(f"Scraped {len(robots)} robots from RCE: {url}")

    return {
        'success': True,
        'url': url,
        'robotCount': len(robots),
        'robots': robots,
    }
