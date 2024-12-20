
import asyncio
import aiohttp
import csv
from datetime import datetime
import sys
from urllib.parse import urlparse
import json
import os

# Create timestamp once for consistent filenames
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
VERIFYPASS_FILE = f'verifypass_domains_{TIMESTAMP}.csv'

# Initialize verifypass CSV file with headers
with open(VERIFYPASS_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Domain', 'Timestamp', 'Status'])

async def save_verifypass_domain(domain, status):
    """Save a domain with verifypass to the dedicated CSV file"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(VERIFYPASS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([domain, current_time, status])
    print(f"✓ VerifyPass detected: {domain}")

async def check_domain(session, domain):
    try:
        # Ensure domain has https://
        if not domain.startswith('http'):
            domain = f'https://{domain}'

        # Check if site is accessible
        async with session.get(domain, timeout=10) as response:
            if response.status != 200:
                return {
                    'domain': domain,
                    'valid': False,
                    'status': response.status,
                    'verifypass': False,
                    'error': f'Invalid status code: {response.status}'
                }

            # Get page content
            html_content = await response.text()
            
            # Check for verifypass indicators
            verifypass_indicators = [
                'verifypass.com',
                'verifypass.js',
                'verifypass-shopify',
                'data-verifypass'
            ]
            
            has_verifypass = any(indicator in html_content.lower() for indicator in verifypass_indicators)
            
            # If verifypass is detected, save it immediately
            if has_verifypass:
                await save_verifypass_domain(domain, response.status)
            
            return {
                'domain': domain,
                'valid': True,
                'status': response.status,
                'verifypass': has_verifypass,
                'error': None
            }

    except asyncio.TimeoutError:
        return {
            'domain': domain,
            'valid': False,
            'status': None,
            'verifypass': False,
            'error': 'Timeout'
        }
    except Exception as e:
        return {
            'domain': domain,
            'valid': False,
            'status': None,
            'verifypass': False,
            'error': str(e)
        }

async def process_domains(domains):
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    ) as session:
        tasks = [check_domain(session, domain) for domain in domains]
        return await asyncio.gather(*tasks)

def load_domains_from_csv(filename):
    domains = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domains.append(row['Domain'])
    return domains

def save_results(results, output_filename):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'domain_check_results_{timestamp}.csv'
    
    with open(output_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Domain', 'Valid', 'Status', 'VerifyPass', 'Error'])
        
        for result in results:
            writer.writerow([
                result['domain'],
                result['valid'],
                result['status'],
                result['verifypass'],
                result['error']
            ])
    
    print(f'\nResults saved to: {output_filename}')

async def main():
    if len(sys.argv) < 2:
        print("Please provide the CSV file path as an argument")
        sys.exit(1)

    csv_file = sys.argv[1]
    print(f"Loading domains from {csv_file}")
    print(f"VerifyPass domains will be saved to: {VERIFYPASS_FILE}")
    
    # Load domains from CSV
    domains = load_domains_from_csv(csv_file)
    total_domains = len(domains)
    print(f"Found {total_domains} domains to check")

    # Process domains in batches to avoid overwhelming the system
    batch_size = 50
    results = []
    
    for i in range(0, total_domains, batch_size):
        batch = domains[i:i + batch_size]
        print(f"\nProcessing batch {i//batch_size + 1} ({len(batch)} domains)")
        
        batch_results = await process_domains(batch)
        results.extend(batch_results)
        
        # Print progress
        valid_sites = sum(1 for r in batch_results if r['valid'])
        verifypass_sites = sum(1 for r in batch_results if r['verifypass'])
        print(f"Batch results: {valid_sites} valid sites, {verifypass_sites} with VerifyPass")
    
    # Save final results
    save_results(results, 'domain_check_results.csv')
    
    # Print summary
    total_valid = sum(1 for r in results if r['valid'])
    total_verifypass = sum(1 for r in results if r['verifypass'])
    print(f"\nFinal Summary:")
    print(f"Total domains processed: {total_domains}")
    print(f"Valid sites: {total_valid}")
    print(f"Sites with VerifyPass: {total_verifypass}")
    print(f"VerifyPass domains saved to: {VERIFYPASS_FILE}")

if __name__ == "__main__":
    asyncio.run(main())