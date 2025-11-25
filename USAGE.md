# Usage Guide

## Quick Reference

### Complete Workflow

```
input/          →  extract_syllabus.py  →  output/course_json/     →  app.py  →  generated_content/
[PDFs]                                    [individual course JSONs]              [topic JSON files]
                                      →  output/generated_pdfs/
                                          [PDF summaries]
```

## Step-by-Step Instructions

### 1️⃣ PDF Extraction

**Place PDFs in `input/` folder:**
```bash
input/
├── MSc_Molecular_Biology.pdf
├── BSc_Microbiology.pdf
└── MSc_Biotechnology.pdf
```

**Run extraction:** (creates individual course JSONs and PDF summaries)
```bash
python extract_syllabus.py
```

**Outputs:**
- `output/course_json/CourseName.json` - One JSON per PDF with structure:
- `output/course_json/CourseName.json` - One JSON per PDF with structure:
```json
{
  "Course_Name": {
    "Course_Name_Syllabus": {
      "Units": [
        {
          "Unit_Number": 1,
          "Unit_Name": "Unit Name",
          "Topics": ["Topic 1", "Topic 2", ...]
        }
      ],
      "resources": {
        "text_books": ["Book 1", "Book 2"],
        "reference_books": ["Reference 1"],
        "web_resources": ["URL 1"]
      },
      "course_outcomes": {
        "CO1": "Outcome description",
        "CO2": "Outcome description"
      }
    }
  }
}
```
- `output/generated_pdfs/CourseName.pdf` - PDF summary with units, outcomes, and resources

### 2️⃣ Content Generation (LLM)

**Prerequisites:**
- Ollama running (`ollama serve`)
- Model installed (`ollama pull gemma3:4b`)
- Course JSON files exist in `output/course_json/`

**Run generator:** (reads all JSON files from `output/course_json/`)
```bash
python app.py
```

**Output:**
- `generated_content/` - Individual JSON files per topic
- `courseDataMap.js` - Consolidated JavaScript map
- `generation_errors/` - Failed topics (if any)

### 3️⃣ Complete Pipeline (One command)

**Run everything:**
```bash
python run_pipeline.py
```

This will:
1. Extract from PDFs in `input/`
2. Generate individual course JSONs in `output/course_json/`
3. Generate PDF summaries in `output/generated_pdfs/`
4. Generate AI content for all topics
5. Create all output files

## Configuration

### Change LLM Model

Edit `app.py` line ~23:
```python
OLLAMA_MODEL = "gemma3:4b"   # Change to: llama3.2, phi3, etc.
```

### Change Input/Output Folders

Edit `app.py`:
```python
INPUT_FOLDER = Path("output/course_json")       # Course JSON files location
TOPIC_OUTPUT_DIR = Path("generated_content")    # Your folder name
ERROR_OUTPUT_DIR = Path("generation_errors")    # Your folder name
```

## Resume / Restart Strategy

If generation stops (crash, Ctrl+C), you can resume:

1. **Option A - Remove completed topics from course JSONs:**
   - Check `generated_content/` for completed files
   - Edit individual course JSON files in `output/course_json/` to remove those topics
   - Run `python app.py` again

2. **Option B - Start fresh:**
   - Delete `generated_content/` folder contents
   - Run `python app.py`

## Troubleshooting

### No PDFs found
```
❌ Error: No PDF files found in 'input'
```
**Fix:** Add PDF files to the `input/` folder

### Ollama not running
```
❌ Error: Failed to reach Ollama
```
**Fix:** Start Ollama with `ollama serve`

### Model not found
```
❌ Error: Model 'gemma3:4b' not found
```
**Fix:** Install model with `ollama pull gemma3:4b`

### Slow generation
- **Typical:** 5-7 minutes per topic
- **Large topics:** 10+ minutes
- **Total time:** ~6-10 hours for 80-100 topics

**Tips:**
- Use smaller models (`gemma2:2b` is faster)
- Run overnight
- Use GPU if available

## Output Format

### Topic JSON Structure (example)
```json
{
  "topic": "Topic Name",
  "notes": ["Note 1", "Note 2", "Note 3"],
  "formulas": ["Formula 1 with $$LaTeX$$", "Formula 2"],
  "realworld": ["Real-world application 1", "Application 2"]
}
```

### courseDataMap.js Structure (excerpt)
```javascript
export const courseDataMap = {
  "Course_Name": {
    "Subject_Name": {
      "Unit_Name": {
        "Topic_Name": {
          "notes": [...],
          "formulas": [...],
          "realworld": [...]
        }
      }
    }
  }
};
```

## Folder Structure (reference)

```
BSC/
├── input/                      # Place PDFs here
├── output/
│   ├── course_json/            # Individual course JSON files
│   └── generated_pdfs/         # PDF summaries with units/outcomes/resources
├── generated_content/          # Individual topic JSONs
├── generation_errors/          # Failed topics (if any)
├── extract_syllabus.py         # PDF extraction script
├── app.py                      # AI content generator
├── run_pipeline.py             # Master pipeline
├── requirements.txt            # Python dependencies
└── USAGE.md                    # This file
```

## Examples

### Process Single PDF
```bash
# 1. Add PDF to input/
cp "MSc Molecular Biology.pdf" input/

# 2. Extract
python extract_syllabus.py

# 3. Generate content
python app.py
```

### Process Multiple PDFs
```bash
# 1. Add all PDFs to input/
cp *.pdf input/

# 2. Run pipeline
python run_pipeline.py
```

### Generate Content Only (Skip PDF Extraction)
```bash
# If you already have course JSON files in output/course_json/
python app.py
```

## Tips & Best Practices

1. **PDF Quality:** Ensure PDFs have clear table structure for best extraction
2. **Naming:** Use descriptive PDF filenames (they become course names)
3. **Monitoring:** Watch console output for progress and errors
4. **Backup:** Save `output/course_json/` folder before regenerating
5. **Interruption:** Safe to Ctrl+C - resume by editing individual course JSONs
6. **Testing:** Try with 1-2 topics first before full generation
7. **Verification:** Check PDF summaries in `output/generated_pdfs/` to verify extraction quality

## Need Help?
Check:
- Are course JSON files present in `output/course_json/`?
- Are PDF summaries generated in `output/generated_pdfs/`?
- Is Ollama running (`ollama list`)?
- Are only a few files in `generation_errors/`? (Normal)

If many failures: try a smaller model or simplify topic text.

Check the following files:
- `README.md` - Full documentation
- `QUICKSTART.md` - Quick setup guide
- Console output for specific error messages
