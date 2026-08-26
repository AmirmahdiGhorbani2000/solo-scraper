import requests
import time
from pathlib import Path
from tqdm import tqdm
from colorama import Fore, Style

class Downloader:
    """Manage file downloads"""
    
    def __init__(self, max_size_mb=10, delay=0.5):
        self.max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        self.delay = delay  # Delay between downloads (seconds)
        self.total_downloaded = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_file(self, url, save_path, file_type='unknown'):
        """Download a file from URL"""
        try:
            # Check total downloaded size
            if self.total_downloaded >= self.max_size_bytes:
                print(f"{Fore.YELLOW}Warning: Maximum download size reached!{Style.RESET_ALL}")
                return False
            
            response = self.session.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Check file size
            content_length = int(response.headers.get('content-length', 0))
            if content_length > 0:
                if self.total_downloaded + content_length > self.max_size_bytes:
                    print(f"{Fore.YELLOW}Warning: File {url} is larger than remaining allowed size!{Style.RESET_ALL}")
                    return False
            
            # Download file with progress bar
            file_size = 0
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                if content_length > 0:
                    with tqdm(total=content_length, unit='B', unit_scale=True, 
                             desc=f"Downloading {save_path.name}", ncols=80) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                file_size += len(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            file_size += len(chunk)
            
            self.total_downloaded += file_size
            print(f"{Fore.GREEN}Downloaded: {save_path.name} ({self.format_size(file_size)}){Style.RESET_ALL}")
            
            # Delay between downloads
            time.sleep(self.delay)
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Error downloading {url}: {str(e)}{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
            return False
    
    @staticmethod
    def format_size(size_bytes):
        """Convert size to readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"