"""
PDF Entity Analyzer - FIXED VERSION

This is the corrected version with all bugs fixed.
"""

import fitz
import spacy
import json
from pathlib import Path
from collections import defaultdict


class PDFEntityAnalyzer:
    def __init__(self, model_name="en_core_web_sm"):
        """Initialize the analyzer with a spaCy model."""
        self.nlp = spacy.load(model_name)
        self.entities = defaultdict(list)
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from all pages of a PDF file."""
        text_content = []
        
        # FIX 1 & 2: Use context manager and correct indexing
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):  # FIX 1: Start from 0, not 1
                page = doc[page_num]
                text = page.get_text()
                text_content.append(text)
        # FIX 2: Document auto-closed by context manager
        
        return " ".join(text_content)
    
    def analyze_entities(self, text):
        """Process text and extract named entities."""
        if not text:
            return {}
        
        # FIX 3: Process entire text, not just first 1000 chars
        doc = self.nlp(text)
        
        entity_counts = defaultdict(int)
        
        for ent in doc.ents:
            self.entities[ent.label_].append(ent.text)
            # FIX 4: Count by entity label, not individual text
            entity_counts[ent.label_] += 1
        
        return entity_counts
    
    def get_entity_summary(self):
        """Get a summary of entities by type."""
        summary = {}
        for entity_type, entities in self.entities.items():
            # FIX 5: Remove duplicates for unique count
            unique_entities = list(set(entities))
            summary[entity_type] = {
                "count": len(entities),
                "unique_count": len(unique_entities),
                "examples": unique_entities[:5]  # Show up to 5 examples
            }
        return summary
    
    def save_results(self, output_path, results):
        """Save analysis results to a JSON file."""
        # FIX 6: Use context manager to ensure file is closed
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
    
    def process_pdf(self, pdf_path, output_path):
        """Main processing pipeline."""
        print(f"Processing: {pdf_path}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(text)} characters")
        
        # Analyze entities
        entity_counts = self.analyze_entities(text)
        print(f"Found {sum(entity_counts.values())} total entities")
        
        # Get summary
        summary = self.get_entity_summary()
        
        # Prepare results
        results = {
            "source_file": str(pdf_path),
            "total_characters": len(text),
            "entity_summary": summary
        }
        
        # Save results
        self.save_results(output_path, results)
        print(f"Results saved to: {output_path}")


def main():
    """Main entry point with example usage."""
    pdf_path = Path("sample_document.pdf")
    output_path = Path("analysis_results.json")
    
    # FIX 7: Add error handling
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        print("Run 'python create_sample_pdf.py' to create a sample document.")
        return
    
    try:
        analyzer = PDFEntityAnalyzer()
        analyzer.process_pdf(pdf_path, output_path)
        print("\nAnalysis complete!")
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()

