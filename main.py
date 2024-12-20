'''
@author: Dipin Arora
'''
import requests
from bs4 import BeautifulSoup as bs
import time
import asyncio
import aiohttp
import csv
import sys
from datetime import datetime

DOMAIN_ZONE = 'com'
timestamp = time.strftime('%Y%m%d_%H%M%S')
output_filename = f'shopify_domains_{timestamp}.csv'

# Initialize CSV file with header
with open(output_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Page', 'Domain', 'Timestamp'])

async def save_to_csv(domains, page_num):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(output_filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for domain in domains:
            writer.writerow([page_num, domain, current_time])
    print(f'Page {page_num}: Saved {len(domains)} domains')

async def scrape(session, page_num):
    page_domains = []
    async with session.get(
            f'https://onshopify.com/domain-zone/{DOMAIN_ZONE}/{page_num}'
    ) as res:
        if res.status == 200:
            text = await res.text()
            soup = bs(text, features='html.parser')
            for link in soup.find_all(
                    attrs={'class': 'col-lg-4 col-md-4 col-sm-12'}):
                if link.text.strip().endswith(f'.{DOMAIN_ZONE}'):
                    page_domains.append(link.text.strip())
            
            # Save domains from this page immediately
            if page_domains:
                await save_to_csv(page_domains, page_num)
            return page_domains

async def fetch(last_page):
    all_domains = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        print(f'Scraping till page number {last_page}')
        for page_num in range(1, last_page):
            task = asyncio.ensure_future(scrape(session, page_num))
            tasks.append(task)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for domains in results:
            if isinstance(domains, list):  # Only add if not an exception
                all_domains.extend(domains)
    return all_domains

def last_page_finder():
    res = requests.get(f'https://onshopify.com/domain-zone/{DOMAIN_ZONE}/')
    if res.status_code == 200:
        soup = bs(res.text, features='html.parser')
        x = soup.find(attrs={'class': 'pagination'})
        if x is not None:
            return int(x.find_all('li').pop().text)
        else:
            raise Exception(
                'Invalid Domain Zone\nYou can find valid domain at https://onshopify.com/domains'
            )

if __name__ == "__main__":
    t = time.time()
    if len(sys.argv) > 1:
        DOMAIN_ZONE = sys.argv[1]
    print('scraping started')
    if len(sys.argv) > 2:
        last_page = int(sys.argv[2])
        if last_page < 0:
            raise Exception('Last Page cannot be less than 0')
    else:
        last_page = last_page_finder()
    all_domains = asyncio.run(fetch(last_page))
    
    print(f'Total execution time: {time.time() - t:.2f} seconds')
    print(f'Total domains found: {len(all_domains)}')
