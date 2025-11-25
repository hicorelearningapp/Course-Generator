
import requests
import os
import time
from pathlib import Path
import json
import re
from typing import Tuple, Dict, Any, List

# ========== CONFIG ==========
# Input: All JSON files from output/course_json/ folder
INPUT_FOLDER = Path("output/course_json")
OUTPUT_JS = "courseDataMap.js"

# Output directories for per-topic saving
TOPIC_OUTPUT_DIR = Path("generated_content")
ERROR_OUTPUT_DIR = Path("generation_errors")

TOPIC_OUTPUT_DIR.mkdir(exist_ok=True)
ERROR_OUTPUT_DIR.mkdir(exist_ok=True)

# OLLAMA CONFIG
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma3:4b"   # optimized model

# LLM retry/backoff settings
LLM_RETRIES = 1
RETRY_BACKOFF = 2.0

# ==========================================
# RULE-BASED JSON CLEANER (your system)
# ==========================================
def rule_based_clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"([,.!?;:])([A-Za-z0-9])", r"\1 \2", text)
    text = re.sub(r"([!?.,])\1+", r"\1", text)

    text = text.replace("“", "\"").replace("”", "\"")
    text = text.replace("‘", "'").replace("’", "'")

    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text)
    return text


def clean_json_recursively(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: clean_json_recursively(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_recursively(x) for x in obj]
    elif isinstance(obj, str):
        return rule_based_clean(obj)
    return obj


def strip_markdown_fences(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```json\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.replace("```", "")
    return raw.strip()


def preprocess_json(raw: str) -> str:
    raw = raw.replace("\r\n", "\n")
    raw = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", "", raw)

    raw = raw.replace("“", "\"").replace("”", "\"")
    raw = raw.replace("‘", "'").replace("’", "'")

    raw = raw.replace("\\ ", "\\\\ ")

    raw = re.sub(
        r"\"([^\"\\]*(?:\\.[^\"\\]*)*)\n([^\"\\]*(?:\\.[^\"\\]*)*)\"",
        lambda m: f"\"{m.group(1)} {m.group(2)}\"",
        raw
    )

    raw = raw.replace("```json", "").replace("```", "")
    return raw.strip()


def try_clean_and_parse(raw: str):
    """Run preprocessing + parse + rule-based cleaning."""
    raw = strip_markdown_fences(raw)
    raw = preprocess_json(raw)

    try:
        data = json.loads(raw)
    except Exception:
        return None, raw  # failed completely

    data = clean_json_recursively(data)
    return data, raw

# FUNCTION: Call Ollama (system + user prompt)
def call_ollama(system_prompt: str, user_prompt: str) -> str:
    """Robust Ollama caller that handles NDJSON and accumulates streamed content."""
    for attempt in range(1, LLM_RETRIES + 1):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                },
                stream=True,
                timeout=300
            )

            if response.status_code != 200:
                print(f"❌ Ollama status {response.status_code}: {response.text}")
                continue

            collected = []

            # Ollama returns NDJSON — read line by line
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except:
                    continue

                # 1st priority: "message": {"content": "…"}
                if "message" in data and "content" in data["message"]:
                    collected.append(data["message"]["content"])

                # 2nd priority: plain "content"
                elif "content" in data:
                    collected.append(data["content"])

                # 3rd: output inside choices (rare)
                elif "choices" in data:
                    for c in data["choices"]:
                        if "message" in c and "content" in c["message"]:
                            collected.append(c["message"]["content"])
                        elif "text" in c:
                            collected.append(c["text"])

            final_text = "".join(collected).strip()
            return final_text

        except Exception as e:
            print(f"❌ Ollama exception: {e}")
            time.sleep(1)

    return ""

