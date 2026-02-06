# backend/app/core/security/input_validator.py

import re

def sanitize_username(username: str) -> str:
    """
    Sanitizes a username by allowing only alphanumeric characters and underscores.
    """
    if not isinstance(username, str):
        raise TypeError("Username must be a string.")
    
    # Remove any characters that are not alphanumeric or underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', username)
    return sanitized

def validate_password_strength(password: str) -> bool:
    """
    Validates password strength based on a set of criteria:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    
    return True

def sanitize_sql_input(text: str) -> str:
    """
    Sanitizes text to prevent SQL injection.
    This is a basic sanitization. For actual database queries, parameterized queries
    or ORMs should always be preferred. This function is mainly for sanitizing
    input that might eventually be part of a dynamic query (e.g., column names)
    or used in a context where full parameterization is not possible.
    """
    if not isinstance(text, str):
        raise TypeError("Input for SQL sanitization must be a string.")

    # Remove or escape common SQL injection characters
    # This is an example; a robust solution might need more context-aware escaping
    sanitized = text.replace("'", "''") # Escape single quotes
    sanitized = sanitized.replace(";", "") # Remove semicolons
    sanitized = sanitized.replace("--", "") # Remove SQL comments
    sanitized = sanitized.replace("/*", "") # Remove multi-line comments
    sanitized = sanitized.replace("*/", "")
    
    # Further sanitization could involve whitelisting allowed characters
    # For user-provided column names, you might only allow a-z, A-Z, 0-9, _
    sanitized = re.sub(r'[^\w\s.-]', '', sanitized) # Allow word chars, space, dot, dash
    
    return sanitized

if __name__ == '__main__':
    print("--- Username Sanitization ---")
    print(f"Original: 'user@name-123!' -> Sanitized: '{sanitize_username('user@name-123!')}'")
    print(f"Original: 'valid_user_42' -> Sanitized: '{sanitize_username('valid_user_42')}'")

    print("\n--- Password Strength Validation ---")
    print(f"'Password123!' is strong: {validate_password_strength('Password123!')}")
    print(f"'weakpass' is strong: {validate_password_strength('weakpass')}")
    print(f"'NoDigit!' is strong: {validate_password_strength('NoDigit!')}")
    print(f"'NoSpecial1' is strong: {validate_password_strength('NoSpecial1')}")

    print("\n--- SQL Input Sanitization ---")
    print(f"Original: 'DROP TABLE users;--' -> Sanitized: '{sanitize_sql_input('DROP TABLE users;--')}'")
    print(f"Original: '1 OR 1=1' -> Sanitized: '{sanitize_sql_input('1 OR 1=1')}'")
    print(f"Original: 'valid_column_name' -> Sanitized: '{sanitize_sql_input('valid_column_name')}'")
