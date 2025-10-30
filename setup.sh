#!/bin/bash

echo "🚀 Setting up debugging practice..."

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
python -m spacy download en_core_web_sm -q

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. source venv/bin/activate"
echo "  2. python create_sample_pdf.py"
echo "  3. python pdf_entity_analyzer.py"
echo ""
echo "Fix the bugs, then run again!"

