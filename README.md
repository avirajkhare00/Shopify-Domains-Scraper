# Shopify Domains Scraper

A collection of Python scripts for scraping and analyzing Shopify-powered websites. This toolkit provides functionality for discovering Shopify stores, analyzing their characteristics, and detecting specific integrations.

The valid domain zones are here - https://onshopify.com/domains

## Benchmarking
- Processes 7000+ websites in approximately 5 minutes
- Efficient asynchronous processing for fast results

## Scripts

### main.py
The original scraper that:
- Scrapes Shopify domains from onshopify.com by domain zone (e.g., .com, .in)
- Uses asynchronous requests for efficient data collection
- Saves domains to a timestamped CSV file with page numbers
- Usage: `python main.py [domain_zone]` (default: com)

### main2.py
Enhanced version that:
- Reads domains from a CSV file
- Checks domain accessibility and validity
- Detects VerifyPass integration on Shopify stores
- Generates two output files:
  - General results CSV with all domain statuses
  - Specific CSV for domains using VerifyPass
- Usage: `python main2.py input_file.csv`

### script.py
Specialized script for identifying Indian Shopify stores:
- Analyzes Shopify stores for Indian locale indicators
- Extracts Shopify metadata including shop ID and country code
- Uses multiple indicators to determine Indian origin
- Saves results with confidence scores and detection indicators
- Usage: `python script.py input_file.csv`

## Requirements
- Python 3.x
- aiohttp
- asyncio
- beautifulsoup4 (for HTML parsing)
- requests
