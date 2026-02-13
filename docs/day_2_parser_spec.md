# Day 2 – Parser Spec (Fixed-Layout / Aligned Text)

## Goal
Parse a “daily file” where each line is one record.
The left side (name/address/city) can shift due to spacing, but the right side contains consistent coded fields.

## Key Insight
Do NOT use comma-splitting.
Use:
1) Split columns by 2+ spaces (alignment padding)
2) Find a reliable anchor: DOB+Gender+DriverLicense field
3) Parse left tokens into identity/address fields
4) Parse right tokens into case metadata fields (later)

---

## Column Splitting Rule
Split a line using 2+ spaces.
Single spaces are allowed within addresses and names.

---

## Anchor Rule (Most Reliable)
The “DOB+Gender+DL” token is recognized by:
- 8 digits for DOB (custom order)
- followed immediately by M or F
- followed by driver’s license characters

Regex concept:
`^\d{8}[MF].+$`

This anchor separates:
- LEFT = identity + address fields
- RIGHT = case / court metadata fields

---

## Left Side Field Mapping
Expected items on the left:
- Last name (always)
- First name (always)
- Address1 (always)
- Address2 (optional)
- City (always)
- State + Zip (always, but state can vary: IL/WI/IN/etc.)

### State+Zip detection
Detect token matching:
`AA 12345` or `AA 12345-6789`

Rules:
- state_zip is the token matching the pattern
- city is the token immediately before state_zip
- everything between first_name and city becomes address tokens

### Address mapping
- If 1 address token: Address1 = token, Address2 = blank
- If 2 address tokens: Address1 = first, Address2 = second
- If >2: Address1 = join all but last, Address2 = last

### Address2 fallback
If Address2 is not provided separately but Address1 contains apartment/unit text,
attempt to split Address1 using keywords:
APT, UNIT, STE, SUITE, #.

---

## Error Handling Rules
A line is rejected if:
- anchor token is missing
- state_zip cannot be found
- required left fields are missing

Errors should capture:
- line number
- reason
- raw line
