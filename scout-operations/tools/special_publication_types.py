"""Conservative editorial-publication cues for routing, never conclusive rejection.

Only unambiguous *leading* title labels trigger a special publication review.
Scientific terms such as "bias correction", "data correction" or a regular
research article mentioning "erratum" in the abstract are not editorial notices.
The official publication identity still needs source checks and human review.
"""
import re

SPECIAL_LEADING = re.compile(
    r"^\s*(?:"
    r"(?:(?:publisher|author|journal)\s+)?(?:corrigendum|erratum|retraction|retracted)\b"
    r"|expression\s+of\s+concern\b"
    r"|(?:(?:publisher|author)\s+)?correction\s*(?::|[\u2013\u2014]|to\b)"
    r")",
    re.IGNORECASE,
)

def special_publication_type(title):
    """Return editorial cue or empty string; absence does not prove eligibility."""
    if not isinstance(title, str):
        return ""
    m = SPECIAL_LEADING.match(title)
    if not m:
        return ""
    term = m.group(0).strip().lower()
    if "corrigendum" in term:
        return "CORRIGENDUM"
    if "erratum" in term:
        return "ERRATUM"
    if "retract" in term:
        return "RETRACTION"
    if "expression" in term:
        return "EXPRESSION_OF_CONCERN"
    return "CORRECTION_NOTICE"
