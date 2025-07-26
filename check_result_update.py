#!/usr/bin/env python3
"""
Verification script to check if result.json is updating properly
"""
import json
import time
from pathlib import Path

def check_result_update():
    """Check if result.json has recent updates"""
    result_path = Path("output/result.json")
    
    if not result_path.exists():
        print("❌ result.json does not exist")
        return
    
    # Check file modification time
    mod_time = result_path.stat().st_mtime
    current_time = time.time()
    time_diff = current_time - mod_time
    
    print(f"📁 File: {result_path}")
    print(f"🕒 Last modified: {time_diff:.1f} seconds ago")
    
    # Load and check content
    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Result Summary:")
        print(f"   - Timestamp: {data['metadata']['processing_timestamp']}")
        print(f"   - Documents: {len(data['metadata']['input_documents'])}")
        print(f"   - Persona: {data['metadata']['persona']}")
        print(f"   - Job: {data['metadata']['job_to_be_done']}")
        print(f"   - Extracted sections: {len(data.get('extracted_sections', []))}")
        print(f"   - Refined subsections: {len(data.get('refined_subsections', []))}")
        
        if time_diff < 60:  # Updated within last minute
            print("✅ File appears to be updating correctly!")
        else:
            print("⚠️  File was not updated recently")
            
    except Exception as e:
        print(f"❌ Error reading result.json: {e}")

if __name__ == "__main__":
    check_result_update()
