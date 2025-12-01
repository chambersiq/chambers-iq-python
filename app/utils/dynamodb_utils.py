from decimal import Decimal
from typing import Any, Dict, List, Union

def parse_float_to_decimal(obj: Any) -> Any:
    """
    Recursively converts float values in a dictionary or list to Decimal.
    DynamoDB requires Decimal for numbers, it does not support float.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: parse_float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [parse_float_to_decimal(v) for v in obj]
    return obj
