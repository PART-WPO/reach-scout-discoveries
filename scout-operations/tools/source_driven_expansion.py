#!/usr/bin/env python3
"""Bounded DOI discovery from official publisher source and structured references.

A discovered DOI is a research lead, NEVER an eligible output or a reviewer handoff.
Only publisher-hosted article text and the exact-DOI Crossref reference list count
as source context. Generic reference citations without data/code cues are excluded.
"""
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import quote, urlparse

MAX_BYTES = 2_000_000
USER_AGENT = "NOAA-WPO-Scout-Source-Expansion/1.0 (source-evidence-only)"
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s<>\[\]{}\"']+", re.I)
DATA_CUE = re.compile(
    r"\b(?:data\s+from|dataset|data\s+set|data\s+availability|"
    r"data\s+repository|data\s+archive|supplement(?:ary|al)?\s+data|"
    r"code\s+(?:availability|repository|archive)|source\s+code|"
    r"software\s+(?:repository|archive))\b", re.I)
PUBLISHER_PREFIXES = {
    "10.1002/": "onlinelibrary.wiley.com",
    "10.1029/": "agupubs.onlinelibrary.wiley.com",
}
SOURCE_LIMIT = 2
LEAD_LIMIT = 3


def canonical(value):
    value = re.sub(r"^(?:doi:|https?://(?:dx\.)?doi\.org/)", "", str(value or "").strip(), flags=re.I)
    value = value.rstrip(".,;:)]}>").lower()
    return value if DOI_RE.fullmatch(value) else ""


def source_urls(seed):
    doi = canonical(seed)
    if not doi:
        raise ValueError("Invalid seed DOI")
    result = [("crossref_references", "https://api.crossref.org/works/" + quote(doi, safe="/"))]
    for prefix, host in PUBLISHER_PREFIXES.items():
        if doi.startswith(prefix):
            result.append(("publisher_article_html", "https://" + host + "/doi/" + quote(doi, safe="/")))
            break
    return result[:SOURCE_LIMIT]


def request_source(url):
    """HTTPS-only bounded official fetch; disallow unrelated redirects and payloads."""
    host = urlparse(url).hostname
    if urlparse(url).scheme != "https" or host not in {
        "api.crossref.org", *PUBLISHER_PREFIXES.values()
    }:
        raise ValueError("Unapproved official source hostname")
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json" if host == "api.crossref.org" else "text/html",
    })
    with urllib.request.urlopen(req, timeout=15) as response:
        actual = urlparse(response.geturl())
        if actual.scheme != "https" or actual.hostname != host:
            raise ValueError("Publisher redirected outside trusted source host")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Official source exceeded bounded byte limit")
        return data


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1
        if tag in {"p", "div", "li", "tr", "section", "h2", "h3", "h4", "br"}:
            self.text.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1
        if tag in {"p", "div", "li", "tr", "section", "h2", "h3", "h4"}:
            self.text.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)

    def plain(self):
        return re.sub(r"[ \t]+", " ", html.unescape(" ".join(self.text)))


def candidate_cues(text, seed, evidence_kind, url):
    """A DOI is supported only by a short data/code-specific local source cue."""
    found = []
    for match in DOI_RE.finditer(text):
        doi = canonical(match.group())
        if not doi or doi == seed:
            continue
        before = text[max(0, match.start() - 300):match.start()].split("\n")[-1]
        after = text[match.end():match.end() + 60]
        context = (before + match.group() + after).strip()
        if not DATA_CUE.search(before):
            continue
        # Keep a compact, auditable excerpt, not publisher article content.
        found.append({
            "doi": doi,
            "evidence_kind": evidence_kind,
            "source_url": url,
            "context_excerpt": context[-320:],
            "eligibility": "RESEARCH_LEAD_ONLY",
        })
    return found


def crossref_reference_leads(raw, seed, url):
    result = []
    doc = json.loads(raw)
    message = doc.get("message") or {}
    if canonical(message.get("DOI")) != seed:
        raise ValueError("Crossref source returned the wrong DOI")
    for reference in (message.get("reference") or [])[:500]:
        if not isinstance(reference, dict):
            continue
        cue = " ".join(str(reference.get(k) or "") for k in (
            "article-title", "volume-title", "unstructured", "series-title"
        ))
        if not DATA_CUE.search(cue):
            continue
        candidate = canonical(reference.get("DOI"))
        if candidate and candidate != seed:
            result.append({
                "doi": candidate,
                "evidence_kind": "crossref_structured_data_code_citation",
                "source_url": url,
                "context_excerpt": cue[:320],
                "eligibility": "RESEARCH_LEAD_ONLY",
            })
        result.extend(candidate_cues(cue, seed, "crossref_reference_text", url))
    return result


def discover(seed, fetch=request_source, max_leads=LEAD_LIMIT):
    """Fetch at most two official sources and return at most three leads."""
    seed = canonical(seed)
    if not seed:
        raise ValueError("Invalid seed DOI")
    sources, leads, seen = [], [], set()
    for kind, url in source_urls(seed):
        try:
            raw = fetch(url)
            if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
                raise ValueError("Malformed or oversized source response")
            if kind == "crossref_references":
                matches = crossref_reference_leads(raw, seed, url)
            else:
                parser = VisibleText()
                parser.feed(raw.decode("utf-8", errors="replace"))
                matches = candidate_cues(parser.plain(), seed, kind, url)
            sources.append({
                "kind": kind, "url": url, "status": "SOURCE_READ",
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "data_code_doi_matches": len(matches),
            })
            for lead in matches:
                if lead["doi"] not in seen and len(leads) < max_leads:
                    seen.add(lead["doi"])
                    lead["source_sha256"] = hashlib.sha256(raw).hexdigest()
                    leads.append(lead)
        except (ValueError, json.JSONDecodeError, UnicodeError,
                urllib.error.URLError, TimeoutError, OSError) as exc:
            sources.append({
                "kind": kind, "url": url, "status": "SOURCE_ACCESS_OR_PARSE_HOLD",
                "error_type": type(exc).__name__,
            })
    return {
        "schema": "reach-scout-source-driven-expansion-v1",
        "seed_doi": seed, "source_checks": sources,
        "discovered_doi_leads": leads,
        "status": "SOURCE_BACKED_LEADS_FOUND" if leads else (
            "NO_DATA_CODE_DOI_IDENTIFIED" if any(s["status"] == "SOURCE_READ" for s in sources)
            else "SOURCE_ACCESS_HOLD"),
        "new_public_candidates": 0,
        "private_hub_import": "NOT_VERIFIED",
    }
