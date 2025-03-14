#!/usr/bin/env python3
"""
Documentation Downloader 📚
A friendly tool to download and convert web documentation to Markdown format.
Author: Your Name
License: MIT
"""

import os
import time
import logging
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin, unquote
import html2text
import requests
from bs4 import BeautifulSoup
from slugify import slugify
from tqdm import tqdm
import validators
import argparse
import re
from requests.exceptions import RequestException
import robotexclusionrulesparser

# ASCII Art Banner for a nice welcome
BANNER = """
╔═══════════════════════════════════════════╗
║     Documentation Downloader v1.0         ║
║         Convert Docs to Markdown          ║
╚═══════════════════════════════════════════╝
"""

# Configure logging with both file and console output
class WinCompatibleLogger:
    """Custom logger that handles emoji encoding on Windows"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # File handler - uses UTF-8 encoding
        file_handler = logging.FileHandler('crawler.log', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Console handler - strips emojis on Windows if needed
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(console_handler)

    def _format_msg(self, msg):
        """Strip emojis if on Windows cmd/powershell"""
        if sys.platform == 'win32' and not os.environ.get('WT_SESSION'):  # Not Windows Terminal
            return ''.join(char for char in msg if ord(char) < 0x10000)
        return msg

    def info(self, msg):
        self.logger.info(self._format_msg(msg))

    def error(self, msg):
        self.logger.error(self._format_msg(msg))

    def debug(self, msg):
        self.logger.debug(self._format_msg(msg))

    def warning(self, msg):
        self.logger.warning(self._format_msg(msg))

logger = WinCompatibleLogger()

class DocumentationCrawler:
    """
    A friendly documentation crawler that converts web documentation to Markdown.
    Supports both sitemap-based and recursive crawling methods.
    """
    
    def __init__(self, base_url, output_dir, delay=1, respect_robots=True, max_pages=None):
        """Initialize the crawler with user-provided configuration."""
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.visited_urls = set()
        self.pending_urls = set()
        self.respect_robots = respect_robots
        self.max_pages = max_pages
        
        # Set up a session for better performance
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Documentation Downloader - A Friendly Web Crawler (https://github.com/yourusername/doc-downloader)'
        })
        
        # Configure robots.txt parser if enabled
        self.robots_parser = None
        if self.respect_robots:
            self._setup_robots_parser()
        
        # Configure HTML to Markdown converter
        self.converter = html2text.HTML2Text()
        self.configure_converter()
        
    def _setup_robots_parser(self):
        """Setup and load robots.txt parser"""
        try:
            robots_url = urljoin(self.base_url, "/robots.txt")
            self.robots_parser = robotexclusionrulesparser.RobotExclusionRulesParser()
            robots_content = requests.get(robots_url, timeout=10).text
            self.robots_parser.parse(robots_content)
            logger.info(f"Loaded robots.txt from {robots_url}")
        except Exception as e:
            logger.warning(f"Could not load robots.txt: {e}. Continuing without robots.txt rules.")
            self.robots_parser = None
            
    def configure_converter(self):
        """Configure HTML to Markdown converter for optimal output."""
        self.converter.ignore_links = False
        self.converter.ignore_images = False
        self.converter.ignore_emphasis = False
        self.converter.body_width = 0  # Don't wrap text
        self.converter.protect_links = True
        self.converter.unicode_snob = True  # Use Unicode instead of ASCII
        self.converter.wrap_links = False   # Don't wrap links
        
    def create_output_directory(self):
        """Create the output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {self.output_dir}")

    def is_allowed_by_robots(self, url):
        """Check if URL is allowed by robots.txt"""
        if not self.respect_robots or not self.robots_parser:
            return True
        user_agent = "Documentation Downloader"  # Use the same user agent as in session
        return self.robots_parser.is_allowed(user_agent, url)

    def is_valid_doc_url(self, url):
        """Check if a URL is valid and belongs to the documentation domain."""
        try:
            if not validators.url(url):
                return False
            parsed = urlparse(url)
            
            # Check if URL is allowed by robots.txt
            if not self.is_allowed_by_robots(url):
                return False
                
            # Check if URL belongs to the same domain and isn't a file/asset
            return (parsed.netloc == self.base_domain and
                   not any(url.lower().endswith(ext) for ext in [
                       '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip',
                       '.css', '.js', '.ico', '.xml', '.json', '.svg',
                       '.woff', '.woff2', '.ttf', '.eot'
                   ]) and
                   '#' not in url)  # Avoid anchor links that point to same page
        except Exception as e:
            logger.debug(f"URL validation error for {url}: {e}")
            return False

    def extract_links(self, soup, current_url):
        """Extract valid documentation links from HTML content."""
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Skip empty hrefs and javascript links
            if not href or href.startswith('javascript:'):
                continue
                
            absolute_url = urljoin(current_url, href)
            if self.is_valid_doc_url(absolute_url):
                links.add(absolute_url)
        return links

    def crawl_recursive(self):
        """Crawl documentation recursively by following links."""
        try:
            self.create_output_directory()
            self.pending_urls.add(self.base_url)
            
            with tqdm(desc="Downloading documentation") as pbar:
                while self.pending_urls and (self.max_pages is None or len(self.visited_urls) < self.max_pages):
                    url = self.pending_urls.pop()
                    if url in self.visited_urls:
                        continue
                        
                    self.visited_urls.add(url)
                    title, content, new_links = self.get_page_content(url)
                    
                    if title and content:
                        self.save_markdown(title, content, url)
                        # Add new links to pending_urls
                        new_links = {link for link in new_links 
                                   if link not in self.visited_urls and link not in self.pending_urls}
                        self.pending_urls.update(new_links)
                        pbar.update(1)
                        pbar.set_postfix({"Pages": len(self.visited_urls),
                                        "Pending": len(self.pending_urls)})
                        time.sleep(self.delay)
            
            logger.info(f"Completed! Downloaded {len(self.visited_urls)} pages")
                    
        except Exception as e:
            logger.error(f"Crawling failed: {e}")
            raise

    def crawl_sitemap(self, sitemap_url):
        """Crawl documentation using sitemap.xml."""
        try:
            self.create_output_directory()
            logger.info("Fetching sitemap...")
            
            response = self.session.get(sitemap_url)
            response.raise_for_status()
            
            # Handle both XML sitemaps and sitemap indexes
            root = ET.fromstring(response.content)
            namespace = ''
            if '}' in root.tag:
                namespace = root.tag.split('}')[0] + '}'
            
            urls = []
            
            # Check if this is a sitemap index
            is_sitemap_index = root.tag == f"{namespace}sitemapindex"
            
            if is_sitemap_index:
                # Process each sitemap in the index
                sitemaps = []
                for sitemap in root.findall(f'.//{namespace}sitemap'):
                    loc_elem = sitemap.find(f'{namespace}loc')
                    if loc_elem is not None:
                        sitemaps.append(loc_elem.text)
                
                logger.info(f"Found sitemap index with {len(sitemaps)} sitemaps")
                
                # Process each sitemap
                for sitemap_url in sitemaps:
                    try:
                        logger.info(f"Fetching sitemap: {sitemap_url}")
                        sm_response = self.session.get(sitemap_url)
                        sm_response.raise_for_status()
                        
                        sm_root = ET.fromstring(sm_response.content)
                        sm_namespace = ''
                        if '}' in sm_root.tag:
                            sm_namespace = sm_root.tag.split('}')[0] + '}'
                        
                        for url in sm_root.findall(f'.//{sm_namespace}url'):
                            loc = url.find(f'{sm_namespace}loc')
                            if loc is not None and self.base_domain in loc.text:
                                if self.is_valid_doc_url(loc.text):
                                    urls.append(loc.text)
                    except Exception as e:
                        logger.error(f"Error processing sitemap {sitemap_url}: {e}")
            else:
                # Regular sitemap processing
                for url in root.findall(f'.//{namespace}url'):
                    loc = url.find(f'{namespace}loc')
                    if loc is not None and self.base_domain in loc.text:
                        if self.is_valid_doc_url(loc.text):
                            urls.append(loc.text)
            
            if not urls:
                logger.error("No URLs found in sitemap that match the base URL")
                raise ValueError("No matching URLs found in sitemap")
            
            logger.info(f"Found {len(urls)} pages to process")
            
            # Limit the number of pages if max_pages is set
            if self.max_pages and len(urls) > self.max_pages:
                urls = urls[:self.max_pages]
                logger.info(f"Limiting to {self.max_pages} pages")
            
            for url in tqdm(urls, desc="Downloading documentation"):
                title, content, _ = self.get_page_content(url)
                if title and content:
                    self.save_markdown(title, content, url)
                    time.sleep(self.delay)
                    
        except Exception as e:
            logger.error(f"Sitemap crawling failed: {e}")
            raise
            
    def get_page_content(self, url):
        """
        Fetch and extract the main content from a documentation page.
        Returns tuple of (title, content, links)
        """
        try:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove navigation, footer, and other non-content elements
            for element in soup.select('nav, footer, script, style, header, .header, .footer, .navigation, .sidebar, .menu, .comments'):
                element.decompose()
                
            # Extract title
            title = soup.title.string if soup.title else urlparse(url).path
            # Clean up the title
            if title:
                title = re.sub(r'\s+', ' ', title).strip()
            
            # Extract main content (adjust selector based on the site's structure)
            main_content = soup.select_one('main, article, .content, #content, .documentation, .doc-content, .markdown-body')
            if not main_content:
                main_content = soup
                
            # Extract links for recursive crawling
            links = self.extract_links(main_content, url)
                
            # Convert to markdown with proper error handling
            try:
                markdown_content = self.converter.handle(str(main_content))
                # Clean up the markdown content
                markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)  # Remove excessive newlines
                return title, markdown_content, links
            except Exception as e:
                logger.error(f"Markdown conversion error for {url}: {e}")
                return title, f"Error converting content: {e}\n\nOriginal URL: {url}", links
            
        except RequestException as e:
            logger.error(f"Failed to fetch page {url}: {e}")
            return None, None, set()
            
    def save_markdown(self, title, content, url):
        """Save the converted content as a markdown file."""
        try:
            # Create a filename from the URL path
            path_parts = urlparse(url).path.strip('/').split('/')
            filename = slugify(path_parts[-1] if path_parts else title)
            
            if not filename:
                filename = 'index'
            
            if not filename.endswith('.md'):
                filename += '.md'
                
            # Create subdirectories based on URL path
            if len(path_parts) > 1:
                subdir = self.output_dir.joinpath(*path_parts[:-1])
                subdir.mkdir(parents=True, exist_ok=True)
                filepath = subdir / filename
            else:
                filepath = self.output_dir / filename
            
            # Add metadata header
            metadata = f"""---
title: {title}
source_url: {url}
date_downloaded: {time.strftime('%Y-%m-%d %H:%M:%S')}
---

"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(metadata + content)
            logger.debug(f"Saved: {filepath}")
            return True
        except IOError as e:
            logger.error(f"Failed to save file {filepath}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error saving markdown for {url}: {e}")
            return False

def verify_url_accessibility(url):
    """Verify that a URL is accessible."""
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 405:  # Method not allowed, try GET instead
            response = requests.get(url, timeout=10, stream=True)
            response.close()  # Don't download the whole content
        return 200 <= response.status_code < 400
    except Exception as e:
        logger.debug(f"URL accessibility check failed for {url}: {e}")
        return False

def get_command_line_args():
    """Parse command line arguments for non-interactive use."""
    parser = argparse.ArgumentParser(
        description='Download web documentation and convert to Markdown'
    )
    parser.add_argument('--url', type=str, help='Base URL of the documentation')
    parser.add_argument('--output', type=str, default='markdown_docs', help='Output directory')
    parser.add_argument('--method', type=str, choices=['auto', 'recursive', 'sitemap'], 
                       default='auto', help='Crawling method')
    parser.add_argument('--sitemap', type=str, help='Custom sitemap URL')
    parser.add_argument('--delay', type=float, default=1.0, 
                       help='Delay between requests in seconds')
    parser.add_argument('--max-pages', type=int, help='Maximum number of pages to download')
    parser.add_argument('--no-robots', action='store_true', 
                       help='Ignore robots.txt restrictions')
    
    args = parser.parse_args()
    return args

def get_user_input():
    """Get documentation URL and other settings from the user."""
    print(BANNER)
    print("\nWelcome to Documentation Downloader!")
    print("This tool will help you convert web documentation to Markdown format.\n")
    
    while True:
        base_url = input("Enter the base documentation URL (e.g., https://docs.example.com): ").strip()
        if base_url:
            if not base_url.startswith(('http://', 'https://')):
                base_url = 'https://' + base_url
            if not validators.url(base_url):
                print("Please enter a valid URL")
                continue
            break
        print("Please enter a valid URL")
    
    # Ask user for crawling method
    sitemap_url = None
    while True:
        print("\nChoose crawling method:")
        print("1. Auto-detect sitemap.xml")
        print("2. Recursive crawling (follows links)")
        print("3. Enter custom sitemap URL")
        
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == '1':
            # Try common sitemap locations
            sitemap_locations = [
                '/sitemap.xml',
                '/sitemap_index.xml',
                '/wp-sitemap.xml',  # WordPress
                '/sitemap/sitemap.xml',
                '/sitemaps/sitemap.xml'
            ]
            
            print("\nChecking for sitemap locations...")
            sitemap_url = None
            
            for location in sitemap_locations:
                test_url = urljoin(base_url, location)
                if verify_url_accessibility(test_url):
                    sitemap_url = test_url
                    print(f"Found sitemap at: {sitemap_url}")
                    break
            
            if sitemap_url:
                break
            print("No sitemap found. Please choose another method.")
            
        elif choice == '2':
            sitemap_url = None
            break
            
        elif choice == '3':
            sitemap_url = input("Enter the complete sitemap URL: ").strip()
            if verify_url_accessibility(sitemap_url):
                break
            print("Could not access the provided sitemap URL. Please try again.")
    
    # Get output directory
    output_dir = input("\nEnter output directory name [markdown_docs]: ").strip()
    if not output_dir:
        output_dir = "markdown_docs"
    
    # Get optional delay setting
    delay_str = input("\nEnter delay between requests in seconds [1.0]: ").strip()
    try:
        delay = float(delay_str) if delay_str else 1.0
    except ValueError:
        print("Invalid delay value, using default of 1.0 seconds")
        delay = 1.0
        
    # Ask about max pages
    max_pages_str = input("\nMaximum number of pages to download (leave empty for no limit): ").strip()
    max_pages = None
    if max_pages_str:
        try:
            max_pages = int(max_pages_str)
            if max_pages < 1:
                print("Invalid value. No maximum limit will be applied.")
                max_pages = None
        except ValueError:
            print("Invalid value. No maximum limit will be applied.")
    
    # Ask about respecting robots.txt
    respect_robots = input("\nRespect robots.txt restrictions? (y/n) [y]: ").strip().lower() != 'n'
    
    return base_url, sitemap_url, output_dir, delay, max_pages, respect_robots

def main():
    """Main entry point of the script."""
    try:
        # Check for command line arguments first
        args = get_command_line_args()
        
        # If URL is provided via command line, use it, otherwise prompt for input
        if args.url:
            base_url = args.url
            output_dir = args.output
            delay = args.delay
            max_pages = args.max_pages
            respect_robots = not args.no_robots
            
            # Determine sitemap URL based on method
            sitemap_url = None
            if args.method == 'sitemap':
                sitemap_url = args.sitemap
            elif args.method == 'auto':
                # Try to auto-detect sitemap
                sitemap_locations = [
                    '/sitemap.xml',
                    '/sitemap_index.xml',
                    '/wp-sitemap.xml',
                    '/sitemap/sitemap.xml',
                    '/sitemaps/sitemap.xml'
                ]
                
                logger.info("Auto-detecting sitemap...")
                for location in sitemap_locations:
                    test_url = urljoin(base_url, location)
                    if verify_url_accessibility(test_url):
                        sitemap_url = test_url
                        logger.info(f"Found sitemap at: {sitemap_url}")
                        break
        else:
            # Get input interactively
            base_url, sitemap_url, output_dir, delay, max_pages, respect_robots = get_user_input()
        
        print("\nStarting documentation download...")
        crawler = DocumentationCrawler(
            base_url, 
            output_dir, 
            delay=delay, 
            respect_robots=respect_robots,
            max_pages=max_pages
        )
        
        if sitemap_url:
            crawler.crawl_sitemap(sitemap_url)
        else:
            crawler.crawl_recursive()
        
        print("\nSuccess! Documentation has been downloaded and converted.")
        print(f"You can find the Markdown files in the '{output_dir}' directory.")
        logger.info("Documentation crawling completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {str(e)}")
        logger.error(f"Script failed: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())