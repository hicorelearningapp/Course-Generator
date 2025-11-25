"""
PDF Syllabus Extractor
Extracts syllabus structure from PDF files and generates syllabus.json
"""

import pdfplumber
import json
import re
import os
from pathlib import Path

def clean_text(text):
    """Clean and normalize text from PDF."""
    if not text:
        return ""
    return text.replace('\n', ' ').strip()

def extract_unit_name_from_objective(objective_text):
    """
    Extract a meaningful, short unit name from the course objective.
    Examples:
    - "To gain knowledge on properties and classification of viruses..." -> "Virus Properties & Classification"
    - "To understand pathogenic microorganisms of viruses..." -> "Viral Pathogenesis & Disease Mechanisms"
    - "To gain knowledge about reemerging viral infections..." -> "Emerging & Reemerging Viral Infections"
    - "Understand the types of parasites causing infections..." -> "Parasitic Infections"
    - "To develop skills in the diagnosis of parasitic infections" -> "Parasitic Diagnosis Techniques"
    """
    if not objective_text or len(objective_text.strip()) < 5:
        return "Unit Content"
    
    text_lower = objective_text.lower()
    
    # Define patterns and corresponding short names
    if "properties and classification of viruses" in text_lower:
        return "Virus Properties & Classification"
    elif "pathogenic microorganisms of viruses" in text_lower or "mechanisms by which they cause" in text_lower:
        return "Viral Pathogenesis & Disease Mechanisms"
    elif "reemerging viral infections" in text_lower or "diagnostic skills" in text_lower and "viral" in text_lower:
        return "Emerging & Reemerging Viral Infections"
    elif "types of parasites" in text_lower and "intestine" in text_lower:
        return "Intestinal Parasitic Infections"
    elif "diagnosis of parasitic" in text_lower or "skills in the diagnosis" in text_lower:
        return "Parasitic Diagnosis Techniques"
    else:
        # Fallback: extract key nouns and create a generic name
        # Remove common starter phrases (case-insensitive)
        text = objective_text.strip()
        
        # List of phrases to remove (in order of length, longest first for better matching)
        starter_phrases = [
            "To gain knowledge on", "To gain knowledge about", "To gain knowledge",
            "To develop skills in", "To develop skills", 
            "Gain knowledge on", "Gain knowledge about", "Gain knowledge",
            "Learn the", "Learn to", "Learn about", "Learn",
            "To understand the", "To understand", "Understand the", "Understand",
            "To acquire knowledge on", "To acquire knowledge", "Acquire knowledge",
            "To study the", "To study", "Study the", "Study",
            "Explain the", "Explain", "Discuss the", "Discuss",
            "Illustrate the", "Illustrate", "Demonstrate the", "Demonstrate",
            "Impart knowledge on", "Impart knowledge", 
            "Practice the", "Practice", "Observe the", "Observe",
            "Learning objectives:", "Learning objective:",
            "The", "A", "An"
        ]
        
        # Try removing phrases iteratively (some objectives have multiple)
        changed = True
        while changed:
            changed = False
            for phrase in starter_phrases:
                if text.lower().startswith(phrase.lower()):
                    text = text[len(phrase):].strip()
                    # Remove leading comma, colon, dash, or "on/about" connectors
                    text = text.lstrip(',:- ')
                    # If it starts with "on " or "about " after removal, remove those too
                    if text.lower().startswith("on "):
                        text = text[3:].strip()
                    elif text.lower().startswith("about "):
                        text = text[6:].strip()
                    changed = True
                    break
        
        # Take first 5-8 words and capitalize, but stop at natural boundaries
        words = text.split()[:8]  # Take up to 8 words
        short_name = ' '.join(words)
        
        # Remove trailing connectors and punctuation
        while short_name and short_name.split()[-1].lower() in ['and', 'or', 'the', 'of', 'in', 'on', 'with', 'to', 'for', 'by', 'at']:
            short_name = ' '.join(short_name.split()[:-1])
        
        # Remove trailing commas, periods, and other punctuation
        short_name = short_name.rstrip(',.;:- ')
        
        # If still empty or too short, return generic name
        if not short_name or len(short_name) < 5:
            return "Unit Content"
        
        # Capitalize properly (title case)
        return short_name.title()

