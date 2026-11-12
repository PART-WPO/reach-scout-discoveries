#!/usr/bin/env python3
"""Bounded native-source recovery for a publisher-cited related DOI.

Research evidence only. This cannot verify absence from REACH/Scout, select a
SPARK parent, approve Hub intake, or create a public candidate.
"""
import argparse
import base64
import json
import re
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
ZENODO_RE = re.compile(r"^10\.5281/zenodo\.(\d+)$", re.I)
GITHUB_RE = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$", re.I)
HOSTS = {"api.datacite.org", "zenodo.org", "api.github.com", "deepblue.lib.umich.edu"}
MAX_BYTES = 1_000_000
USER_AGENT = "NOAA-WPO-Scout-Related-Source-Recovery/1.0"


def canonical_doi(value):
    value = re.sub(r"^(?:doi:|https?://(?:dx\.)?doi\.org/)", "", str(value or "").strip(), flags=re.I)
    return value.lower().rstrip(".,;)") if DOI_RE.fullmatch(value.rstrip(".,;)")) else ""


def _read(url, accept):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.username or parsed.password or parsed.port:
        raise ValueError("UNAPPROVED_SOURCE_HOST")
    req = Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    with urlopen(req, timeout=12) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != parsed.hostname:
            raise ValueError("UNAPPROVED_SOURCE_REDIRECT")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("SOURCE_RESPONSE_TOO_LARGE")
    return raw


def fetch_json(url):
    return json.loads(_read(url, "application/json").decode("utf-8"))


def fetch_text(url):
    return _read(url, "text/html, text/plain").decode("utf-8", errors="replace")


def github_api(repo_url):
    m = GITHUB_RE.fullmatch(str(repo_url or "").strip())
    if not m:
        return ""
    return "https://api.github.com/repos/" + quote(m.group(1), safe="") + "/" + quote(m.group(2), safe="")


