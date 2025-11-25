# Quick Start

### 1. Drop PDFs
Put all syllabus PDFs in `input/`.
```
input/
	CourseA.pdf
	CourseB.pdf
```

### 2. Install deps + model
```bash
pip install -r requirements.txt
ollama pull gemma3:4b   # or a smaller model
```

### 3. Run full pipeline
```bash
python run_pipeline.py
```
Answer `y` when asked to start generation.

### 4. Outputs
```
output/course_json/       # individual course JSON files (one per PDF)
output/generated_pdfs/    # PDF summaries with units, outcomes, resources
generated_content/        # per-topic JSON
generation_errors/        # malformed raw outputs (if any)
courseDataMap.js          # consolidated map
```

### Regenerate Only Content
```bash
python app.py
```

### Resume After Interruption
Remove completed topics from individual course JSON files in `output/course_json/` or leave as‑is (duplicates will just overwrite). Then rerun `python app.py`.

### Common Fixes
| Issue | Fix |
|-------|-----|
| Model not found | `ollama pull gemma3:4b` |
| No PDFs found | Place PDFs in `input/` |
| Lots of JSON errors | Increase `LLM_RETRIES` or switch model |

### Time Estimate (Approx.)
| Topics | Time |
|--------|------|
| 50     | 4–8 h |
| 100    | 8–16 h |
| 300    | Overnight+ |

Run overnight for large sets. Check early sample JSONs before letting it run long.