def extract_syllabus(pdf_path):
    """Extract syllabus data from a PDF file."""
    units = []
    course_objectives = {}
    course_outcomes = {}
    resources = {
        "text_books": [],
        "reference_books": [],
        "web_resources": []
    }
    current_unit = None
    state = "LOOKING_FOR_OBJECTIVES"
    current_resource_type = None
    
    roman_to_int = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 2:
                        continue
                    
                    col0 = str(row[0]).strip() if row[0] else ""
                    col1 = str(row[1]).strip() if row[1] else ""
                    
                    # Extract course objectives
                    if state == "LOOKING_FOR_OBJECTIVES":
                        if col0.startswith("CO") and col0[2:].isdigit():
                            co_num = int(col0[2:])
                            objective_text = ""
                            for cell in row[1:]:
                                if cell and len(str(cell).strip()) > 20:
                                    objective_text = clean_text(str(cell))
                                    break
                            if objective_text:
                                short_name = extract_unit_name_from_objective(objective_text)
                                course_objectives[co_num] = short_name
                        elif ("Unit" in col0 or "UNIT" in col0) and ("Details" in col1 or any("Details" in str(c) for c in row if c)):
                            state = "PROCESSING_UNITS"
                            continue
                    
                    if state == "PROCESSING_UNITS":
                        # Check if it's a new unit (Roman Numeral)
                        if col0 in roman_to_int:
                            # Save previous unit
                            if current_unit:
                                units.append(current_unit)
                            
                            unit_num = roman_to_int[col0]
                            raw_text = ""
                            for cell in row[1:]:
                                if cell and len(str(cell).strip()) > 20:
                                    raw_text = clean_text(str(cell))
                                    break
                            
                            # Get unit name from course objective
                            unit_name = f"Unit {col0}"
                            for cell in row:
                                if cell and str(cell).strip().startswith("CO") and str(cell).strip()[2:].isdigit():
                                    co_num = int(str(cell).strip()[2:])
                                    unit_name = course_objectives.get(co_num, unit_name)
                                    break
                            
                            current_unit = {
                                "Unit_Number": unit_num,
                                "Unit_Name": unit_name,
                                "Raw_Content": raw_text
                            }
                        
                        # Continuation of unit content
                        elif (not col0 or col0 == '') and current_unit:
                            for cell in row[1:]:
                                if cell and len(str(cell).strip()) > 10:
                                    current_unit["Raw_Content"] += " " + clean_text(str(cell))
                                    break
                        
                        # End of units section
                        elif "Total" in col1 or "Course Outcomes" in col0:
                            if current_unit:
                                units.append(current_unit)
                                current_unit = None
                            state = "LOOKING_FOR_OUTCOMES"
                            continue
                    
                    # Extract course outcomes
                    if state == "LOOKING_FOR_OUTCOMES":
                        if col0.startswith("CO") and col0[2:].isdigit():
                            co_num = int(col0[2:])
                            outcome_text = ""
                            for cell in row[1:]:
                                if cell and len(str(cell).strip()) > 20:
                                    outcome_text = clean_text(str(cell))
                                    break
                            if outcome_text:
                                course_outcomes[co_num] = outcome_text
                        elif "Text Books" in col0 or "Text Books" in str(row):
                            state = "LOOKING_FOR_RESOURCES"
                            current_resource_type = "text_books"
                            continue
                    
                    # Extract resources
                    if state == "LOOKING_FOR_RESOURCES":
                        # Check for section headers
                        if "References Books" in col0 or "Reference Books" in col0:
                            current_resource_type = "reference_books"
                            continue
                        elif "Web Resources" in col0:
                            current_resource_type = "web_resources"
                            continue
                        elif "Methods of Evaluation" in col0 or "Methods of Assessment" in col0:
                            state = "DONE"
                            break
                        
                        # Extract resource entries (numbered items)
                        if col0 and (col0.isdigit() or col0.endswith('.')):
                            resource_text = ""
                            for cell in row[1:]:
                                if cell and len(str(cell).strip()) > 10:
                                    resource_text = clean_text(str(cell))
                                    break
                            if resource_text and current_resource_type:
                                resources[current_resource_type].append(resource_text)
                
                if state == "DONE":
                    break
            if state == "DONE":
                break
    
    # Post-process units to split topics
    final_units = []
    int_to_roman = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI'}
    
    for unit in units:
        raw = unit["Raw_Content"]
        
        # Multi-stage topic splitting:
        # 1. First split by periods (.) - strongest boundary
        # 2. Then split by semicolons (;) - medium boundary
        # 3. Keep commas (,) within same topic - weak/no boundary
        
        topics = []
        current_topic = ""
        paren_depth = 0
        i = 0
        
        while i < len(raw):
            char = raw[i]
            
            if char == '(':
                paren_depth += 1
                current_topic += char
            elif char == ')':
                paren_depth -= 1
                current_topic += char
            elif char == '.' and paren_depth == 0:
                # Check if this is end of sentence (not an abbreviation)
                # Look ahead to see if next char is space or end of string
                if i + 1 < len(raw) and raw[i + 1] in [' ', '\n', '\t']:
                    current_topic += char
                    # This is end of a topic - split it
                    if current_topic.strip():
                        topics.append(current_topic.strip())
                    current_topic = ""
                elif i + 1 >= len(raw):
                    # End of string
                    current_topic += char
                    if current_topic.strip():
                        topics.append(current_topic.strip())
                    current_topic = ""
                else:
                    # Likely an abbreviation like "Dr." or decimal, keep it
                    current_topic += char
            elif char == ';' and paren_depth == 0:
                # Semicolon is also a topic boundary
                current_topic += char
                if current_topic.strip():
                    topics.append(current_topic.strip())
                current_topic = ""
            else:
                current_topic += char
            
            i += 1
        
        # Add the last topic if exists
        if current_topic.strip():
            topics.append(current_topic.strip())
        
        # Post-process: detect list patterns and split further if needed
        # Pattern: "word1 - detail1, word2 - detail2, word3 - detail3"
        # This indicates a list that should be split
        final_topics = []
        for topic in topics:
            # Check if topic has multiple "X – Y" or "X - Y" patterns separated by commas
            # Count how many times we see "word(s) [–-] word(s)," pattern
            dash_comma_count = len([m for m in re.finditer(r'\w+\s*[–-]\s*[^,]+,', topic)])
            
            # If we have 3+ such patterns, it's likely a list that should be split
            if dash_comma_count >= 3:
                # Split by comma, but this is aggressive - only for list-like content
                parts = topic.split(',')
                for part in parts:
                    if part.strip():
                        final_topics.append(part.strip())
            else:
                # Keep as-is
                final_topics.append(topic)
        
        topics = final_topics
        
        # Don't remove first topic - it contains actual content
        # The unit name is derived from course objectives, not from topics
        
        final_units.append({
            "Unit_Number": unit["Unit_Number"],
            "Unit_Name": unit["Unit_Name"],
            "Topics": topics
        })
    
    return {
        "units": final_units,
        "course_outcomes": course_outcomes,
        "resources": resources
    }