def recover(doi, *, github_repo_url=None, github_source_url=None,
            get_json=fetch_json, get_text=fetch_text):
    """Return exact-identity source evidence with failures, not fabricated metadata.

    github_repo_url must be independently traced to an official article or
    repository record; github_source_url records that traceable citation.
    """
    key = canonical_doi(doi)
    if not key:
        raise ValueError("A canonical exact DOI is required")
    evidence, official, title, native, github_release = [], False, "", False, None
    attr = {}

    def attempt(kind, url, reader):
        try:
            body = reader(url)
            evidence.append({"kind": kind, "url": url, "status": "ACCESSIBLE"})
            return body
        except (OSError, ValueError, TimeoutError, UnicodeError, KeyError, TypeError) as err:
            evidence.append({"kind": kind, "url": url, "status": "SOURCE_ACCESS_FAILURE",
                             "error_type": type(err).__name__, "detail": str(err)[:130]})
            return None

    datacite_url = "https://api.datacite.org/dois/" + quote(key, safe="/")
    data = attempt("official_datacite_exact_doi", datacite_url, get_json)
    if isinstance(data, dict):
        a = (data.get("data") or {}).get("attributes") or {}
        if canonical_doi(a.get("doi")) == key:
            official, attr = True, a
            title = "; ".join(x.get("title", "") for x in a.get("titles", [])[:2] if isinstance(x, dict))
            evidence[-1]["status"] = "EXACT_DOI_VERIFIED"
        else:
            evidence[-1]["status"] = "DOI_IDENTITY_MISMATCH"

    z = ZENODO_RE.fullmatch(key)
    if z:
        zenodo_url = "https://zenodo.org/api/records/" + z.group(1)
        record = attempt("native_zenodo_record", zenodo_url, get_json)
        if isinstance(record, dict):
            doi_found = canonical_doi(record.get("doi") or (record.get("metadata") or {}).get("doi"))
            if doi_found == key:
                native = True
                official = True
                title = title or str((record.get("metadata") or {}).get("title") or "")
                evidence[-1]["status"] = "EXACT_DOI_VERIFIED"
            else:
                evidence[-1]["status"] = "VERSION_OR_DOI_IDENTITY_MISMATCH"
                evidence[-1]["returned_doi"] = doi_found
    else:
        landing = str(attr.get("url") or "").strip()
        parsed = urlsplit(landing)
        # The institutional landing link must come from this exact DOI's
        # DataCite record. Never construct a guessed Deep Blue dataset slug.
        if official and parsed.scheme == "https" and parsed.hostname == "deepblue.lib.umich.edu":
            page = attempt("datacite_cited_deepblue_landing", landing, get_text)
            if isinstance(page, str):
                native = key.lower() in page.lower()
                evidence[-1]["status"] = ("EXACT_DOI_VISIBLE" if native
                                          else "PAGE_ACCESSIBLE_IDENTITY_UNVERIFIED")

    gitapi = github_api(github_repo_url)
    if gitapi and github_source_url and urlsplit(github_source_url).scheme == "https":
        # Caller must supply an independently confirmed official citation.
        readme = attempt("publisher_cited_github_readme", gitapi + "/readme", get_json)
        if isinstance(readme, dict) and readme.get("encoding") == "base64":
            try:
                readme_text = base64.b64decode(readme.get("content") or "").decode("utf-8")
                if key in readme_text.lower():
                    evidence[-1]["status"] = "README_EXACT_DOI_VERIFIED"
                    native = True
                else:
                    evidence[-1]["status"] = "README_DOI_NOT_FOUND"
            except (ValueError, UnicodeError) as err:
                evidence[-1]["status"] = "README_DECODING_ERROR"
        if native:
            releases = attempt("publisher_cited_github_releases", gitapi + "/releases", get_json)
            if isinstance(releases, list) and releases:
                published = [
                    {"tag": x.get("tag_name"), "published_at": x.get("published_at"),
                     "url": x.get("html_url")}
                    for x in releases if x.get("published_at") and not x.get("draft")]
                github_release = min(published, key=lambda x: x["published_at"]) if published else None
                evidence[-1]["status"] = "RELEASE_METADATA_VERIFIED" if published else "NO_PUBLISHED_RELEASE"
    elif github_repo_url:
        evidence.append({"kind": "github_trace", "status": "UNVERIFIED_PUBLISHER_LINK",
                         "reason": "GitHub repository citation source required"})

    funding = []
    for f in attr.get("fundingReferences", []):
        if not isinstance(f, dict):
            continue
        for x in (f.get("awardNumber"), f.get("award")):
            if isinstance(x, str) and x.strip() and x not in funding:
                funding.append(x)
    if official and (native or (not z and not attr.get("url"))):
        status = "OFFICIAL_DOI_VERIFIED"
    elif official or native:
        status = "OUTPUT_METADATA_PARTIAL"
    else:
        status = "SOURCE_ACCESS_FAILURE"
    return {
        "schema": "reach-scout-related-source-recovery-v1",
        "doi": key, "status": status, "official_exact_doi_verified": official,
        "native_exact_doi_or_readme_verified": native, "title": title,
        "resource_type": (attr.get("types") or {}).get("resourceTypeGeneral"),
        "datacite_created_date": str(attr.get("created") or "")[:10] if official else "",
        "output_level_funding_references": funding,
        "github_initial_release": github_release,
        "evidence": evidence, "public_reach_and_scout_identity_gate": "NOT_RUN_BY_THIS_TOOL",
        "project_attribution": "NOT_VERIFIED_FROM_PARENT_ARTICLE",
        "private_hub_import": "NOT_VERIFIED", "new_public_candidate_count": 0,
        "next_action": "COMPLETE_PUBLIC_REACH_SCOUT_AND_IR_IDENTITY_AND_OUTPUT_LEVEL_PROJECT_BRIDGE",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doi", required=True)
    ap.add_argument("--github-repo-url")
    ap.add_argument("--github-source-url")
    args = ap.parse_args()
    print(json.dumps(recover(args.doi, github_repo_url=args.github_repo_url,
                             github_source_url=args.github_source_url), indent=2))


if __name__ == "__main__":
    main()
