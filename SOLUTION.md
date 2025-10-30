# Solutions

## Bug 1: Off-by-one error
**Location**: Line ~29 in `extract_text_from_pdf()`

**Problem**: `range(1, len(doc) + 1)` skips page 0 and tries to access a page that doesn't exist

**Fix**:
```python
# Change this:
for page_num in range(1, len(doc) + 1):

# To this:
for page_num in range(len(doc)):
```

## Bug 2: Document not closed
**Location**: `extract_text_from_pdf()` method

**Problem**: fitz document is never closed

**Fix**: Add `doc.close()` at the end, or use:
```python
with fitz.open(pdf_path) as doc:
    # ... your code
```

## Bug 3: Only processing 1000 characters
**Location**: Line ~42 in `analyze_entities()`

**Problem**: `self.nlp(text[:1000])` only processes first 1000 chars

**Fix**:
```python
# Change this:
doc = self.nlp(text[:1000])

# To this:
doc = self.nlp(text)
```

## Bug 4: Wrong dictionary key
**Location**: Line ~50 in `analyze_entities()`

**Problem**: `entity_counts[ent.text]` should count by entity TYPE, not individual text

**Fix**:
```python
# Change this:
entity_counts[ent.text] += 1

# To this:
entity_counts[ent.label_] += 1
```

## Bug 5: Duplicates not removed
**Location**: Line ~59 in `get_entity_summary()`

**Problem**: Returning all entities, not unique ones

**Fix**:
```python
# Change this:
"unique": entities

# To this:
"unique": list(set(entities))
```

## Bug 6: File not closed
**Location**: Line ~67 in `save_results()`

**Problem**: File opened but never closed

**Fix**: Use context manager:
```python
# Change this:
f = open(output_path, 'w')
json.dump(results, f, indent=2)

# To this:
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
```

## Bug 7: No error handling
**Location**: Line ~94 in `main()`

**Problem**: No check if file exists

**Fix**: Add check at start of main():
```python
if not pdf_path.exists():
    print(f"Error: File not found: {pdf_path}")
    print("Run 'python create_sample_pdf.py' first")
    return
```

---

## Verify Your Fixes

After fixing all bugs, run the tests:
```bash
pytest test_analyzer.py -v
```

All tests should pass! ✅

See `pdf_entity_analyzer_FIXED.py` for the complete working version.