def sanitize_course_name(filename):
    """Create a clean course name from filename."""
    name = os.path.splitext(filename)[0]
    # Remove special characters except underscores and spaces
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces and hyphens with underscores
    name = re.sub(r'[-\s]+', '_', name)
    return name

def generate_pdf_summary(syllabus_data, course_name, output_path):
    """Generate a PDF summary for a course."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = styles['Heading1']
        title_style.alignment = 1  # Center
        story.append(Paragraph(f"{course_name.replace('_', ' ')} Summary", title_style))
        story.append(Spacer(1, 12))
        
        # Units
        units = syllabus_data.get("units", [])
        if units:
            story.append(Paragraph("Course Units", styles['Heading2']))
            story.append(Spacer(1, 6))
            
            for unit in units:
                unit_header = f"Unit {unit['Unit_Number']}: {unit['Unit_Name']}"
                story.append(Paragraph(unit_header, styles['Heading3']))
                
                for topic in unit['Topics']:
                    story.append(Paragraph(f"• {topic}", styles['Normal']))
                
                story.append(Spacer(1, 12))
        
        # Course Outcomes
        outcomes = syllabus_data.get("course_outcomes", {})
        if outcomes:
            story.append(Paragraph("Course Outcomes", styles['Heading2']))
            for co_num in sorted(outcomes.keys()):
                story.append(Paragraph(f"<b>CO{co_num}:</b> {outcomes[co_num]}", styles['Normal']))
                story.append(Spacer(1, 6))
            story.append(Spacer(1, 12))
        
        # Resources
        resources = syllabus_data.get("resources", {})
        
        if resources.get("text_books"):
            story.append(Paragraph("Text Books", styles['Heading2']))
            for i, book in enumerate(resources["text_books"], 1):
                story.append(Paragraph(f"{i}. {book}", styles['Normal']))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 12))
        
        if resources.get("reference_books"):
            story.append(Paragraph("Reference Books", styles['Heading2']))
            for i, book in enumerate(resources["reference_books"], 1):
                story.append(Paragraph(f"{i}. {book}", styles['Normal']))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 12))
        
        if resources.get("web_resources"):
            story.append(Paragraph("Web Resources", styles['Heading2']))
            for i, resource in enumerate(resources["web_resources"], 1):
                story.append(Paragraph(f"{i}. {resource}", styles['Normal']))
                story.append(Spacer(1, 3))
        
        doc.build(story)
        return True
    except Exception as e:
        print(f"   ⚠️  Could not generate PDF summary: {e}")
        return False

def process_pdfs(input_folder, output_folder):
    """Process all PDFs in input folder and generate individual JSON files."""
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    json_output_path = output_path / "course_json"
    pdf_output_path = output_path / "generated_pdfs"
    
    if not input_path.exists():
        print(f"❌ Error: Input folder '{input_folder}' not found.")
        print(f"   Please create the folder and add PDF files.")
        return False
    
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ Error: No PDF files found in '{input_folder}'")
        print(f"   Please add syllabus PDF files to the input folder.")
        return False
    
    print(f"\n{'='*70}")
    print(f"  PDF Syllabus Extraction")
    print(f"{'='*70}\n")
    print(f"📁 Input folder: {input_folder}")
    print(f"📄 Found {len(pdf_files)} PDF file(s):\n")
    
    for pdf in pdf_files:
        print(f"   • {pdf.name}")
    
    print(f"\n🔄 Processing...\n")
    
    # Create output directories
    json_output_path.mkdir(parents=True, exist_ok=True)
    pdf_output_path.mkdir(parents=True, exist_ok=True)
    
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        pdf_name = pdf_file.name
        print(f"📖 Processing: {pdf_name}")
        
        try:
            syllabus_data = extract_syllabus(str(pdf_file))
            
            if syllabus_data and syllabus_data.get("units"):
                course_name = sanitize_course_name(pdf_name)
                syllabus_key = f"{course_name}_Syllabus"
                
                # Structure each JSON: { "Course_Name": { "Course_Name_Syllabus": { "Units": [...], "resources": {...}, "course_outcomes": {...} } } }
                json_data = {
                    course_name: {
                        syllabus_key: {
                            "Units": syllabus_data["units"],
                            "resources": syllabus_data["resources"],
                            "course_outcomes": syllabus_data["course_outcomes"]
                        }
                    }
                }
                
                # Save individual JSON
                json_path = json_output_path / f"{course_name}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                
                # Generate PDF summary
                pdf_summary_path = pdf_output_path / f"{course_name}_summary.pdf"
                generate_pdf_summary(syllabus_data, course_name, str(pdf_summary_path))
                
                units = syllabus_data["units"]
                print(f"   ✅ Extracted {len(units)} units with {sum(len(u['Topics']) for u in units)} topics")
                print(f"   📄 Saved: {json_path.name}")
                print(f"   📑 PDF: {pdf_summary_path.name}")
                successful += 1
            else:
                print(f"   ⚠️  No syllabus units found")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"  Extraction Complete!")
    print(f"{'='*70}")
    print(f"✅ Successfully processed: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Output folder: {output_folder}")
    print(f"📄 Course JSONs: {json_output_path}")
    print(f"📑 PDF summaries: {pdf_output_path}")
    print(f"{'='*70}\n")
    
    return successful > 0

if __name__ == "__main__":
    input_folder = "input"
    output_folder = "output"
    
    success = process_pdfs(input_folder, output_folder)
    
    if success:
        print("✅ Ready for content generation!")
        print("   Run: python app.py")
    else:
        print("⚠️  Please fix the errors and try again.")
