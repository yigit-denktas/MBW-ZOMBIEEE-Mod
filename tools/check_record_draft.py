#!/usr/bin/env python3
"""Conservative draft count and reference checker; NOT the official toolkit check."""
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
record=json.loads((ROOT/"progress/ledger.json").read_text())
items=record["items"];ms=record["milestones"]
ids=[item["id"] for item in items];mids=[m["id"] for m in ms]
assert len(ids)==len(set(ids)),"duplicate leaf ID"
assert len(mids)==len(set(mids)),"duplicate milestone ID"
assert len(items)==24 and len(ms)==5,"proposed baseline changed; update README and source history"
for item in items:
    assert item["milestoneId"] in mids
    assert all(dep in ids and dep!=item["id"] for dep in item["dependsOn"])
for m in ms:
    assert all(gate in ids for gate in m["gateItemIds"])
    assert all(next(it for it in items if it["id"]==gate)["milestoneId"]==m["id"] for gate in m["gateItemIds"])
gate_ids=[g for m in ms for g in m["gateItemIds"]]
assert len(gate_ids)==len(set(gate_ids))==len(items),"duplicate or orphan gate leaf"
done=sum(it["required"] and it["state"]=="done" for it in items)
required=sum(it["required"] for it in items)
accepted=sum(m["sourceAccepted"] is True for m in ms)
readme=(ROOT/"README.md").read_text()
assert "<!-- project-record:start -->" in readme and "<!-- project-record:end -->" in readme
assert f"{done}/{required}" in readme and f"{accepted}/{len(ms)}" in readme,"README fraction does not match ledger"
issue_links = json.loads((ROOT/"progress/issue-mapping.json").read_text())["crosswalk"]
assert {1,2,3,4,5,6,8,9} == {row["issue"] for row in issue_links}
assert all(set(row["leafIds"]).issubset(set(ids)) for row in issue_links)
assert all(item["owner"].startswith("Agent ") for item in items)
assert all(not (item["required"] and any(next(d for d in items if d["id"] == dep)["required"] is False for dep in item["dependsOn"])) for item in items), "Required release leaf depends on optional work"
assert not any(m["sourceAccepted"] for m in ms),"no owner-approved milestone acceptance yet"
print(json.dumps({"provisional_required":{"done":done,"total":required},
 "accepted_milestones":{"done":accepted,"total":len(ms)},
 "source":"progress/ledger.json","official_toolkit_validation":"still required"},indent=2))
