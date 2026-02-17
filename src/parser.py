import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple

# 2+ spaces = column separators in aligned text reports
MULTISPACE = re.compile(r"\s{2,}")

# Anchor token: 8 digits DOB + M/F + rest is driver's license
DOB_GENDER_DL = re.compile(r"^(?P<dob>\d{8})(?P<gender>[MF])(?P<dl>.+)$")

# State + zip (supports ZIP or ZIP+4); works for IL/WI/IN/etc.
STATE_ZIP = re.compile(r"^(?P<state>[A-Z]{2})\s*(?P<zip>\d{5}(?:-\d{4})?)$")

def parse_yymmddcc(date8: str) -> Optional[str]:
    """
    Convert custom 8-digit date format YYMMDDCC to ISO YYYY-MM-DD.
    Example: 26021220 -> 2026-02-12
    """
    if not date8 or len(date8) != 8 or not date8.isdigit():
        return None

    yy = date8[0:2]
    mm = date8[2:4]
    dd = date8[4:6]
    cc = date8[6:8]

    year = int(cc + yy)
    month = int(mm)
    day = int(dd)

    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None

    return f"{year:04d}-{month:02d}-{day:02d}"

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


def parse_left_side(left_tokens: List[str]) -> Tuple[Optional[Dict[str, str]], Optional[Dict[str, str]]]:
    """
    Parse left-side tokens into identity/address fields.

    Expected (conceptually):
        last_name, first_name, address1, [address2], city, state_zip

    Returns:
        (data, error)
    """
    if len(left_tokens) < 5:
        return None, {
            "reason": f"Not enough left-side tokens (got {len(left_tokens)})",
            "left_tokens": " | ".join(left_tokens),
        }

    # Find state+zip token scanning from right
    state_zip_i = None
    for i in range(len(left_tokens) - 1, -1, -1):
        if STATE_ZIP.match(left_tokens[i]):
            state_zip_i = i
            break

    if state_zip_i is None:
        return None, {
            "reason": "Could not find state+zip token on left side",
            "left_tokens": " | ".join(left_tokens),
        }

    if state_zip_i < 2:
        return None, {
            "reason": "State+zip found too early to parse city/name/address",
            "left_tokens": " | ".join(left_tokens),
        }

    city_i = state_zip_i - 1
    city = left_tokens[city_i]
    state_zip = left_tokens[state_zip_i]

    last_name = left_tokens[0]
    first_name = left_tokens[1]

    address_tokens = left_tokens[2:city_i]
    if not address_tokens:
        return None, {
            "reason": "Missing address tokens",
            "left_tokens": " | ".join(left_tokens),
        }

    # Address rules
    if len(address_tokens) == 1:
        address1, address2 = address_tokens[0], ""
    elif len(address_tokens) == 2:
        address1, address2 = address_tokens[0], address_tokens[1]
    else:
        address1 = " ".join(address_tokens[:-1])
        address2 = address_tokens[-1]

    # Optional fallback: if address2 is blank but address1 contains apt/unit markers
    if not address2:
        upper = address1.upper()
        markers = [" APT ", " APARTMENT ", " UNIT ", " STE ", " SUITE ", " #"]
        for marker in markers:
            idx = upper.find(marker)
            if idx != -1:
                address2 = address1[idx:].strip()
                address1 = address1[:idx].strip()
                break

    m = STATE_ZIP.match(state_zip)
    assert m is not None
    state = m.group("state")
    zip_code = m.group("zip")

    return {
        "last_name": last_name,
        "first_name": first_name,
        "address1": address1,
        "address2": address2,
        "city": city,
        "state": state,
        "zip": zip_code,
    }, None

RIGHT_CASE_PREFIX = re.compile(r"^(?P<state>[A-Z]{2})(?P<year>\d{2})(?P<charge>[A-Z]{2})(?P<seq>\d{8})")
ALL_DATES = re.compile(r"\d{8}")

