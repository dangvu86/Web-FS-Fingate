#!/usr/bin/env python3

from simple_app import download_zip_from_drive
import os

def test_google_drive_download():
    """Test Google Drive download with the original file ID"""
    
    # Original file ID from your fs_extract.py
    file_id = "1A0yeEBAvLkX64PlatHboPAHhHVIcJICw"
    
    print(f"Testing Google Drive download...")
    print(f"File ID: {file_id}")
    print(f"URL: https://drive.google.com/file/d/{file_id}/view")
    
    result = download_zip_from_drive(file_id)
    
    if result:
        print(f"Download successful! File size: {len(result.getvalue())} bytes")
        return True
    else:
        print("Download failed!")
        return False

def test_alternative_file_ids():
    """Test with some alternative public file IDs"""
    test_ids = [
        "1A0yeEBAvLkX64PlatHboPAHhHVIcJICw",  # Original
        # You can add more test IDs here
    ]
    
    for file_id in test_ids:
        print(f"\n--- Testing ID: {file_id} ---")
        result = download_zip_from_drive(file_id)
        if result:
            print(f"Success: {len(result.getvalue())} bytes")
            break
        else:
            print("Failed")

if __name__ == '__main__':
    print("Google Drive Download Test")
    print("=" * 40)
    
    try:
        test_google_drive_download()
        print("\n" + "=" * 40)
        print("If download failed, possible reasons:")
        print("1. File is not publicly accessible")
        print("2. Google Drive has rate limiting")
        print("3. File sharing permissions are restricted")
        print("4. Network connectivity issues")
        print("\nSolutions:")
        print("1. Ensure file is shared publicly (Anyone with link can view)")
        print("2. Try using a different file ID")
        print("3. Check your internet connection")
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()