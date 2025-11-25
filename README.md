# BSC Course Content Generator

Generate rich academic study material from syllabus PDFs using a two‑stage pipeline:

1. Extract: `extract_syllabus.py` → builds individual course JSONs in `output/course_json/` + PDF summaries
2. Generate: `app.py` → produces per‑topic JSON + consolidated `courseDataMap.js`

## 🔍 Overview

This project lets you drop multiple syllabus PDFs in `input/`, automatically parse unit/topic structures with resources (textbooks, references, web links) and course outcomes, generate PDF summaries, and then use a local Ollama model to create deep postgraduate‑level educational content (notes, formulas, real‑world applications) per topic.

## ✨ Features

- Automated PDF → individual course JSONs (robust unit/topic extraction)
- Resource extraction (textbooks, reference books, web resources)
- Course outcomes (CO) extraction and mapping
- PDF summary generation with reportlab
- LLM content generation (streamed, cleaned, JSON‑validated)
- Per‑topic JSON artifacts + consolidated JavaScript map
- JSON cleaning & fallback for malformed outputs
- Resume capability (remove completed topics to continue)
- Clean, organized output structure

## 📁 Current Structure
```
FolderName/
├── input/                # Place syllabus PDFs here
├── output/
│   ├── course_json/      # Individual course JSON files (one per PDF)
│   └── generated_pdfs/   # PDF summaries with units, outcomes, resources
├── generated_content/    # Valid per-topic JSON files
├── generation_errors/    # Raw LLM outputs that could not be cleaned
├── extract_syllabus.py   # PDF parsing → course JSONs + PDF summaries
├── app.py                # AI generation → topic JSON + courseDataMap.js
├── run_pipeline.py       # Orchestrates extraction then generation
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── QUICKSTART.md         # Fast setup steps
└── USAGE.md              # Detailed usage & troubleshooting
```

## 🛠 Prerequisites

- Python 3.10+ (virtual environment recommended)
- Ollama installed and running (`ollama serve` auto on most platforms)
- Pulled model (default used here: `gemma3:4b`) – choose smaller for speed or larger for depth

## ⚙️ Installation
```bash
pip install -r requirements.txt
ollama pull gemma3:4b   # or gemma2:2b / llama3.2 / phi3
```

## 🚀 Usage Paths

### 1. Full Pipeline (Extract + Generate)
```bash
python run_pipeline.py
```
Prompts you after extraction before starting generation.

### 2. Extract Only
```bash
python extract_syllabus.py
```
Produces individual course JSONs in `output/course_json/` and PDF summaries in `output/generated_pdfs/`.

### 3. Generate From Existing Syllabus
```bash
python app.py
```
Reads all JSON files from `output/course_json/` and writes topic files + `courseDataMap.js`.

### 4. Resume After Interruption
Remove completed topics from individual course JSON files in `output/course_json/` or delete unfinished JSONs in `generated_content/` then rerun `python app.py`.

## 🧠 Configuration (`app.py`)
```python
INPUT_FOLDER = Path("output/course_json")
OLLAMA_MODEL = "gemma3:4b"      # swap for speed/size
LLM_RETRIES = 1                  # increase if transient failures
TOPIC_OUTPUT_DIR = Path("generated_content")
ERROR_OUTPUT_DIR = Path("generation_errors")
```

## 📤 Output Formats

Per‑topic JSON (example):
```json
{
  "notes": [{"title": "Concept", "points": ["Point A", "Point B"]}],
  "formulas": [{"title": "Rate Law", "formula": "v = k[A]", "explanation": "Mechanistic reasoning..."}],
  "realworld": [{"title": "Industrial Bioreactor", "concept": "Scale‑up", "description": "Application narrative..."}]
}
```

`courseDataMap.js` (excerpt):
```javascript
export const courseDataMap = {
  "Course_Name": {
    "Course_Name_Syllabus": [
      { "id": 1, "chapterName": "Unit Title", "topics": [ {"name": "Topic", "notes": [...]} ] }
    ]
  }
};
```

## ⏱ Performance (Typical)

- Extraction: ~1–5 s per PDF
- Generation: ~5–10 min per topic (model + complexity dependent)
- 300 topics → multi‑hour (overnight recommended)

## 🔧 Troubleshooting Quick Table

| Symptom                                  | Fix |
|------------------------------------------|-----|
| `No PDF files found`                     | Place PDFs in `input/` then rerun extraction |
| `Model not found`                        | `ollama pull gemma3:4b` (or chosen model) |
| Very slow generation                     | Use smaller model (`gemma2:2b`), reduce topics, run overnight |
| Many files in `generation_errors/`       | Increase `LLM_RETRIES`, inspect raw output, prune problematic topics |
| JSON parse failures                      | Cleaner runs automatically; truly broken outputs land in errors folder |

## ♻️ Regeneration Patterns

Full reset:
```bash
rm -rf generated_content generation_errors courseDataMap.js
python app.py
```

Add new PDFs later:
```bash
cp NEW*.pdf input/
python extract_syllabus.py
python app.py
```

## 🔐 Data Quality Tips

- Ensure syllabus tables have clear Unit/CO markers
- Use consistent PDF formatting (export from source if possible)
- Prefer text‑based PDFs (image scans reduce accuracy)
- Optionally manually adjust individual JSON files in `output/course_json/` before generation
- Check generated PDF summaries in `output/generated_pdfs/` to verify extraction

## 🤝 Integration

Import in a web app:
```javascript
import { courseDataMap } from './courseDataMap.js';
// traverse courses → subjects → units → topics
```

## ✅ What To Do Next
1. Drop PDFs into `input/`
2. Run pipeline or individual steps
3. Inspect first few generated topic JSONs
4. Adjust model / retry settings if needed
5. Let full generation run to completion

## 📄 License & Use
Use freely for internal academic content generation. Add your own license file if distributing.

## 🙋 Support Checklist Before Asking
1. Do JSON files exist in `output/course_json/` and look structured?
2. Are PDF summaries generated in `output/generated_pdfs/`?
3. Is Ollama running and model pulled? (`ollama list`)
4. Any network / timeout errors printed?
5. Are malformed outputs isolated in `generation_errors/`?

If yes to all and still blocked, inspect a failing raw file and simplify the topic wording.

---
Enjoy building rich academic datasets locally. 🚀
#
