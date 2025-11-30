# tools/docs_processor.py
"""
Document processor for uploaded prescriptions / medical records.
Supports extracting text from PDF (via pdfplumber) or accepting raw text.
Provides a basic keyword extractor by splitting and filtering.
"""

import pdfplumber
import os
import re

def process_document(path_or_text):
    """
    If input is a path to an existing file, try to extract text from PDF.
    If it's a long text string, return it directly.
    """
    if isinstance(path_or_text, str) and os.path.exists(path_or_text):
        # attempt PDF text extraction
        try:
            text = ""
            with pdfplumber.open(path_or_text) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text() or ""
                    text += txt + "\n"
            return text
        except Exception as e:
            return f"[ERROR extracting PDF: {e}]"
    else:
        # assume raw text
        return str(path_or_text)

def extract_keywords(text, top_k=20):
    """
    Very simple keyword extraction:
    - Lowercase, remove punctuation
    - Return common medical-like phrases by finding ngrams of size 1-3
    This is intentionally simple; replace with an NLP extractor if available.
    """
    t = text.lower()
    # remove punctuation except hyphens
    t = re.sub(r"[^a-z0-9\s\-]", " ", t)
    tokens = [w for w in t.split() if len(w) > 2]
    # gather basic ngrams
    ngrams = set()
    for n in (1,2,3):
        for i in range(len(tokens)-n+1):
            ng = " ".join(tokens[i:i+n])
            ngrams.add(ng)
    # prioritize medical-sounding words (simple heuristic)
    prioritized = [g for g in ngrams if any(k in g for k in ["pain","pressure","diabetes","fever","cough","fracture","rash","lipid","cholesterol","blood","pressure","metformin","atorvastatin","aspirin","warfarin"])]
    if not prioritized:
        prioritized = list(ngrams)
    return prioritized[:top_k]
