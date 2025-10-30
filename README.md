# 🐛 Debugging Practice

**Fix 7 bugs in a Python PDF text analyzer using PyMuPDF and spaCy.**

## Quick Start

```bash
# Setup
./setup.sh

# Create test PDF
python create_sample_pdf.py

# Run the buggy code
python pdf_entity_analyzer.py
```

## Your Task

The file `pdf_entity_analyzer.py` has **7 bugs**. Find and fix them all.

**The bugs:**
1. Array indexing error
2. Unclosed file/document
3. Only processing partial text
4. Wrong dictionary key in counting
5. Not removing duplicates
6. File handle not closed
7. No error handling

## How to Practice

1. **Read the code** - Understand what it's supposed to do
2. **Run it** - See what breaks: `python pdf_entity_analyzer.py`
3. **Fix bugs** - One at a time
4. **Test** - Run again after each fix

## Debugging Tips

**Add print statements:**
```python
print(f"DEBUG: page {i} of {len(doc)}")
print(f"DEBUG: text length = {len(text)}")
```

**Use Python debugger:**
```python
import pdb; pdb.set_trace()  # Pause here
# Commands: n (next), s (step), c (continue), p var (print)
```

**Check your assumptions:**
- Are you looping through ALL pages?
- Is the file/document being closed?
- Are you processing the FULL text?
- Are you using the right dictionary keys?

## When Stuck

Check `SOLUTION.md` for hints (one bug at a time - don't spoil all!)

## Test Your Fixes

Run the test suite to verify everything works:
```bash
pytest test_analyzer.py -v
```

## What Success Looks Like

When all bugs are fixed:
- No errors when running
- Processes all 4 pages of the sample PDF
- Creates `analysis_results.json` with entity data
- All files close properly
- All tests pass ✅

---

**Just start fixing!** The best way to learn is by doing. 🐛➡️✨

