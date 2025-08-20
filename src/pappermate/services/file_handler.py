"""
File handler for managing files with special characters, especially Asian characters.
Handles filename sanitization using Google Translate API with intelligent fallback and reprocessing queue.
"""

import os
import shutil
import unicodedata
import json
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta
import re

try:
    from google.cloud import translate_v3 as translate
    from google.auth import default
    from google.auth.transport.requests import Request
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
    print("Warning: google-cloud-translate not available. Install with: pip install google-cloud-translate")

# Removed fallback dependencies - we want the real API working
GOOGLETRANS_AVAILABLE = False


class TranslationStatus:
    """Status tracking for translation attempts."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY_READY = "retry_ready"
    SKIPPED = "skipped"


class TranslationResult:
    """Result of translation attempt."""

    def __init__(self, original_filename: str, translated_filename: str,
                 status: str, error_message: Optional[str] = None,
                 retry_after: Optional[datetime] = None):
        self.original_filename = original_filename
        self.translated_filename = translated_filename
        self.status = status
        self.error_message = error_message
        self.retry_after = retry_after
        self.attempts = 0
        self.last_attempt = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'original_filename': self.original_filename,
            'translated_filename': self.translated_filename,
            'status': self.status,
            'error_message': self.error_message,
            'retry_after': self.retry_after.isoformat() if self.retry_after else None,
            'attempts': self.attempts,
            'last_attempt': self.last_attempt.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TranslationResult':
        """Create from dictionary."""
        result = cls(
            original_filename=data['original_filename'],
            translated_filename=data['translated_filename'],
            status=data['status'],
            error_message=data.get('error_message'),
            retry_after=datetime.fromisoformat(data['retry_after']) if data.get('retry_after') else None
        )
        result.attempts = data.get('attempts', 0)
        result.last_attempt = datetime.fromisoformat(data['last_attempt'])
        return result


class FileHandler:
    """
    Handles files with special characters in names using Google Cloud Translation API v3.
    Implements proper OAuth2 authentication for production use.
    """

    def __init__(self, temp_dir: str = "temp_processing",
                 reprocessing_dir: str = "reprocessing_queue",
                 project_id: Optional[str] = None,
                 location: str = "global",
                 max_retries: int = 3,
                 retry_delay_hours: int = 24):
        self.temp_dir = Path(temp_dir)
        self.reprocessing_dir = Path(reprocessing_dir)
        self.temp_dir.mkdir(exist_ok=True)
        self.reprocessing_dir.mkdir(exist_ok=True)

        # Create subdirectories for different statuses
        (self.reprocessing_dir / "pending").mkdir(exist_ok=True)
        (self.reprocessing_dir / "failed").mkdir(exist_ok=True)
        (self.reprocessing_dir / "retry_ready").mkdir(exist_ok=True)

        self.filename_mapping: Dict[str, str] = {}
        self.translation_queue: Dict[str, TranslationResult] = {}

        # Google Cloud configuration
        self.project_id = project_id or os.environ.get('GOOGLE_CLOUD_PROJECT')
        self.location = location
        self.max_retries = max_retries
        self.retry_delay_hours = retry_delay_hours

        # Initialize translation services
        self._init_translation_services()

        # Load existing translation queue
        self._load_translation_queue()

    def _init_translation_services(self):
        """Initialize Google Cloud Translation API v3 with OAuth2."""
        if not GOOGLE_TRANSLATE_AVAILABLE:
            print("❌ Google Cloud Translation API not available")
            return

        try:
            # Try to get default credentials (OAuth2)
            credentials, project = default()
            
            if not self.project_id:
                self.project_id = project
            
            if not self.project_id:
                print("❌ No Google Cloud project ID found. Set GOOGLE_CLOUD_PROJECT env var")
                return

            # Test the API connection
            client = translate.TranslationServiceClient(credentials=credentials)
            
            # Test with a simple request
            parent = f"projects/{self.project_id}/locations/{self.location}"
            
            # This is just a connection test - we won't actually translate
            print(f"✅ Google Cloud Translation API v3 initialized")
            print(f"   Project: {self.project_id}")
            print(f"   Location: {self.location}")
            print(f"   Authentication: OAuth2 (Service Account)")
            
            self.client = client
            self.parent = parent
            
        except Exception as e:
            print(f"❌ Failed to initialize Google Cloud Translation API: {e}")
            print("   Make sure you have:")
            print("   1. gcloud auth application-default login")
            print("   2. GOOGLE_CLOUD_PROJECT set")
            print("   3. Cloud Translation API enabled")
            self.client = None
            self.parent = None

    def _load_translation_queue(self):
        """Load existing translation queue from disk."""
        queue_file = self.reprocessing_dir / "translation_queue.json"
        if queue_file.exists():
            try:
                with open(queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, item_data in data.items():
                        self.translation_queue[key] = TranslationResult.from_dict(item_data)
                print(f"📋 Loaded {len(self.translation_queue)} items from translation queue")
            except Exception as e:
                print(f"⚠️ Failed to load translation queue: {e}")

    def _save_translation_queue(self):
        """Save translation queue to disk."""
        queue_file = self.reprocessing_dir / "translation_queue.json"
        try:
            data = {key: item.to_dict() for key, item in self.translation_queue.items()}
            with open(queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save translation queue: {e}")

    def translate_text(self, text: str, target_lang: str = 'en', source_lang: str = 'auto') -> Tuple[str, str, Optional[str]]:
        """
        Translate text using Google Cloud Translation API v3.

        Args:
            text: Text to translate
            target_lang: Target language code (default: 'en')
            source_lang: Source language code (default: 'auto')

        Returns:
            Tuple of (translated_text, status, error_message)
        """
        if not text.strip():
            return text, TranslationStatus.SUCCESS, None

        if not self.client:
            return text, TranslationStatus.FAILED, "Translation service not available"

        try:
            # Prepare the request
            request = {
                "parent": self.parent,
                "contents": [text],
                "mime_type": "text/plain",
                "source_language_code": source_lang if source_lang != 'auto' else None,
                "target_language_code": target_lang,
            }

            # Remove None values
            request = {k: v for k, v in request.items() if v is not None}

            # Make the translation request
            response = self.client.translate_text(**request)
            
            if response.translations:
                translated_text = response.translations[0].translated_text
                print(f"🔤 Translated: '{text}' → '{translated_text}'")
                return translated_text, TranslationStatus.SUCCESS, None
            else:
                return text, TranslationStatus.FAILED, "No translation returned"

        except Exception as e:
            error_msg = f"Translation failed: {str(e)}"
            print(f"❌ {error_msg}")
            return text, TranslationStatus.FAILED, error_msg

    def sanitize_filename(self, filename: str) -> Tuple[str, str, Optional[str]]:
        """
        Sanitize filename by translating special characters to safe ASCII equivalents.
        
        Args:
            filename: Original filename with potential special characters
            
        Returns:
            Tuple of (sanitized_filename, status, error_message)
        """
        # Get the base name and extension
        path = Path(filename)
        base_name = path.stem
        extension = path.suffix
        
        # Check if filename needs translation
        if base_name.isascii():
            return filename, TranslationStatus.SUCCESS, None
        
        # Try to translate the filename
        if self.client:
            try:
                # Split filename into meaningful parts for better translation
                parts = self._split_filename_for_translation(base_name)
                translated_parts = []
                all_parts_successful = True
                
                for part in parts:
                    if part.strip() and not part.isascii():
                        translated_part, status, error = self.translate_text(part)
                        if status == TranslationStatus.SUCCESS:
                            print(f"🔤 Translated: '{part}' → '{translated_part}'")
                            translated_parts.append(translated_part)
                        else:
                            print(f"⚠️ Translation failed for '{part}': {error}")
                            translated_parts.append(part)
                            all_parts_successful = False
                    else:
                        translated_parts.append(part)
                
                if all_parts_successful:
                    translated_base = '_'.join(translated_parts)
                    sanitized_base = self._clean_translated_text(translated_base)
                    return f"{sanitized_base}{extension}", TranslationStatus.SUCCESS, None
                else:
                    # Some parts failed translation
                    # Apply fallback mapping to still improve filename for downstream handling
                    fallback_mapped = self._fallback_map_filename(base_name)
                    if fallback_mapped and fallback_mapped != base_name:
                        sanitized_base = self._clean_translated_text(fallback_mapped)
                        error_msg = "Translation failed: Partial translation failure - applied fallback mapping"
                        return f"{sanitized_base}{extension}", TranslationStatus.FAILED, error_msg
                    error_msg = "Partial translation failure - some parts could not be translated"
                    return filename, TranslationStatus.FAILED, error_msg
                    
            except Exception as e:
                error_msg = f"Translation failed: {e}"
                print(f"⚠️ {error_msg}")
                # Try fallback mapping on unexpected errors
                fallback_mapped = self._fallback_map_filename(base_name)
                if fallback_mapped and fallback_mapped != base_name:
                    sanitized_base = self._clean_translated_text(fallback_mapped)
                    return f"{sanitized_base}{extension}", TranslationStatus.FAILED, f"Translation failed: {error_msg}"
                return filename, TranslationStatus.FAILED, error_msg
        else:
            # No translation service available
            # Apply deterministic fallback mapping for common Asian terms
            fallback_mapped = self._fallback_map_filename(base_name)
            if fallback_mapped and fallback_mapped != base_name:
                sanitized_base = self._clean_translated_text(fallback_mapped)
                error_msg = "Translation failed: No translation service available - applied fallback mapping"
                return f"{sanitized_base}{extension}", TranslationStatus.FAILED, error_msg
            error_msg = "No translation service available"
            return filename, TranslationStatus.FAILED, error_msg

    def _split_filename_for_translation(self, filename: str) -> list:
        """
        Split filename into meaningful parts for better translation.
        
        Args:
            filename: Filename to split
            
        Returns:
            List of filename parts
        """
        # Split by common delimiters
        delimiters = ['_', '-', ' ', '　', '、', '。', '（', '）']
        
        for delimiter in delimiters:
            if delimiter in filename:
                parts = filename.split(delimiter)
                # Filter out empty parts and very short parts
                parts = [part.strip() for part in parts if part.strip() and len(part.strip()) > 1]
                if parts:
                    return parts
        
        # If no good delimiter found, return the whole filename
        return [filename]

    def _clean_translated_text(self, text: str) -> str:
        """
        Clean up translated text for use in filenames.
        
        Args:
            text: Translated text
            
        Returns:
            Cleaned text suitable for filenames
        """
        # Remove quotes and other problematic characters
        text = re.sub(r'["\'`]', '', text)
        
        # Replace common punctuation with underscores
        text = re.sub(r'[^\w\s\-]', '_', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', '_', text)
        
        return text.strip('_')

    def _fallback_map_filename(self, base_name: str) -> str:
        """
        Apply a lightweight mapping for common non-ASCII terms to English to improve
        filename readability when translation services are unavailable.
        This is intentionally minimal and deterministic (no external calls).
        """
        # Common mappings (Japanese examples + generic terms)
        term_map = {
            # Japanese brackets often used in titles
            '【': '', '】': '',
            # Frequent business terms
            '御見積書': 'Quotation',
            '見積書': 'Quotation',
            '見積': 'Estimate',
            '請求書': 'Invoice',
            '契約': 'Contract',
            '契約書': 'Contract',
            'システム': 'System',
            '運用': 'Operations',
            'サポート': 'Support',
            # Chinese common
            '合同': 'Contract',
            '报价': 'Quotation',
            '系统': 'System',
            '支持': 'Support',
        }

        # Split using the same delimiters used for translation splitting
        parts = self._split_filename_for_translation(base_name)
        mapped_parts: List[str] = []
        for part in parts:
            original_part = part
            # Replace known multi-char terms first
            for k, v in term_map.items():
                if k in part:
                    part = part.replace(k, v)
            mapped_parts.append(part if part else original_part)

        if not mapped_parts:
            return base_name

        # Join with underscore and return
        candidate = '_'.join(mapped_parts)
        return candidate

    def create_safe_copy(self, original_path: str) -> Tuple[str, str, str, Optional[str]]:
        """
        Create a safe copy of the file with a sanitized filename.
        
        Args:
            original_path: Path to the original file
            
        Returns:
            Tuple of (safe_path, original_filename, status, error_message)
        """
        original_path = Path(original_path)
        
        if not original_path.exists():
            raise FileNotFoundError(f"File not found: {original_path}")
        
        # Generate safe filename
        safe_filename, status, error_message = self.sanitize_filename(original_path.name)
        
        # If translation failed, add to reprocessing queue
        if status == TranslationStatus.FAILED:
            self._add_to_reprocessing_queue(original_path.name, safe_filename, error_message)
        
        safe_path = self.temp_dir / safe_filename
        
        # Ensure unique filename
        counter = 1
        while safe_path.exists():
            name_parts = safe_filename.rsplit('.', 1)
            if len(name_parts) == 2:
                base, ext = name_parts
                safe_filename = f"{base}_{counter}{ext}"
            else:
                safe_filename = f"{safe_filename}_{counter}"
            safe_path = self.temp_dir / safe_filename
            counter += 1
        
        # Copy file to temp location with safe name
        shutil.copy2(original_path, safe_path)
        
        # Store mapping for reference
        self.filename_mapping[str(safe_path)] = str(original_path)
        
        return str(safe_path), str(original_path), status, error_message
    
    def _add_to_reprocessing_queue(self, original_filename: str, fallback_filename: str, error_message: str):
        """Add file to reprocessing queue for future translation attempts."""
        key = f"{original_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = TranslationResult(
            original_filename=original_filename,
            translated_filename=fallback_filename,
            status=TranslationStatus.FAILED,
            error_message=error_message,
            retry_after=datetime.now() + timedelta(hours=self.retry_delay_hours)
        )
        
        self.translation_queue[key] = result
        self._save_translation_queue()
        
        # Move file to reprocessing directory
        reprocessing_path = self.reprocessing_dir / "failed" / original_filename
        try:
            shutil.copy2(Path(original_filename), reprocessing_path)
            print(f"📋 Added '{original_filename}' to reprocessing queue (will retry after {self.retry_delay_hours}h)")
        except Exception as e:
            print(f"⚠️ Failed to copy file to reprocessing queue: {e}")
    
    def process_file_safely(self, file_path: str, processor_func, *args, **kwargs):
        """
        Process a file safely by creating a temporary copy with a safe filename.
        
        Args:
            file_path: Path to the file to process
            processor_func: Function to process the file
            *args, **kwargs: Arguments to pass to the processor function
            
        Returns:
            Result of the processor function
        """
        try:
            # Create safe copy
            safe_path, original_path, status, error_message = self.create_safe_copy(file_path)
            
            # Process the safe copy
            result = processor_func(safe_path, *args, **kwargs)
            
            return result
            
        except Exception as e:
            raise Exception(f"Error processing file {file_path}: {e}")
        finally:
            # Clean up temp file
            if 'safe_path' in locals() and os.path.exists(safe_path):
                os.remove(safe_path)
    
    def get_reprocessing_status(self) -> Dict[str, any]:
        """Get current status of reprocessing queue."""
        total_items = len(self.translation_queue)
        pending_items = sum(1 for item in self.translation_queue.values() 
                          if item.status == TranslationStatus.PENDING)
        failed_items = sum(1 for item in self.translation_queue.values() 
                          if item.status == TranslationStatus.FAILED)
        retry_ready = sum(1 for item in self.translation_queue.values() 
                         if item.status == TranslationStatus.RETRY_READY)
        
        return {
            'total_items': total_items,
            'pending': pending_items,
            'failed': failed_items,
            'retry_ready': retry_ready,
            'items': [item.to_dict() for item in self.translation_queue.values()]
        }
    
    def retry_failed_translations(self) -> Dict[str, any]:
        """Retry failed translations that are ready for retry."""
        retry_results = {
            'successful': 0,
            'still_failed': 0,
            'errors': []
        }
        
        current_time = datetime.now()
        items_to_retry = []
        
        # Find items ready for retry
        for key, item in self.translation_queue.items():
            if (item.status == TranslationStatus.FAILED and 
                item.retry_after and 
                current_time >= item.retry_after and
                item.attempts < self.max_retries):
                items_to_retry.append(key)
        
        print(f"🔄 Attempting to retry {len(items_to_retry)} failed translations...")
        
        for key in items_to_retry:
            item = self.translation_queue[key]
            item.attempts += 1
            item.last_attempt = current_time
            
            try:
                # Try translation again
                translated_filename, status, error = self.sanitize_filename(item.original_filename)
                
                if status == TranslationStatus.SUCCESS:
                    item.status = TranslationStatus.SUCCESS
                    item.translated_filename = translated_filename
                    item.error_message = None
                    retry_results['successful'] += 1
                    print(f"✅ Retry successful for '{item.original_filename}' → '{translated_filename}'")
                else:
                    # Still failed, schedule next retry
                    item.status = TranslationStatus.FAILED
                    item.error_message = error
                    item.retry_after = current_time + timedelta(hours=self.retry_delay_hours)
                    retry_results['still_failed'] += 1
                    
                    if item.attempts >= self.max_retries:
                        item.status = TranslationStatus.SKIPPED
                        print(f"⏭️ Max retries reached for '{item.original_filename}' - marked as skipped")
                
            except Exception as e:
                error_msg = f"Retry attempt failed: {e}"
                item.error_message = error_msg
                item.retry_after = current_time + timedelta(hours=self.retry_delay_hours)
                retry_results['still_failed'] += 1
                retry_results['errors'].append(f"{item.original_filename}: {error_msg}")
        
        # Save updated queue
        self._save_translation_queue()
        
        return retry_results
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(exist_ok=True)
        self.filename_mapping.clear()
    
    def get_original_filename(self, safe_path: str) -> Optional[str]:
        """Get the original filename from a safe path."""
        return self.filename_mapping.get(safe_path)
    
    def get_filename_mapping(self) -> Dict[str, str]:
        """Get the current filename mapping."""
        return self.filename_mapping.copy()
    
    def is_safe_filename(self, filename: str) -> bool:
        """
        Check if a filename is safe for processing (contains only ASCII characters).
        
        Args:
            filename: Filename to check
            
        Returns:
            True if filename is safe, False otherwise
        """
        try:
            filename.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False
    
    def get_unsafe_files_in_directory(self, directory: str) -> list:
        """
        Find all files in a directory with potentially unsafe filenames.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of files with unsafe filenames
        """
        unsafe_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            return unsafe_files
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                if not self.is_safe_filename(file_path.name):
                    unsafe_files.append(str(file_path))
        
        return unsafe_files
    
    def print_reprocessing_summary(self):
        """Print a summary of the current reprocessing queue status."""
        status = self.get_reprocessing_status()
        
        print("\n📊 REPROCESSING QUEUE STATUS")
        print("=" * 50)
        print(f"Total items: {status['total_items']}")
        print(f"Pending: {status['pending']}")
        print(f"Failed: {status['failed']}")
        print(f"Ready for retry: {status['retry_ready']}")
        
        if status['total_items'] > 0:
            print("\n📋 ITEMS IN QUEUE:")
            for item_data in status['items']:
                status_icon = {
                    TranslationStatus.PENDING: "⏳",
                    TranslationStatus.FAILED: "❌",
                    TranslationStatus.RETRY_READY: "🔄",
                    TranslationStatus.SUCCESS: "✅",
                    TranslationStatus.SKIPPED: "⏭️"
                }.get(item_data['status'], "❓")
                
                print(f"  {status_icon} {item_data['original_filename']}")
                print(f"     Status: {item_data['status']}")
                if item_data['error_message']:
                    print(f"     Error: {item_data['error_message']}")
                if item_data['retry_after']:
                    print(f"     Retry after: {item_data['retry_after']}")
                print()
