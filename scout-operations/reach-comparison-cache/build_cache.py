#!/usr/bin/env python3
"""Build a checksum-verified, compact public REACH comparison cache."""
import csv, hashlib, io, json, pathlib, re, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
BASE="https://raw.githubusercontent.com/PART-WPO/reach-dashboard/main/"
def get(path):
    with urllib.request.urlopen(BASE+path, timeout=45) as response:
        return response.read()
def sha(data): return hashlib.sha256(data).hexdigest()
def git_blob_sha(data):
    """GitHub's content-addressed blob id; enables verification via GitHub file metadata."""
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
def norm(s): return re.sub(r"[^a-z0-9]+"," ",str(s or "").casefold()).strip()
def dois(s):
    return sorted(set(m.lower().rstrip(".,;)") for m in re.findall(r"10\.\d{4,9}/[^\s,;<>\"']+",str(s or ""),re.I)))
def main():
    manifest_bytes=get("agent-data/manifest.json")
    manifest=json.loads(manifest_bytes)
    records={}
    checked=[]
    for section in ("index","details"):
        for shard in manifest[section]["files"]:
            path=shard["path"]; data=get(path)
            if sha(data)!=shard["sha256"] or len(data)!=shard["bytes"]:
                raise ValueError("checksum or size mismatch: "+path)
            rows=list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
            if len(rows)!=shard["rows"]: raise ValueError("row count mismatch: "+path)
            checked.append({"path":path,"sha256":sha(data),"rows":len(rows)})
            for row in rows:
                uid=row.get("REACH UID","").strip()
                rid=row.get("Record ID","").strip()
                key=uid or rid
                if not key: raise ValueError("missing REACH identity in "+path)
                item=records.setdefault(key,{"reach_uid":uid,"record_id":rid,"title":"","title_normalized":"","awards":"","links":[],"dois":[],"index_path":None,"detail_path":None})
                if section=="index":
                    item["index_path"]=path
                    item["title"]=row.get("Title","")
                    item["title_normalized"]=norm(item["title"])
                    item["awards"]=row.get("Award Number(s)","")
                else: item["detail_path"]=path
                linkcols=("Link to Output","Journal Article Link","Publications","Data & Instruments","Code","Other Knowledge Products")
                for col in linkcols:
                    value=row.get(col,"")
                    if value and value not in item["links"]: item["links"].append(value)
                    item["dois"]=sorted(set(item["dois"])|set(dois(value)))
    if len(records)!=manifest["source"]["rows"]:
        raise ValueError("record count mismatch: expected %s got %s"%(manifest["source"]["rows"],len(records)))
    if any(not r["index_path"] or not r["detail_path"] for r in records.values()):
        raise ValueError("index/detail join incomplete")
    output={"schema":"reach-scout-comparison-cache-v1","source_repo":"PART-WPO/reach-dashboard","source_manifest_sha256":sha(manifest_bytes),"source_csv_sha256_declared":manifest["source"]["sha256"],"source_records":len(records),"verified_shards":checked,"records":sorted(records.values(),key=lambda x:x["record_id"])}
    HERE.mkdir(parents=True,exist_ok=True)
    cache_bytes = (json.dumps(output,ensure_ascii=False,separators=(",",":"))+"\\n").encode("utf-8")
    (HERE/"comparison-index.json").write_bytes(cache_bytes)
    # Produced only AFTER every shard's SHA-256, byte size, row count and
    # record identity have passed. This is a deterministic, reusable snapshot
    # attestation, not a claim about a future REACH manifest.
    attestation = {
        "schema": "reach-scout-comparison-attestation-v1",
        "status": "VERIFIED_SNAPSHOT",
        "source_repo": "PART-WPO/reach-dashboard",
        "source_manifest_sha256": sha(manifest_bytes),
        "source_manifest_git_blob_sha": git_blob_sha(manifest_bytes),
        "source_csv_sha256_declared": manifest["source"]["sha256"],
        "cache_sha256": sha(cache_bytes),
        "cache_git_blob_sha": git_blob_sha(cache_bytes),
        "source_records": len(records),
        "verified_shard_count": len(checked),
    }
    (HERE/"cache-verification.json").write_text(
        json.dumps(attestation,sort_keys=True,indent=2)+"\\n", encoding="utf-8")
    print(json.dumps({"records":len(records),"verified_shards":len(checked),
                      "cache_sha256":sha(cache_bytes),"attestation":"VERIFIED_SNAPSHOT"}))
if __name__=="__main__":main()
