#!/usr/bin/env python3
"""
Test script for PapperMate's intelligent translation system.
Demonstrates fallback handling and reprocessing queue.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pappermate.services.file_handler import FileHandler, TranslationStatus
from pappermate.config.translation import setup_translation_environment


def test_translation_system():
    """Test the complete translation system."""
    print("🚀 TESTING PapperMate Translation System")
    print("=" * 50)
    
    # Setup translation environment
    config = setup_translation_environment()
    
    # Initialize FileHandler
    print("\n🔧 Initializing FileHandler...")
    handler = FileHandler(
        temp_dir="temp_test",
        reprocessing_dir="reprocessing_test",
        project_id=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        max_retries=2,
        retry_delay_hours=1  # Short delay for testing
    )
    
    # Test filenames with different characteristics
    test_filenames = [
        "normal_file.pdf",  # ASCII - should work
        "【御見積書】_システム運用サポート.pdf",  # Japanese - needs translation
        "框架合同_发票.pdf",  # Chinese - needs translation
        "서비스_계약서.pdf",  # Korean - needs translation
        "file_with_spaces.pdf",  # ASCII with spaces - should work
        "見積書_システム.pdf",  # Japanese - needs translation
    ]
    
    print(f"\n📝 Testing {len(test_filenames)} filenames...")
    
    for filename in test_filenames:
        print(f"\n--- Testing: {filename} ---")
        
        # Check if filename needs translation
        needs_translation = not filename.isascii()
        print(f"   Needs translation: {'✅ Yes' if needs_translation else '❌ No'}")
        
        if needs_translation:
            # Try to sanitize
            sanitized, status, error = handler.sanitize_filename(filename)
            print(f"   Sanitized: {sanitized}")
            print(f"   Status: {status}")
            if error:
                print(f"   Error: {error}")
        else:
            print(f"   No translation needed")
    
    # Show reprocessing queue status
    print("\n" + "=" * 50)
    handler.print_reprocessing_summary()
    
    # Test retry functionality
    print("\n🔄 Testing retry functionality...")
    retry_results = handler.retry_failed_translations()
    
    if retry_results['successful'] > 0 or retry_results['still_failed'] > 0:
        print(f"   Successful retries: {retry_results['successful']}")
        print(f"   Still failed: {retry_results['still_failed']}")
        if retry_results['errors']:
            print(f"   Errors: {retry_results['errors']}")
    
    # Final status
    print("\n📊 Final Status:")
    handler.print_reprocessing_summary()
    
    return handler


def test_with_real_files():
    """Test with actual files in the pdfContracts directory."""
    pdf_dir = Path("pdfContracts")
    
    if not pdf_dir.exists():
        print(f"⚠️ Directory {pdf_dir} not found. Skipping real file test.")
        return
    
    print(f"\n🔍 Testing with real files in {pdf_dir}...")
    
    handler = FileHandler()
    
    # Find PDF files
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("   No PDF files found.")
        return
    
    print(f"   Found {len(pdf_files)} PDF files")
    
    for pdf_file in pdf_files[:3]:  # Test first 3 files
        print(f"\n--- Testing real file: {pdf_file.name} ---")
        
        # Check if filename needs translation
        needs_translation = not pdf_file.name.isascii()
        print(f"   Needs translation: {'✅ Yes' if needs_translation else '❌ No'}")
        
        if needs_translation:
            # Try to sanitize
            sanitized, status, error = handler.sanitize_filename(pdf_file.name)
            print(f"   Sanitized: {sanitized}")
            print(f"   Status: {status}")
            if error:
                print(f"   Error: {error}")
    
    # Show final status
    print("\n📊 Final Status with Real Files:")
    handler.print_reprocessing_summary()


if __name__ == "__main__":
    try:
        # Test basic functionality
        handler = test_translation_system()
        
        # Test with real files if available
        test_with_real_files()
        
        print("\n✅ Translation system test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
