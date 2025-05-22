# File: app/utils/result.py
# (Content as previously generated, verified)
from typing import TypeVar, Generic, List, Any, Optional

T = TypeVar('T')

class Result(Generic[T]):
    def __init__(self, is_success: bool, value: Optional[T] = None, errors: Optional[List[str]] = None):
        self.is_success = is_success
        self.value = value
        self.errors = errors if errors is not None else []

    @staticmethod
    def success(value: Optional[T] = None) -> 'Result[T]':
        return Result(is_success=True, value=value)

    @staticmethod
    def failure(errors: List[str]) -> 'Result[Any]': 
        return Result(is_success=False, errors=errors)

    def __repr__(self):
        if self.is_success:
            return f"<Result success={True} value='{str(self.value)[:50]}'>"
        else:
            return f"<Result success={False} errors={self.errors}>"
