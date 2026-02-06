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

# Example usage
if __name__ == '__main__':
    test_text = """
    O cliente João Silva (joao.silva@example.com) com CPF 123.456.789-00 e telefone (11) 98765-4321
    fez um pedido. Outro CPF: 99988877766. E-mail alternativo: j.silva@mail.com. Telefone comercial: 21991234567.
    """
    
    print("--- Original Text ---")
    print(test_text)

    print("\n--- Masked Text (mask_pii) ---")
    masked_text = mask_pii(test_text)
    print(masked_text)
    assert "***.***.***-00" in masked_text
    assert "***@example.com" in masked_text
    assert "(**) *****-4321" in masked_text
    assert "***@mail.com" in masked_text
    assert "**991234567" in masked_text


    print("\n--- PII Summary (get_pii_summary) ---")
    pii_summary = get_pii_summary(test_text)
    print(json.dumps(pii_summary, indent=2))
    assert "cpf" in pii_summary
    assert "email" in pii_summary
    assert "phone" in pii_summary
    assert "123.456.789-00" in pii_summary["cpf"]
    assert "joao.silva@example.com" in pii_summary["email"]
    assert "(11) 98765-4321" in pii_summary["phone"]

    print("\nData masking and PII detection tests passed!")
