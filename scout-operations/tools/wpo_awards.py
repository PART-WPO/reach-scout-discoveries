"""Canonical NOAA OAR award parsing and source-grounded WPO funding evidence.

A 459 program segment establishes a WPO funding connection only when
it is explicitly supplied as an award for the exact output by its official
publisher-deposited Crossref funding record. Other OAR segments do not.
This does NOT authorize automatic Smartsheet or REACH insertion.
"""
import re

NOAA_OAR = re.compile(r"^NA\d{2}OARX?(\d{3})C?\d{4,}(?:-[A-Z0-9]+)?$", re.I)
WPO_459 = re.compile(r"^NA\d{2}OARX?459C?\d{4,}(?:-[A-Z0-9]+)?$", re.I)


def oar_segment(award):
    match = NOAA_OAR.fullmatch(str(award or "").strip().upper())
    return match.group(1) if match else None


def is_wpo_459(award):
    return WPO_459.fullmatch(str(award or "").strip().upper()) is not None


def official_459_awards(meta):
    """Publisher-deposited *article-level* structured Crossref awards only.

    Do not infer article funding from a SPARK parent, a child/related output,
    a title/abstract mention, or an unverified award-number research lead.
    """
    if not isinstance(meta, dict) or meta.get("status") != "ok" or (
        str(meta.get("provider") or "").lower() != "crossref"
    ):
        return []
    matched = set()
    for funder in meta.get("funding_references") or []:
        if not isinstance(funder, dict):
            continue
        awards = funder.get("award") or []
        if isinstance(awards, str):
            awards = [awards]
        for award in awards:
            value = str(award or "").strip().upper()
            if is_wpo_459(value):
                matched.add(value)
    return sorted(matched)
