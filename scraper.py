import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from colorama import Fore, Style
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

class Scraper:
    """Main class for crawling and extracting links"""
    
    def __init__(self, base_url, max_depth=2, same_domain=True, use_selenium=False):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        self.same_domain = same_domain
        self.use_selenium = use_selenium
        self.visited_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Initialize Selenium if needed
        self.driver = None
        if self.use_selenium:
            self._init_selenium()
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f"{Fore.GREEN}Selenium initialized successfully{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error initializing Selenium: {str(e)}{Style.RESET_ALL}")
            self.driver = None
    
    def get_page_content(self, url):
        """Get HTML content of a page"""
        if self.use_selenium and self.driver:
            return self._get_page_content_selenium(url)
        else:
            return self._get_page_content_requests(url)
    
    def _get_page_content_requests(self, url):
        """Get page content using requests"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Detect encoding
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                if 'charset=' in response.text[:1000].lower():
                    charset = re.search(r'charset=([^\s;]+)', response.text[:1000], re.I)
                    if charset:
                        response.encoding = charset.group(1).strip('"\'')
            
            return response.text
        except Exception as e:
            print(f"{Fore.RED}Error fetching {url}: {str(e)}{Style.RESET_ALL}")
            return None
    
    def _get_page_content_selenium(self, url):
        """Get page content using Selenium"""
        try:
            self.driver.get(url)
            time.sleep(2)  # Wait for page to load
            
            # Wait for body to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source after JavaScript execution
            return self.driver.page_source
        except Exception as e:
            print(f"{Fore.RED}Error fetching {url} with Selenium: {str(e)}{Style.RESET_ALL}")
            return None
    
    def extract_links(self, html, current_url):
        """Extract all links from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        links = {
            'pages': [],      # Links to other pages
            'downloads': []   # Links to files
        }
        
        # Find all anchor tags
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(current_url, href)
            
            # Remove fragment and query
            parsed = urlparse(absolute_url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Detect link type
            if self.is_download_link(clean_url):
                links['downloads'].append(clean_url)
            elif self.is_page_link(clean_url):
                links['pages'].append(clean_url)
        
        # Find direct file links (img src, video src, etc.)
        for img in soup.find_all(['img', 'video', 'audio', 'source']):
            src = img.get('src') or img.get('data-src')
            if src:
                absolute_url = urljoin(current_url, src)
                links['downloads'].append(absolute_url)
        
        return links
    
    def extract_text_content(self, html, current_url):
        """Extract text content from HTML page"""
        soup = BeautifulSoup(html, 'html.parser')
        text_content = []
        
        # Extract title
        title = soup.find('title')
        if title:
            text_content.append(f"Title: {title.get_text(strip=True)}")
        
        # Extract headings
        for heading_level in range(1, 7):
            headings = soup.find_all(f'h{heading_level}')
            for heading in headings:
                text_content.append(f"H{heading_level}: {heading.get_text(strip=True)}")
        
        # Extract paragraphs
        paragraphs = soup.find_all('p')
        for para in paragraphs:
            text = para.get_text(strip=True)
            if text:
                text_content.append(f"Paragraph: {text}")
        
        # Extract lists
        for list_type in ['ul', 'ol']:
            lists = soup.find_all(list_type)
            for list_element in lists:
                items = list_element.find_all('li')
                for item in items:
                    text = item.get_text(strip=True)
                    if text:
                        text_content.append(f"List Item: {text}")
        
        # Extract article content if available
        articles = soup.find_all('article')
        for article in articles:
            text = article.get_text(strip=True)
            if text:
                text_content.append(f"Article: {text}")
        
        # Extract div content
        divs = soup.find_all('div', class_=re.compile(r'content|article|post|text', re.I))
        for div in divs:
            text = div.get_text(strip=True)
            if text and len(text) > 50:  # Only substantial content
                text_content.append(f"Content: {text}")
        
        return '\n\n'.join(text_content)
    
    def is_download_link(self, url):
        """Detect downloadable file links"""
        download_extensions = [
            '.pdf', '.txt', '.md', '.csv', '.log',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h',
            '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts',
            '.json', '.xml', '.yml', '.yaml', '.sql', '.sh', '.bash'
        ]
        
        import os
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in download_extensions)
    
    def is_page_link(self, url):
        """Detect regular page links"""
        page_extensions = ['.htm', '.html', '.php', '.asp', '.aspx', '/', '']
        path = urlparse(url).path.lower()
        
        # If no extension or has page extension
        if not any(path.endswith(ext) for ext in ['.jpg', '.png', '.pdf', '.zip']):
            if self.same_domain:
                return urlparse(url).netloc == self.base_domain
            return True
        return False
    
    def crawl(self):
        """Start crawling"""
        queue = deque([(self.base_url, 0)])  # (url, depth)
        all_downloads = set()
        all_pages = set()
        all_text_content = {}
        
        print(f"{Fore.CYAN}Starting crawl from: {self.base_url}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Maximum depth: {self.max_depth}{Style.RESET_ALL}")
        
        while queue:
            current_url, depth = queue.popleft()
            
            if current_url in self.visited_urls:
                continue
            
            if depth > self.max_depth:
                continue
            
            self.visited_urls.add(current_url)
            all_pages.add(current_url)
            
            print(f"\n{Fore.YELLOW}Checking page (depth {depth}): {current_url}{Style.RESET_ALL}")
            
            html = self.get_page_content(current_url)
            if html:
                # Extract text content
                text_content = self.extract_text_content(html, current_url)
                if text_content:
                    all_text_content[current_url] = text_content
                    print(f"{Fore.GREEN}  Text extracted: {len(text_content)} characters{Style.RESET_ALL}")
                
                # Extract links
                links = self.extract_links(html, current_url)
                
                # Add download links
                for download_link in links['downloads']:
                    if download_link not in all_downloads:
                        all_downloads.add(download_link)
                        print(f"{Fore.GREEN}  File found: {download_link}{Style.RESET_ALL}")
                
                # Add new pages to queue
                if depth < self.max_depth:
                    for page_link in links['pages']:
                        if page_link not in self.visited_urls and page_link not in [q[0] for q in queue]:
                            queue.append((page_link, depth + 1))
            
            # Short delay to avoid overwhelming the server
            time.sleep(0.5)
        
        print(f"\n{Fore.CYAN}Crawling completed!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Pages checked: {len(all_pages)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Files found: {len(all_downloads)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Text content extracted from: {len(all_text_content)} pages{Style.RESET_ALL}")
        
        return all_downloads, all_text_content
    
    def close(self):
        """Close Selenium driver if open"""
        if self.driver:
            self.driver.quit()
            print(f"{Fore.GREEN}Selenium driver closed{Style.RESET_ALL}")