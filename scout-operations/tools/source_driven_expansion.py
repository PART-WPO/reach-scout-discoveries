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
import subprocess
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import quote, urlparse, urljoin

MAX_BYTES = 2_000_000
MAX_PDF_BYTES = 8_000_000
IR_HOST = "repository.library.noaa.gov"
IR_ITEM_RE = re.compile(r"^https://repository\.library\.noaa\.gov/view/noaa/\d+$")
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
        "api.crossref.org", IR_HOST, *PUBLISHER_PREFIXES.values()
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
        cap = MAX_PDF_BYTES if host == IR_HOST and actual.path.lower().endswith(".pdf") else MAX_BYTES
        data = response.read(cap + 1)
        if len(data) > cap:
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


class PdfLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and isinstance(value, str):
                    self.hrefs.append(value)


def pdf_text_from_bytes(data):
    """Use the runner's sandboxed Poppler extractor; never execute PDF content."""
    if not isinstance(data, bytes) or not data.startswith(b"%PDF-") or len(data) > MAX_PDF_BYTES:
        raise ValueError("Invalid or oversized public manuscript PDF")
    proc = subprocess.run(
        ["pdftotext", "-layout", "-", "-"], input=data, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=20, check=True,
    )
    text = proc.stdout.decode("utf-8", errors="replace")[:250_000]
    # Join within-paragraph PDF line wraps, keep blank-line boundaries to
    # prevent data cues from leaking across unrelated citations.
    return re.sub(r"(?<!\n)\n(?!\n)", " ", text)


def noaa_ir_pdf_leads(seed, ir_url, fetch=request_source, pdf_to_text=None):
    """Use only a SHA-indexed exact-DOI NOAA IR item and that item's own PDF link."""
    if not IR_ITEM_RE.fullmatch(str(ir_url or "")):
        raise ValueError("NOAA IR item is not an exact trusted public URL")
    sources, leads = [], []
    try:
        item_raw = fetch(ir_url)
        if not isinstance(item_raw, bytes) or len(item_raw) > MAX_BYTES:
            raise ValueError("Oversized NOAA IR public item page")
        links = PdfLinks()
        links.feed(item_raw.decode("utf-8", errors="replace"))
        sources.append({"kind": "noaa_ir_landing", "url": ir_url, "status": "SOURCE_READ",
                        "source_sha256": hashlib.sha256(item_raw).hexdigest()})
        allowed = sorted({
            urljoin(ir_url + "/", href) for href in links.hrefs
            if isinstance(href, str)
        })
        pdf_links = [u for u in allowed if (
            urlparse(u).scheme == "https" and urlparse(u).hostname == IR_HOST
            and u.startswith(ir_url + "/") and
            re.fullmatch(r"noaa_\d+_DS\d+\.pdf", urlparse(u).path.rsplit("/", 1)[-1], re.I)
        )]
        if not pdf_links:
            sources.append({"kind": "noaa_ir_manuscript_pdf", "url": ir_url,
                            "status": "NO_VALIDATED_MANUSCRIPT_PDF_LINK"})
            return sources, leads
        pdf_url = pdf_links[0]
        pdf_raw = fetch(pdf_url)
        if not isinstance(pdf_raw, bytes) or len(pdf_raw) > MAX_PDF_BYTES:
            raise ValueError("Oversized manuscript PDF")
        text = (pdf_to_text or pdf_text_from_bytes)(pdf_raw)
        if not isinstance(text, str):
            raise ValueError("Public manuscript text extractor returned invalid text")
        leads = candidate_cues(text, seed, "noaa_ir_accepted_manuscript_pdf", pdf_url)
        sources.append({"kind": "noaa_ir_manuscript_pdf", "url": pdf_url,
                        "status": "SOURCE_READ", "source_sha256": hashlib.sha256(pdf_raw).hexdigest(),
                        "data_code_doi_matches": len(leads)})
        for lead in leads:
            lead["source_sha256"] = hashlib.sha256(pdf_raw).hexdigest()
    except (ValueError, OSError, TimeoutError, subprocess.SubprocessError,
            urllib.error.URLError) as exc:
        sources.append({"kind": "noaa_ir_accepted_manuscript", "url": ir_url,
                        "status": "SOURCE_ACCESS_OR_PARSE_HOLD", "error_type": type(exc).__name__})
    return sources, leads


def discover(seed, fetch=request_source, max_leads=LEAD_LIMIT, *, ir_url=None, pdf_to_text=None):
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
    # Wiley and other publisher sites can reject unattended clients. When
    # SHA-verified NOAA IR metadata proves the exact seed item, try its own
    # publicly linked accepted manuscript; never infer PDF URLs or follow
    # arbitrary article links.
    if ir_url and not leads:
        extra_sources, extra_leads = noaa_ir_pdf_leads(
            seed, ir_url, fetch=fetch, pdf_to_text=pdf_to_text)
        sources.extend(extra_sources)
        for lead in extra_leads:
            if lead["doi"] not in seen and len(leads) < max_leads:
                seen.add(lead["doi"])
                leads.append(lead)
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
