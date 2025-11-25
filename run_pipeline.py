"""
BSC Course Content Generator - Master Pipeline
Runs PDF extraction followed by content generation
"""

import subprocess
import sys
from pathlib import Path
import json

def run_command(description, script_name):
    """Run a Python script and handle errors."""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run([sys.executable, script_name], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error: {description} failed with exit code {e.returncode}")
        return False

def main():
    """Main pipeline orchestrator."""
    
    print("\n" + "="*70)
    print("  BSC COURSE CONTENT GENERATOR")
    print("  Complete Pipeline: PDF → Syllabus → AI Content")
    print("="*70)
    
    # Check if input folder has PDFs
    input_path = Path("input")
    if not input_path.exists() or not list(input_path.glob("*.pdf")):
        print("\n⚠️  WARNING: No PDF files found in 'input/' folder")
        print("   Please add syllabus PDFs to the input folder.")
        print("\n   To run only content generation (skip PDF extraction):")
        print("   python app.py\n")
        response = input("Continue with PDF extraction anyway? (y/n): ")
        if response.lower() != 'y':
            print("\n❌ Pipeline cancelled.")
            return 1
    
    # Step 1: Extract syllabus from PDFs
    if not run_command("Step 1: Extracting Syllabus from PDFs", 
                       "extract_syllabus.py"):
        print("\n❌ Pipeline failed at PDF extraction.")
        return 1
    
    # Check if output was created
    output_folder = Path("output/course_json")
    json_files = list(output_folder.glob("*.json"))
    
    if not json_files:
        print("\n❌ Error: No JSON files were created in output/course_json/")
        print("   Check the PDF extraction step for errors.")
        return 1
    
    print("\n✅ Syllabus extraction complete!")
    print(f"   JSON folder: {output_folder}")
    print(f"   Courses: {len(json_files)}")
    
    # Count total topics from all JSON files
    total_topics = 0
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for course_name, course_data in data.items():
            for syllabus_key, syllabus_content in course_data.items():
                if isinstance(syllabus_content, dict) and "Units" in syllabus_content:
                    for unit in syllabus_content["Units"]:
                        total_topics += len(unit.get("Topics", []))
    
    print(f"   Total topics: {total_topics}")
    
    # Step 2: Generate AI content
    print("\n" + "="*70)
    print("  Ready to generate AI content")
    print("="*70)
    print(f"\nThis will generate detailed content for {total_topics} topics using Ollama.")
    print("Depending on syllabus size, this may take several hours.")
    
    response = input("\nStart content generation? (y/n): ")
    if response.lower() != 'y':
        print("\n⏸️  Paused. Run 'python app.py' when ready to generate content.")
        return 0
    
    if not run_command("Step 2: Generating AI Content", 
                       "app.py"):
        print("\n❌ Pipeline failed at content generation.")
        return 1
    
    print("\n" + "="*70)
    print("  🎉 PIPELINE COMPLETE!")
    print("="*70)
    print("\n✅ All content generated successfully!")
    print(f"   📁 Topic files: generated_content/")
    print(f"   📋 Summary: courseDataMap.js")
    print("\n" + "="*70 + "\n")
    
    return 0

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
