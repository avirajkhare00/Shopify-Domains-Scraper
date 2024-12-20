import asyncio
import aiohttp
import csv
from datetime import datetime
import sys
from bs4 import BeautifulSoup
import re
import json

# Create timestamp for output file
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
INDIAN_DOMAINS_FILE = f'indian_shopify_domains_{TIMESTAMP}.csv'

async def save_indian_domain(domain, confidence, indicators, country_code, shop_id):
    """Save a domain identified as Indian to the CSV file"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(INDIAN_DOMAINS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([domain, confidence, indicators, country_code, shop_id, current_time])
    print(f"🇮🇳 Indian site detected: {domain} (Shop ID: {shop_id}, Country: {country_code})")

def extract_shopify_data(html_content):
    """Extract Shopify metadata from the page"""
    data = {
        'country_code': None,
        'shop_id': None,
        'indicators': []
    }
    
    try:
        # Look for Shopify.shop.locale in script tags
        locale_pattern = r'Shopify\.locale\s*=\s*["\']([^"\']+)["\']'
        locale_match = re.search(locale_pattern, html_content)
        if locale_match and 'IN' in locale_match.group(1).upper():
            data['country_code'] = 'IN'
            data['indicators'].append('Shopify locale: IN')

        # Look for shop ID and country in meta tags
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check meta tags
        for meta in soup.find_all('meta'):
            # Check for country in meta tags
            if meta.get('property') == 'og:locale':
                locale = meta.get('content', '')
                if 'IN' in locale.upper():
                    data['country_code'] = 'IN'
                    data['indicators'].append('Meta locale: IN')
            
            # Look for Shopify shop ID
            if meta.get('name') == 'shopify-digital-wallet':
                content = meta.get('content', '')
                if '/shop/' in content:
                    shop_id = content.split('/shop/')[-1].split('/')[0]
                    data['shop_id'] = shop_id
        
        # Check for Shopify.shop object in scripts
        for script in soup.find_all('script'):
            script_text = script.string or ''
            if 'Shopify.shop' in script_text:
                # Try to find shop country
                country_match = re.search(r'Shopify\.shop\s*=\s*({[^}]+})', script_text)
                if country_match:
                    try:
                        shop_data = json.loads(country_match.group(1))
                        if shop_data.get('country_code') == 'IN':
                            data['country_code'] = 'IN'
                            data['indicators'].append('Shopify.shop country: IN')
                    except json.JSONDecodeError:
                        pass

        # Look for currency settings
        currency_patterns = [
            r'currency:\s*["\']INR["\']',
            r'defaultCurrency:\s*["\']INR["\']',
            r'Shopify\.currency\.active\s*=\s*["\']INR["\']'
        ]
        
        for pattern in currency_patterns:
            if re.search(pattern, html_content):
                data['indicators'].append('Currency: INR')
                break

        # Check for Indian address format in templates
        address_indicators = [
            'pin-code',
            'pincode',
            'postal-code-in',
            'india-zip',
            'india-post'
        ]
        
        for indicator in address_indicators:
            if indicator in html_content.lower():
                data['indicators'].append(f'Indian address format: {indicator}')

    except Exception as e:
        print(f"Error extracting Shopify data: {str(e)}")
    
    return data

async def check_domain(session, domain):
    try:
        # Ensure domain has https://
        if not domain.startswith('http'):
            domain = f'https://{domain}'

        # Check if site is accessible
        async with session.get(
            domain, 
            timeout=15,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
        ) as response:
            if response.status != 200:
                return

            # Get page content
            html_content = await response.text()
            
            # Extract Shopify metadata
            shopify_data = extract_shopify_data(html_content)
            
            # If we found Indian indicators in Shopify metadata
            if shopify_data['country_code'] == 'IN' or shopify_data['indicators']:
                confidence = len(shopify_data['indicators']) * 25  # 25% per indicator
                confidence = min(confidence, 100)  # Cap at 100%
                
                if confidence >= 25:  # Save if at least one strong indicator
                    await save_indian_domain(
                        domain,
                        confidence,
                        ', '.join(shopify_data['indicators']),
                        shopify_data['country_code'],
                        shopify_data['shop_id']
                    )

    except Exception as e:
        # Just skip problematic domains
        pass

async def process_domains(domains):
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30)
    ) as session:
        tasks = [check_domain(session, domain) for domain in domains]
        await asyncio.gather(*tasks, return_exceptions=True)

def load_domains_from_csv(filename):
    domains = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domains.append(row['Domain'])
    return domains

# Initialize output CSV file with headers
with open(INDIAN_DOMAINS_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Domain', 'Confidence', 'Indicators', 'Country_Code', 'Shop_ID', 'Timestamp'])

async def main():
    if len(sys.argv) < 2:
        print("Please provide the CSV file path as an argument")
        sys.exit(1)

    csv_file = sys.argv[1]
    print(f"Loading domains from {csv_file}")
    print(f"Indian domains will be saved to: {INDIAN_DOMAINS_FILE}")
    
    # Load domains from CSV
    domains = load_domains_from_csv(csv_file)
    total_domains = len(domains)
    print(f"Found {total_domains} domains to check")

    # Process domains in batches to avoid overwhelming the system
    batch_size = 50
    
    for i in range(0, total_domains, batch_size):
        batch = domains[i:i + batch_size]
        print(f"\nProcessing batch {i//batch_size + 1} ({len(batch)} domains)")
        await process_domains(batch)
        print(f"Completed batch {i//batch_size + 1}")

    print(f"\nProcessing complete! Check {INDIAN_DOMAINS_FILE} for results")

if __name__ == "__main__":
    asyncio.run(main())
