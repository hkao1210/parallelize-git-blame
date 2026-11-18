"""Dense summary algebra. Integers are zero-based older-boundary line indices."""
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class Origin:
    commit: str
    line: int  # one-based line at introduction

Entry = Union[int, Origin]

def identity(size):
    return tuple(range(size))

def compose(older, newer):
    """older: B -> A; newer: C -> B; result: C -> A or terminal origin."""
    return tuple(older[x] if isinstance(x, int) else x for x in newer)
