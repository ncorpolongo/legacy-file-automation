import re
from typing import List, Optional

# 2+ spaces = column separators in aligned text reports
MULTISPACE = re.compile(r"\s{2,}")

DOB_GENDER_DL = re.compile(r"^(?P<dob>\d{8})(?P<gender>[MF])(?P<dl>.+)$")

def split_columns(line: str) -> List[str]:
    """
    Split one aligned-text line into tokens using 2+ spaces as separators.

    Why:
    - Single spaces can appear inside addresses (e.g., '123 Main St')
    - 2+ spaces are alignment padding between fields/columns

    Returns:
        List of non-empty, stripped tokens.
    """
    line = line.rstrip("\n")
    return [t.strip() for t in MULTISPACE.split(line) if t.strip()]

def find_anchor_index(tokens: List[str]) -> Optional[int]:
    """
    Returns the index of the token that matches the DOB+Gender+DriverLicense pattern.
    If not found, returns None.
    """
    for i, token in enumerate(tokens):
        if DOB_GENDER_DL.match(token):
            return i
    return None
