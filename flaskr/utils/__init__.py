def validate_string(value: str) -> bool:
    if not (value and isinstance(value, str) and len(value) > 4):
        return False
    return True
