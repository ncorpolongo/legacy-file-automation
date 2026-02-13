import re
from typing import List

# 2+ spaces = column separators in aligned text reports
MULTISPACE = re.compile(r"\s{2,}")

def split_columns(line: str) -> List[str]:
    """
    Split one aligned-text line into tokens using 2+ spaces as separators.

    Why:
    - Single spaces can appear inside addresses (e.g., '123 Main St')
    - 2+ spaces are alignment padding between fields/columns

    Returns:
        List of non-empty, stripped tokens.
    """
    # Remove only the newline at the end; keep internal spacing intact
    line = line.rstrip("\n")

    tokens = [t.strip() for t in MULTISPACE.split(line) if t.strip()]
    return tokens