def parse_right_side(right_tokens: List[str]) -> Tuple[Optional[Dict[str, str]], Optional[Dict[str, str]]]:
    """
    Parse right-side tokens into case metadata.
    Returns (data, error).
    """
    if not right_tokens:
        return None, {"reason": "Missing right-side tokens"}

    # Often the last token is the 16-char tail id
    tail_id = right_tokens[-1]
    composite = "".join(right_tokens[:-1]) if len(right_tokens) > 1 else right_tokens[0]

    data: Dict[str, str] = {"tail_id": tail_id}

    m = RIGHT_CASE_PREFIX.match(composite)
    if not m:
        return None, {"reason": "Could not parse case prefix", "composite": composite, "tail_id": tail_id}

    data.update({
        "case_state": m.group("state"),
        "case_year": m.group("year"),
        "charge_code": m.group("charge"),
        "case_seq": m.group("seq"),
        "case_number": m.group(0),  # full prefix, e.g., IL25TR00004567
    })

    rest = composite[len(m.group(0)):]  # everything after the case prefix

    # Status/program code is typically last 12 chars (your spec)
    status_code = ""
    if len(rest) >= 12:
        status_code = rest[-12:]
        rest_before_status = rest[:-12]
    else:
        rest_before_status = rest

    data["status_code"] = status_code

    # Extract all 8-digit date strings from rest_before_status
    dates = ALL_DATES.findall(rest_before_status)

    # first date = sentencing, second date = supervision end
    sentencing_raw = dates[0] if len(dates) >= 1 else ""
    supervision_end_raw = dates[1] if len(dates) >= 2 else ""

    data["sentencing_date_raw"] = sentencing_raw
    data["supervision_end_date_raw"] = supervision_end_raw

    data["sentencing_date"] = parse_yymmddcc(sentencing_raw) if sentencing_raw else None
    data["supervision_end_date"] = parse_yymmddcc(supervision_end_raw) if supervision_end_raw else None

    # Branch code = letters at the start before the first digit (robust)
    first_digit_i = None
    for i, ch in enumerate(rest_before_status):
        if ch.isdigit():
            first_digit_i = i
            break

    if first_digit_i is None:
        branch_code = rest_before_status
    else:
        branch_code = rest_before_status[:first_digit_i]

    data["branch_code"] = branch_code

    return data, None
    
def parse_line(line: str) -> Tuple[Optional[Dict[str, object]], Optional[Dict[str, str]]]:
    """
    Parse one raw line into a structured record.

    Returns:
        (record, error)
    """
    tokens = split_columns(line)

    anchor_i = find_anchor_index(tokens)
    if anchor_i is None:
        return None, {
            "reason": "Missing DOB/Gender/DL anchor token",
            "raw": line.rstrip("\n"),
            "tokens": " | ".join(tokens),
        }

    left_tokens = tokens[:anchor_i]
    anchor_token = tokens[anchor_i]
    right_tokens = tokens[anchor_i + 1:]

    left_data, left_err = parse_left_side(left_tokens)
    if left_err:
        left_err["raw"] = line.rstrip("\n")
        return None, left_err

    m = DOB_GENDER_DL.match(anchor_token)
    if not m:
        return None, {
            "reason": "Anchor token did not match DOB/Gender/DL pattern",
            "raw": line.rstrip("\n"),
            "anchor_token": anchor_token,
        }

    record: Dict[str, object] = dict(left_data)
    record.update({
        "dob_raw": m.group("dob"),
        "gender": m.group("gender"),
        "driver_license": m.group("dl").strip(),
        "right_tokens": right_tokens,
    })

    right_data, right_err = parse_right_side(right_tokens)
    if right_err:
        right_err["raw"] = line.rstrip("\n")
        right_err["right_tokens"] = " | ".join(right_tokens)
        return None, right_err
    record.update(right_data)

    return record, None

def parse_file(file_path: str) -> Tuple[List[Dict[str, object]], List[Dict[str, str]]]:
    """
    Parse a whole daily file.

    Returns:
        (records, errors)
    """
    records: List[Dict[str, object]] = []
    errors: List[Dict[str, str]] = []

    path = Path(file_path)
    for line_number, line in enumerate(path.open("r", encoding="utf-8"), start=1):
        if not line.strip():
            continue

        rec, err = parse_line(line)
        if err:
            err["line_number"] = str(line_number)
            errors.append(err)
        else:
            rec["line_number"] = line_number
            records.append(rec)

    return records, errors

import csv

def export_records_to_csv(records: List[Dict[str, object]], output_path: str) -> None:
    if not records:
        return

    fieldnames = list(records[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def export_errors_to_csv(errors: List[Dict[str, str]], output_path: str) -> None:
    if not errors:
        return

    fieldnames = list(errors[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(errors)