# FUNCTION: Generate topic content (sequential)
def generate_topic_content(class_name, subject, chapter_name, topic) -> Tuple[Dict[str, Any], bool, str]:
    """Generate one topic’s content using Ollama.

    Returns (parsed_json_or_empty_dict, is_error_flag, raw_text).
    """

    SYSTEM_PROMPT = """
You are an expert academic faculty and advanced AI academic content generator.
You ALWAYS output valid, strict JSON with no text outside the JSON.

CORE RULES:
- Your output must be a valid JSON object.
- The FIRST character must be '{' and the LAST character must be '}'.
- Do NOT output markdown, explanations, natural language, or commentary outside JSON.
- Do NOT include code fences.
- Maintain appropriate academic level depth with advanced concepts.
- Ensure high conceptual clarity, complexity, examples, and analytical depth.

CONTENT REQUIREMENTS:
- Every section must have 3 to 5 items, each with complex, detailed explanation, 3–5 sentences minimum.
- Every "points" list must have 3–5 bullet points.
- Formulas must include reasoning, interpretation, use-cases, constraints.
- Real-world sections must include practical applications, industry relevance, and real-world examples.

STRICT JSON SCHEMA:

{
  "notes": [
    {
      "title": "string",
      "points": ["string", "string"]
    }
  ],
  "formulas": [
    {
      "title": "string",
      "formula": "string",
      "explanation": "string"
    }
  ],
  "realworld": [
    {
      "title": "string",
      "concept": "string",
      "description": "string"
    }
  ]
}

If you cannot produce valid JSON, output an empty JSON object: {}
"""

    USER_PROMPT = f"""
Generate deeply detailed, university-level study material for the following topic:

Class: {class_name}
Subject: {subject}
Chapter: {chapter_name}
Topic: {topic}

Follow these rules:

1. Your response MUST be ONLY valid JSON.
2. Use the EXACT schema below:

{{
  "notes": [
    {{
      "title": "string",
      "points": ["string", "string"]
    }}
  ],
  "formulas": [
    {{
      "title": "string",
      "formula": "string",
      "explanation": "string"
    }}
  ],
  "realworld": [
    {{
      "title": "string",
      "concept": "string",
      "description": "string"
    }}
  ]
}}

3. Required output structure:
- notes: 3–5 sections, each with 3–5 long, complex points
- formulas: 2–4 sections
- realworld: 2–3 sections

4. The content MUST be:
- University/postgraduate level appropriate for the subject
- Analytical and concept-rich
- No motivational tone
- No text outside JSON

5. START with '{' and END with '}'.
"""

    raw_text = call_ollama(SYSTEM_PROMPT, USER_PROMPT)

    # Try to parse JSON directly
    try:
        parsed = json.loads(raw_text)
        return parsed, False, raw_text
    except Exception:
        # Not valid raw JSON — return empty dict flag true and raw text so caller can clean/save
        return {}, True, raw_text


# FUNCTION: Save EACH topic to its own JSON file (unchanged behaviour)
def save_topic_json(class_name, subject, chapter_name, topic, parsed_json, cleaned_raw, is_error):
    """Save the JSON (valid or invalid) for each topic."""

    # Construct safe folder structure
    dir_path = TOPIC_OUTPUT_DIR if not is_error else ERROR_OUTPUT_DIR

    class_dir = dir_path / class_name
    subject_dir = class_dir / subject
    chapter_dir = subject_dir / chapter_name

    chapter_dir.mkdir(parents=True, exist_ok=True)

    safe_topic_name = topic.replace("/", "_").replace("\\", "_")

    filename = f"{safe_topic_name}.json" if not is_error else f"{safe_topic_name}_ERROR.json"
    full_path = chapter_dir / filename

    with open(full_path, "w", encoding="utf-8") as f:
        if is_error or not parsed_json:
            f.write(cleaned_raw)
        else:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)

    print(f"📄 Saved topic JSON: {full_path}")


# JSON cleaning utilities (kept same behaviour)
def clean_and_fix_json(raw_json: str):
    """
    Cleans messy JSON:
    - Fixes curly quotes
    - Fixes mismatched/unescaped quotes
    - Fixes trailing commas
    - Removes invalid trailing characters
    - Ensures valid JSON output
    """

    cleaned = raw_json

    # 1. Replace curly quotes with straight quotes
    cleaned = cleaned.replace("“", "\"").replace("”", "\"")
    cleaned = cleaned.replace("‘", "'").replace("’", "'")

    # 2. Fix common broken quote patterns
    cleaned = cleaned.replace("',", "\",")
    cleaned = cleaned.replace("’", "'")
    cleaned = cleaned.replace("‚", "'")

    # 3. Remove trailing commas before ] or }
    cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)

    # 4. Remove trailing unmatched quotes
    cleaned = re.sub(r"\"\s*\"", "\"", cleaned)

    # 5. Fix double quotes inside JSON values
    cleaned = re.sub(r"(?<!\\)\"(?=[^:,}]*:)", "\"", cleaned)

    # 6. Remove ending stray characters like ” or '
    cleaned = re.sub(r"[\"']\s*}$", "}", cleaned)

    # 7. Try parsing — if valid JSON, return parsed + cleaned text
    try:
        parsed = json.loads(cleaned)
        return parsed, cleaned, None

    except json.JSONDecodeError as e:
        # If JSON fails, try LAST RESORT fixes

        # Escape internal double quotes inside values
        cleaned2 = re.sub(r'":\s*"([^"]*?)"', lambda m: '": "' + m.group(1).replace('"', '\\"') + '"', cleaned)

        try:
            parsed = json.loads(cleaned2)
            return parsed, cleaned2, None
        except Exception as e2:
            # Still invalid: return raw cleaned JSON and the error
            return None, cleaned, str(e2)


