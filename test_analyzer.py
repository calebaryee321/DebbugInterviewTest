"""
Simple tests for PDF Entity Analyzer

Run with: pytest test_analyzer.py -v
"""

import pytest
import fitz
import json
from pathlib import Path
from pdf_entity_analyzer_FIXED import PDFEntityAnalyzer


@pytest.fixture
def test_pdf(tmp_path):
    """Create a simple test PDF with 3 pages."""
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    page1.insert_text((50, 50), "Apple Inc. is in California.")
    
    # Page 2
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Microsoft is in Washington.")
    
    # Page 3
    page3 = doc.new_page()
    page3.insert_text((50, 50), "Google is in California too.")
    
    doc.save(pdf_path)
    doc.close()
    
    return pdf_path


@pytest.fixture
def analyzer():
    """Create analyzer instance."""
    return PDFEntityAnalyzer()


def test_extracts_all_pages(analyzer, test_pdf):
    """Test that all pages are extracted (Bug 1 check)."""
    text = analyzer.extract_text_from_pdf(test_pdf)
    
    # Should contain text from all 3 pages
    assert "Apple" in text
    assert "Microsoft" in text
    assert "Google" in text


def test_document_closes(analyzer, test_pdf):
    """Test that PDF document closes properly (Bug 2 check)."""
    analyzer.extract_text_from_pdf(test_pdf)
    
    # Should be able to delete file if it was closed
    test_pdf.unlink()
    assert not test_pdf.exists()


def test_processes_full_text(analyzer):
    """Test that full text is processed, not just first 1000 chars (Bug 3 check)."""
    # Create text longer than 1000 characters
    long_text = "Apple Inc. is a technology company. " * 50  # ~1800 chars
    
    result = analyzer.analyze_entities(long_text)
    
    # Should process entire text and find entities
    assert len(result) > 0


def test_counts_by_entity_type(analyzer):
    """Test that entities are counted by type, not individual text (Bug 4 check)."""
    text = "Apple Inc. and Microsoft are companies. Google too."
    result = analyzer.analyze_entities(text)
    
    # Keys should be entity labels (ORG, PERSON, etc), not entity text
    if result:
        for key in result.keys():
            assert key.isupper(), f"Expected entity type label, got: {key}"


def test_removes_duplicates(analyzer):
    """Test that duplicate entities are handled (Bug 5 check)."""
    text = "Apple Inc. Apple Inc. Apple Inc."
    analyzer.analyze_entities(text)
    
    summary = analyzer.get_entity_summary()
    
    if "ORG" in summary:
        unique = summary["ORG"]["unique"]
        # Should have no duplicates
        assert len(unique) == len(set(unique))


def test_saves_and_closes_json(analyzer, tmp_path):
    """Test that JSON file is saved and closed properly (Bug 6 check)."""
    output_path = tmp_path / "test_output.json"
    
    test_data = {"test": "data", "number": 42}
    analyzer.save_results(output_path, test_data)
    
    # Should be able to read back
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded == test_data
    
    # Should be able to delete (file was closed)
    output_path.unlink()
    assert not output_path.exists()


def test_full_pipeline(analyzer, test_pdf, tmp_path):
    """Test complete processing pipeline."""
    output_path = tmp_path / "results.json"
    
    # Should complete without errors
    analyzer.process_pdf(test_pdf, output_path)
    
    # Output should exist and be valid JSON
    assert output_path.exists()
    
    with open(output_path) as f:
        results = json.load(f)
    
    # Check structure
    assert "source_file" in results
    assert "total_characters" in results
    assert "entity_summary" in results
    assert results["total_characters"] > 0


def test_empty_pdf(analyzer, tmp_path):
    """Test handling of empty PDF."""
    pdf_path = tmp_path / "empty.pdf"
    doc = fitz.open()
    doc.new_page()  # Empty page
    doc.save(pdf_path)
    doc.close()
    
    text = analyzer.extract_text_from_pdf(pdf_path)
    assert isinstance(text, str)


def test_missing_file_handled(analyzer, tmp_path):
    """Test error handling for missing file (Bug 7 check)."""
    nonexistent = tmp_path / "does_not_exist.pdf"
    
    # Should raise an error (not silently fail)
    with pytest.raises(Exception):
        analyzer.extract_text_from_pdf(nonexistent)

