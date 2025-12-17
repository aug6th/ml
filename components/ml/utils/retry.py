from __future__ import annotations

import asyncio
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                        continue
                    raise
            raise RuntimeError("Max retries exceeded")
        return wrapper
    return decorator

