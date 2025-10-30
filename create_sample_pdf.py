"""
Helper script to create a sample PDF for testing the entity analyzer.
"""

import fitz
from pathlib import Path


def create_sample_pdf():
    """Create a sample PDF with text containing named entities."""
    
    # Sample text with various named entities
    sample_texts = [
        """
        Apple Inc. was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne 
        in Cupertino, California in 1976. The company is headquartered in 
        Apple Park and has offices in New York, London, and Tokyo.
        """,
        """
        The United Nations held a conference in Geneva, Switzerland last month. 
        Secretary-General António Guterres addressed world leaders from France, 
        Germany, Japan, and Brazil about climate change initiatives.
        """,
        """
        Microsoft Corporation, led by CEO Satya Nadella, announced a partnership 
        with OpenAI. The collaboration will focus on artificial intelligence 
        research in Seattle, Washington and San Francisco, California.
        """,
        """
        The European Union, based in Brussels, Belgium, includes member states 
        such as Spain, Italy, Poland, and Sweden. President Ursula von der Leyen 
        discussed new policies with representatives from the European Parliament.
        """
    ]
    
    # Create PDF
    doc = fitz.open()
    
    for i, text in enumerate(sample_texts, 1):
        page = doc.new_page(width=595, height=842)  # A4 size
        
        # Add title
        title_rect = fitz.Rect(50, 50, 545, 100)
        page.insert_textbox(
            title_rect,
            f"Page {i}: Sample Document",
            fontsize=16,
            fontname="helv",
            color=(0, 0, 0)
        )
        
        # Add content
        content_rect = fitz.Rect(50, 120, 545, 792)
        page.insert_textbox(
            content_rect,
            text.strip(),
            fontsize=11,
            fontname="helv",
            color=(0, 0, 0),
            align=0
        )
    
    # Save PDF
    output_path = Path("sample_document.pdf")
    doc.save(output_path)
    doc.close()
    
    print(f"✓ Sample PDF created: {output_path}")
    print(f"  - {len(sample_texts)} pages")
    print(f"  - Contains multiple named entities for testing")


if __name__ == "__main__":
    create_sample_pdf()

