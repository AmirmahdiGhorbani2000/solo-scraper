import mimetypes
from pathlib import Path
from urllib.parse import urlparse
import re

class ContentDetector:
    """Detect content type from URL and file extension"""
    
    # Extensions for each content type
    TEXT_EXTENSIONS = {'.txt', '.md', '.rtf', '.doc', '.docx', '.odt', '.csv', '.log'}
    CODE_EXTENSIONS = {
        '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.php',
        '.rb', '.go', '.rs', '.swift', '.kt', '.ts', '.json', '.xml', '.yml',
        '.yaml', '.sql', '.sh', '.bash', '.r', '.m', '.ipynb'
    }
    PDF_EXTENSIONS = {'.pdf'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff'}
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma'}
    ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}
    
    @staticmethod
    def detect_from_url(url):
        """Detect content type from URL"""
        path = urlparse(url).path.lower()
        extension = Path(path).suffix
        
        if extension in ContentDetector.CODE_EXTENSIONS:
            return 'code', extension
        elif extension in ContentDetector.PDF_EXTENSIONS:
            return 'pdf', extension
        elif extension in ContentDetector.IMAGE_EXTENSIONS:
            return 'image', extension
        elif extension in ContentDetector.VIDEO_EXTENSIONS:
            return 'video', extension
        elif extension in ContentDetector.AUDIO_EXTENSIONS:
            return 'audio', extension
        elif extension in ContentDetector.TEXT_EXTENSIONS:
            return 'text', extension
        elif extension in ContentDetector.ARCHIVE_EXTENSIONS:
            return 'archive', extension
        else:
            return 'unknown', extension
    
    @staticmethod
    def detect_from_headers(content_type):
        """Detect content type from Content-Type header"""
        if not content_type:
            return 'unknown', ''
        
        content_type = content_type.lower()
        
        if 'text/html' in content_type or 'text/plain' in content_type:
            return 'text', '.txt'
        elif 'application/pdf' in content_type:
            return 'pdf', '.pdf'
        elif 'image/' in content_type:
            ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
            return 'image', ext or '.jpg'
        elif 'video/' in content_type:
            ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
            return 'video', ext or '.mp4'
        elif 'audio/' in content_type:
            ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
            return 'audio', ext or '.mp3'
        elif 'application/zip' in content_type or 'application/x-rar' in content_type:
            return 'archive', '.zip'
        elif 'javascript' in content_type or 'json' in content_type or 'xml' in content_type:
            return 'code', mimetypes.guess_extension(content_type.split(';')[0].strip()) or '.txt'
        else:
            return 'unknown', ''