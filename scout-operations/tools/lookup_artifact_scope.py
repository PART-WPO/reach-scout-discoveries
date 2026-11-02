#!/usr/bin/env python3
"""Read-only artifact file-scope inventory for DOI and tagged GitHub research leads.

Inventory is evidence for follow-up, not proof of funding, successful download,
REACH eligibility, or a new independently catalogable output.
"""
import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import quote

ZENODO = re.compile(r"^10[.]5281/zenodo[.](\d+)$", re.I)
SOURCE_SUFFIXES = (".f90", ".f", ".f95", ".py", ".r", ".jl", ".c", ".cpp", ".h", ".ipynb", ".m", ".sh")

def get(url, github=False):
    headers = {"Accept": "application/vnd.github+json" if github else "application/json",
               "User-Agent": "NOAA-WPO-REACH-Scout-Artifact-Scope/1.0"}
    if github and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=16) as response:
            return json.load(response), None
    except urllib.error.HTTPError as e:
        return None, {"kind": "http", "code": e.code}
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        return None, {"kind": "access", "detail": str(e)[:160]}

def zenodo(doi):
    match = ZENODO.fullmatch(str(doi).lower())
    if not match:
        return {"status": "not_zenodo", "files_verified": False}
    url = "https://zenodo.org/api/records/" + match.group(1)
    record, error = get(url)
    if error:
        return {"status": "source_inaccessible", "source": url,
                "files_verified": False, "error": error}
    raw_files = record.get("files") or []
    if isinstance(raw_files, dict):
        raw_files = list((raw_files.get("entries") or {}).values())
    if not isinstance(raw_files, list):
        raw_files = []
    files = []
    for f in raw_files[:100]:
        if not isinstance(f, dict):
            continue
        files.append({"name": f.get("key") or f.get("filename") or f.get("name"),
                      "size_bytes": f.get("size") or f.get("filesize"),
                      "access_url_present": bool((f.get("links") or {}).get("self") or (f.get("links") or {}).get("content"))})
    record_doi = str((record.get("metadata") or {}).get("doi") or record.get("doi") or "").lower()
    return {"status": "ok", "source": url, "files_verified": True,
            "requested_doi": str(doi).lower(), "record_id": record.get("id"),
            "record_doi": record_doi,
            "resolved_record_is_exact_doi": record_doi == str(doi).lower(),
            "identity_relationship": "exact_version" if record_doi == str(doi).lower() else "concept_or_alias_resolves_version",
            "concept_doi": record.get("conceptdoi") or (record.get("metadata") or {}).get("conceptdoi"),
            "file_count": len(raw_files), "files_sample": files,
            "access": record.get("access") or {}, "file_listing_truncated": len(raw_files) > 100,
            "note": "File names are API-listed; files were not downloaded or independently validated."}

def github_tree(output_url):
    pattern = re.compile(r"^https://github[.]com/([^/]+)/([^/]+)/(?:releases/tag|tree)/([^/?#]+)")
    match = pattern.match(str(output_url))
    if not match:
        return {"status": "no_exact_tag", "files_verified": False}
    owner, repo, tag = match.groups()
    url = ("https://api.github.com/repos/" + quote(owner, safe="") + "/" +
           quote(repo, safe="") + "/git/trees/" + quote(tag, safe="") + "?recursive=1")
    data, error = get(url, github=True)
    if error:
        return {"status": "source_inaccessible", "source": url,
                "files_verified": False, "error": error}
    tree = data.get("tree") or []
    blobs = [x for x in tree if x.get("type") == "blob"]
    code = [x for x in blobs if str(x.get("path") or "").lower().endswith(SOURCE_SUFFIXES)]
    return {"status": "ok", "source": url, "files_verified": True,
            "tag": tag, "file_count": len(blobs), "source_code_file_count": len(code),
            "source_code_paths_sample": [x.get("path") for x in code[:25]],
            "other_paths_sample": [x.get("path") for x in blobs[:25]],
            "tree_truncated": bool(data.get("truncated")),
            "note": "Tag-specific Git tree inventory; source files were not executed or downloaded."}
