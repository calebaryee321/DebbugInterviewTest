"""
PDF Entity Analyzer

Extracts text from PDFs and identifies named entities using spaCy.
This code has 7 bugs - find and fix them!
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
        doc = fitz.open(pdf_path)
        
        for page_num in range(1, len(doc) + 1):  # BUG 1
            page = doc[page_num]
            text = page.get_text()
            text_content.append(text)
        
        return " ".join(text_content)  # BUG 2
    
    def analyze_entities(self, text):
        """Process text and extract named entities."""
        if not text:
            return {}
        
        doc = self.nlp(text[:1000])  # BUG 3
        
        entity_counts = defaultdict(int)
        
        for ent in doc.ents:
            self.entities[ent.label_].append(ent.text)
            entity_counts[ent.text] += 1  # BUG 4
        
        return entity_counts
    
    def get_entity_summary(self):
        """Get a summary of entities by type."""
        summary = {}
        for entity_type, entities in self.entities.items():
            summary[entity_type] = {
                "count": len(entities),
                "unique": entities  # BUG 5
            }
        return summary
    
    def save_results(self, output_path, results):
        """Save analysis results to a JSON file."""
        f = open(output_path, 'w')  # BUG 6
        json.dump(results, f, indent=2)
    
    def process_pdf(self, pdf_path, output_path):
        """Main processing pipeline."""
        print(f"Processing: {pdf_path}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(text)} characters")
        
        # Analyze entities
        entity_counts = self.analyze_entities(text)
        print(f"Found {len(entity_counts)} entities")
        
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
    """Main entry point."""
    pdf_path = Path("sample_document.pdf")  # BUG 7
    output_path = Path("analysis_results.json")
    
    analyzer = PDFEntityAnalyzer()
    analyzer.process_pdf(pdf_path, output_path)
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()

