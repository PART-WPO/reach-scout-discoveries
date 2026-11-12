#!/usr/bin/env python3
"""Reusable, fail-closed verification of the SHA-pinned REACH comparison snapshot.

The builder verifies every official shard before creating an attestation. This
checker verifies that the attested cache bytes have NOT changed. With --live,
it additionally compares the current authoritative manifest fingerprint.
Neither mode turns a cache miss into proof that an output is new.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path("scout-operations/reach-comparison-cache/comparison-index.json")
ATTESTATION = Path("scout-operations/reach-comparison-cache/cache-verification.json")
MANIFEST_URL = "https://raw.githubusercontent.com/PART-WPO/reach-dashboard/main/agent-data/manifest.json"


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _result(status, reason, *, attestation=None, source_freshness="NOT_CHECKED"):
    return {
        "status": status,
        "reason": reason,
        "source_freshness": source_freshness,
        "source_manifest_git_blob_sha": (attestation or {}).get("source_manifest_git_blob_sha"),
        "cache_git_blob_sha": (attestation or {}).get("cache_git_blob_sha"),
        "verified_shard_count": (attestation or {}).get("verified_shard_count"),
        "source_records": (attestation or {}).get("source_records"),
    }


def verify_snapshot(*, root=ROOT, manifest_bytes=None):
    """Verify an already-verified cache, without re-downloading 150 shards.

    Status VERIFIED_SNAPSHOT is evidence for the cached snapshot only.
    SOURCE_CHANGED is a stale snapshot, not a cryptographic hash collision.
    SHA_MISMATCH identifies an actual byte-level cache/source inconsistency.
    """
    root = Path(root)
    proof_path, cache_path = root / ATTESTATION, root / CACHE
    if not proof_path.is_file():
        return _result("NOT_VERIFIED", "ATTESTATION_MISSING")
    if not cache_path.is_file():
        return _result("NOT_VERIFIED", "CACHE_MISSING")
    try:
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        raw = cache_path.read_bytes()
        cache = json.loads(raw.decode("utf-8"))
    except (ValueError, OSError, UnicodeDecodeError) as exc:
        return _result("NOT_VERIFIED", "UNREADABLE_OR_INVALID_JSON:" + type(exc).__name__)

    if (proof.get("schema") != "reach-scout-comparison-attestation-v1"
            or proof.get("status") != "VERIFIED_SNAPSHOT"
            or proof.get("source_repo") != "PART-WPO/reach-dashboard"
            or cache.get("schema") != "reach-scout-comparison-cache-v1"):
        return _result("NOT_VERIFIED", "INVALID_ATTESTATION_SCHEMA", attestation=proof)

    if (proof.get("cache_sha256") != hashlib.sha256(raw).hexdigest()
            or proof.get("cache_git_blob_sha") != git_blob_sha(raw)):
        return _result("SHA_MISMATCH", "CACHE_CONTENT_HASH_MISMATCH", attestation=proof)

    if (proof.get("source_manifest_sha256") != cache.get("source_manifest_sha256")
            or proof.get("source_csv_sha256_declared") != cache.get("source_csv_sha256_declared")):
        return _result("SHA_MISMATCH", "SOURCE_MANIFEST_FINGERPRINT_MISMATCH", attestation=proof)

    if (not isinstance(proof.get("source_records"), int)
            or proof["source_records"] != cache.get("source_records")
            or proof["source_records"] != len(cache.get("records", []))
            or not isinstance(proof.get("verified_shard_count"), int)
            or proof["verified_shard_count"] != len(cache.get("verified_shards", []))
            or proof["verified_shard_count"] <= 0):
        return _result("NOT_VERIFIED", "INCOMPLETE_ATTESTATION_COUNTS", attestation=proof)

    if manifest_bytes is not None:
        if (proof.get("source_manifest_git_blob_sha") != git_blob_sha(manifest_bytes)
                or proof.get("source_manifest_sha256") != hashlib.sha256(manifest_bytes).hexdigest()):
            return _result("SOURCE_CHANGED", "LIVE_SOURCE_MANIFEST_CHANGED",
                           attestation=proof, source_freshness="STALE")
        return _result("VERIFIED_SNAPSHOT", "CACHE_AND_LIVE_MANIFEST_MATCH",
                       attestation=proof, source_freshness="CURRENT")
    return _result("VERIFIED_SNAPSHOT", "CACHE_ATTESTATION_MATCHES",
                   attestation=proof)


def fetch_manifest():
    req = Request(MANIFEST_URL, headers={"User-Agent": "reach-scout-cache-verifier/1.0"})
    with urlopen(req, timeout=30) as response:
        return response.read(2_000_001)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true",
                        help="Also verify the current official REACH manifest (a single small read)")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.live:
        try:
            manifest_bytes = fetch_manifest()
        except Exception as exc:
            result = _result("NOT_VERIFIED", "SOURCE_MANIFEST_ACCESS_FAILURE:" +
                             type(exc).__name__, source_freshness="NOT_CHECKED")
        else:
            result = verify_snapshot(root=args.root, manifest_bytes=manifest_bytes)
    else:
        result = verify_snapshot(root=args.root)
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "VERIFIED_SNAPSHOT":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
