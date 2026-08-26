import os
import zipfile
from pathlib import Path
from colorama import Fore, Style, init
from scraper import Scraper
from downloader import Downloader
from content_detector import ContentDetector
from urllib.parse import urlparse
import re

# Initialize colorama
init()

def create_zip(source_dir, zip_name):
    """Create ZIP file from download directory"""
    zip_path = f"{zip_name}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    
    return zip_path

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def main():
    """Main program function"""
    print(f"{Fore.CYAN}SoloScraper - Universal Web Scraper{Style.RESET_ALL}")
    
    # Get user input
    url = input(f"{Fore.YELLOW}Enter website URL: {Style.RESET_ALL}").strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    zip_name = input(f"{Fore.YELLOW}Enter output ZIP filename (without extension): {Style.RESET_ALL}").strip()
    if not zip_name:
        zip_name = "scraped_data"
    zip_name = sanitize_filename(zip_name)
    
    try:
        max_size = float(input(f"{Fore.YELLOW}Maximum download size (MB): {Style.RESET_ALL}").strip() or "50")
        max_depth = int(input(f"{Fore.YELLOW}Crawl depth (1-5): {Style.RESET_ALL}").strip() or "2")
        use_selenium_input = input(f"{Fore.YELLOW}Use Selenium for JavaScript-heavy sites? (y/n): {Style.RESET_ALL}").strip().lower()
        use_selenium = use_selenium_input in ['y', 'yes']
    except ValueError:
        print(f"{Fore.RED}Invalid value! Using defaults.{Style.RESET_ALL}")
        max_size = 50
        max_depth = 2
        use_selenium = False
    
    # Limit depth
    max_depth = max(1, min(max_depth, 5))
    
    # Create temporary directory for downloads
    temp_dir = Path("temp_downloads")
    temp_dir.mkdir(exist_ok=True)
    
    # Start crawling
    scraper = Scraper(url, max_depth=max_depth, same_domain=True, use_selenium=use_selenium)
    download_links, text_content = scraper.crawl()
    
    # Create subdirectories
    subdirs = {
        'text': temp_dir / 'texts',
        'pdf': temp_dir / 'pdfs',
        'code': temp_dir / 'codes',
        'image': temp_dir / 'images',
        'video': temp_dir / 'videos',
        'audio': temp_dir / 'audios',
        'archive': temp_dir / 'archives',
        'unknown': temp_dir / 'unknown'
    }
    
    for subdir in subdirs.values():
        subdir.mkdir(parents=True, exist_ok=True)
    
    # Save extracted text content
    if text_content:
        print(f"\n{Fore.CYAN}Saving extracted text content...{Style.RESET_ALL}")
        text_file_path = subdirs['text'] / 'extracted_text.txt'
        with open(text_file_path, 'w', encoding='utf-8') as f:
            for page_url, content in text_content.items():
                f.write(f"{'='*60}\n")
                f.write(f"Source URL: {page_url}\n")
                f.write(f"{'='*60}\n\n")
                f.write(content)
                f.write("\n\n")
        print(f"{Fore.GREEN}Text content saved to: {text_file_path.name}{Style.RESET_ALL}")
    
    # Download files
    if download_links:
        downloader = Downloader(max_size_mb=max_size, delay=0.3)
        
        print(f"\n{Fore.CYAN}Starting download of {len(download_links)} files...{Style.RESET_ALL}")
        
        file_counter = {}
        for link in download_links:
            # Detect file type
            file_type, extension = ContentDetector.detect_from_url(link)
            
            # Generate filename
            if file_type not in file_counter:
                file_counter[file_type] = 1
            else:
                file_counter[file_type] += 1
            
            filename = f"file_{file_counter[file_type]}{extension}"
            save_path = subdirs[file_type] / filename
            
            # Download
            downloader.download_file(link, save_path, file_type)
            
            # Check size limit
            if downloader.total_downloaded >= downloader.max_size_bytes:
                print(f"\n{Fore.YELLOW}Maximum size limit reached! Download stopped.{Style.RESET_ALL}")
                break
    else:
        print(f"\n{Fore.YELLOW}No downloadable files found.{Style.RESET_ALL}")
    
    # Close Selenium if used
    scraper.close()
    
    # Create final ZIP
    print(f"\n{Fore.CYAN}Creating ZIP file...{Style.RESET_ALL}")
    zip_path = create_zip(temp_dir, zip_name)
    
    # Clean up temporary directory
    import shutil
    shutil.rmtree(temp_dir)
    
    # Display summary
    zip_size = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"\n{Fore.GREEN}{'—'*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Operation completed successfully!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}ZIP file: {zip_path}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}File size: {zip_size:.2f} MB{Style.RESET_ALL}")
    
    if text_content:
        print(f"{Fore.GREEN}Text content extracted from: {len(text_content)} pages{Style.RESET_ALL}")
    
    if download_links:
        print(f"{Fore.GREEN}Files downloaded:{Style.RESET_ALL}")
        for file_type, count in file_counter.items():
            print(f"{Fore.GREEN}   - {file_type}: {count} files{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}{'—'*60}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()