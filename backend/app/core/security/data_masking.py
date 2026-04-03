# backend/app/core/security/data_masking.py

import re
from typing import List, Dict, Any, Optional

def mask_pii(text: str) -> str:
    """
    Masks common Personally Identifiable Information (PII) like CPF, email, and phone numbers.
    CPF: Replaces numbers with '*' except for the last two digits.
    Email: Masks username part, keeps domain.
    Phone: Masks most digits, keeps last four.
    """
    if not isinstance(text, str):
        return text

    # Mask CPF (e.g., XXX.XXX.XXX-XX or XXXXXXXXXXX)
    # 11 digits, with or without dots and hyphens
    text = re.sub(r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})', 
                  lambda m: '***.***.***-' + m.group(1)[-2:], text)
    
    # Mask Email
    text = re.sub(r'(\b[a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b)', 
                  lambda m: '***@' + m.group(2), text)

    # Mask Phone Numbers (e.g., (XX) XXXXX-XXXX or XXXXXXXXX)
    # Simple mask: keep country code if present, and last 4 digits
    # (NN) NNNNN-NNNN
    text = re.sub(r'(\(?\d{2}\)?\s?\d{4,5}-?\d{4})', 
                  lambda m: re.sub(r'\d(?=\d{4})', '*', m.group(1)), text)
    
    return text

def get_pii_summary(text: str) -> Dict[str, List[str]]:
    """
    Detects and categorizes types of PII present in the text.
    Returns a dictionary with PII types as keys and detected PII fragments as values.
    """
    if not isinstance(text, str):
        return {}

    pii_found: Dict[str, List[str]] = {
        "cpf": [],
        "email": [],
        "phone": []
    }

    # Detect CPF
    cpf_matches = re.findall(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', text)
    if cpf_matches:
        pii_found["cpf"].extend(cpf_matches)

    # Detect Email
    email_matches = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text)
    if email_matches:
        pii_found["email"].extend(email_matches)

    # Detect Phone Numbers
    phone_matches = re.findall(r'(\(?\d{2}\)?\s?\d{4,5}-?\d{4})', text)
    if phone_matches:
        pii_found["phone"].extend(phone_matches)
    
    return {k: list(set(v)) for k, v in pii_found.items() if v} # Remove duplicates and empty lists

