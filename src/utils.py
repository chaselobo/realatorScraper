import re
import sys
from loguru import logger

def setup_logger(log_file="scraper.log"):
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(log_file, rotation="10 MB", level="DEBUG")
    return logger

def normalize_phone(phone: str) -> str:
    """Normalize phone number to ###-###-#### format."""
    if not phone:
        return ""
    
    # Remove non-digits
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
    
    return phone

def validate_email(email: str) -> bool:
    """Basic regex email validation."""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def parse_name(full_name: str):
    """Split full name into first and last name."""
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    
    return parts[0], " ".join(parts[1:])