def _process_topic_seq(class_name, subject, chapter_name, topic):
    start = time.time()

    # Call LLM
    content_parsed, is_error, raw_text = generate_topic_content(
        class_name, subject, chapter_name, topic
    )

    # CASE 1: Perfect JSON
    if not is_error and content_parsed:
        final_topic_json = content_parsed
        final_is_error = False
        raw_to_save = raw_text

    else:
        # Try our deterministic cleaner
        cleaned, cleaned_raw = try_clean_and_parse(raw_text)

        if cleaned:
            # ✅ Cleaned successfully - this is VALID JSON, not an error!
            final_topic_json = cleaned
            final_is_error = False
            raw_to_save = cleaned_raw
        else:
            # ❌ Truly unparseable - this is an actual error
            final_topic_json = {"raw_output": raw_text}
            final_is_error = True
            raw_to_save = raw_text

    # SAVE (THIS WAS YOUR BUG!)
    try:
        save_topic_json(
            class_name,
            subject,
            chapter_name,
            topic,
            final_topic_json,
            raw_to_save,      # ✅ ALWAYS SAVE RAW OR CLEANED RAW
            final_is_error    # ✅ USE FINAL ERROR FLAG
        )
    except Exception as e:
        print(f"❌ Failed to save topic {topic}: {e}")

    elapsed = time.time() - start
    print(f"✅ Done: {class_name} | {subject} | {chapter_name} → {topic} ({elapsed:.1f}s)")

    return {
        "name": topic,
        "notes": final_topic_json.get("notes", []),
        "formulas": final_topic_json.get("formulas", []),
        "realworld": final_topic_json.get("realworld", []),
    }

# MAIN: Build course data from multiple JSON files (sequential)
def build_course_data(input_folder):
    """Iterate through all JSON files and generate courseDataMap. Sequential (one call at a time)."""
    input_path = Path(input_folder)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input folder not found: {input_path}")
    
    # Find all JSON files (excluding generated_pdfs folder)
    json_files = [f for f in input_path.glob("*.json")]
    
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {input_path}")
    
    print(f"📂 Found {len(json_files)} course JSON file(s)")
    for jf in json_files:
        print(f"   • {jf.name}")
    print()
    
    # Dynamic course map
    course_map = {}

    for json_file in json_files:
        print(f"📖 Loading: {json_file.name}")
        
        with open(json_file, "r", encoding="utf-8") as f:
            syllabus = json.load(f)
        
        for class_name, subjects in syllabus.items():
            readable_class = class_name.replace("_", " ")

            for subject, chapters in subjects.items():
                if class_name not in course_map:
                    course_map[class_name] = {}
                
                if subject not in course_map[class_name]:
                    course_map[class_name][subject] = []

                # Read list of units
                unit_list = chapters.get("Units", [])

                for chapter in unit_list:
                    chapter_id = chapter["Unit_Number"]
                    chapter_name = chapter["Unit_Name"]

                    chapter_entry = {
                        "id": chapter_id,
                        "class": readable_class,
                        "chapterName": chapter_name,
                        "title": f"Unit {chapter_id}: {chapter_name}",
                        "topics": [],
                    }

                    # ----- PROCESS TOPICS SEQUENTIALLY -----
                    for topic in chapter.get("Topics", []):
                        print(f"🧠 Generating → {readable_class} | {subject} | {chapter_name} → {topic}")
                        topic_entry = _process_topic_seq(readable_class, subject, chapter_name, topic)
                        chapter_entry["topics"].append(topic_entry)

                    # Append the full chapter AFTER processing topics
                    course_map[class_name][subject].append(chapter_entry)

    return course_map



def save_as_js(data, output_path):
    # Clean JS data before saving
    cleaned_data = clean_json_recursively(data)

    js_string = "export const courseDataMap = " + json.dumps(
        cleaned_data, indent=2, ensure_ascii=False
    ) + ";"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(js_string)

    print(f"✅ JS file generated: {output_path}")


# RUNNER
if __name__ == "__main__":
    try:
        print("🚀 Starting course content generation...")
        print(f"📂 Input folder: {INPUT_FOLDER}")
        print(f"📂 Output: {OUTPUT_JS}")
        print(f"📁 Content folder: {TOPIC_OUTPUT_DIR}")
        print(f"📁 Error folder: {ERROR_OUTPUT_DIR}")
        print()
        start_time = time.time()

        data = build_course_data(INPUT_FOLDER)
        save_as_js(data, OUTPUT_JS)

        print(f"✨ Completed in {time.time() - start_time:.2f} seconds")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
        
