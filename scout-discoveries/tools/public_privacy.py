"""Fail-closed privacy gate for PUBLIC REACH Scout output metadata.

Run before publishing new Scout batches. This is a targeted technical screen,
not an authorization to disclose private data or a replacement for review.
Never echo matched values into CI error output.
"""
import re

# Legitimate PI and author names are public scholarly attribution. Their
# emails, private reviewer activity, internal row IDs, and credentials are not.
EMAIL = re.compile(r"(?i)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PRIVATE_LABEL = re.compile(
    r"(?i)\b(?:"
    r"(?:reviewer\s+(?:e-?mail|name|identity|notes?|decision|user(?:name)?|id)|review\s+notes?)"
    r"|reviewed\s+(?:at|by)"
    r"|(?:decision|finding)\s+fingerprint"
    r"|(?:created|smartsheet|smartsheetgov|private|source)\s+(?:sheet|row)\s+id"
    r"|private\s+(?:review|decision)\s+(?:note|record|history|log)"
    r"|(?:api|access|refresh|authorization)\s+(?:key|token|secret)"
    r")\s*[:=]"
)
SECRET = re.compile(
    r"(?i)(?:"
    r"\bgithub_pat_[A-Za-z0-9_]{20,}"
    r"|\bgh[pousr]_[A-Za-z0-9]{20,}"
    r"|\bxox[baprs]-[A-Za-z0-9-]{15,}"
    r"|\bAIza[0-9A-Za-z_-]{25,}"
    r"|\bsk-(?:proj-)?[0-9A-Za-z_-]{20,}"
    r"|\bBearer\s+[0-9A-Za-z._~-]{12,}"
    r"|[?&](?:api_?key|access_?token|refresh_?token|auth|token|client_secret|signature|sig)="
    r")"
)
PRIVATE_TRACKER_LINK = re.compile(
    r"(?i)https?://[^\s/]*(?:smartsheet\.com|smartsheetgov\.com)(?:/|\b)"
)
# Strictly disallow even empty private-only columns in other future public
# export schemas, while the existing Scout 24-column template remains valid.
PRIVATE_COLUMNS = {
    "reviewer email", "reviewer decision", "review notes", "reviewer notes",
    "reviewed at", "created row id", "created sheet id",
    "smartsheet row id", "smartsheet sheet id",
    "decision fingerprint", "finding fingerprint",
    "reviewer name", "reviewer identity", "authorization token",
}

def check_public_metadata(row, source="public-metadata", line=0):
    if not isinstance(row, dict):
        raise ValueError("Public privacy check requires a field-value mapping")
    for field, value in row.items():
        # Existing 24-column Scout schema intentionally has an empty PI email
        # field; its presence is already validated in build_manifest.
        if field.strip().casefold() in PRIVATE_COLUMNS:
            raise ValueError(f"Public privacy check blocked internal field in {source}:{line}")
        text = str(value or "")
        for label, pattern in (
            ("email address", EMAIL),
            ("internal reviewer/row metadata", PRIVATE_LABEL),
            ("credential or signed link", SECRET),
            ("private tracker URL", PRIVATE_TRACKER_LINK),
        ):
            if pattern.search(text):
                raise ValueError(
                    f"Public privacy check blocked {label} in "
                    f"{source}:{line} / {field}"
                )
    return True
