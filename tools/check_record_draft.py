#!/usr/bin/env python3
"""Conservative draft count and reference checker; NOT the official toolkit check."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
record=json.loads((ROOT/"progress/ledger.json").read_text(encoding="utf-8"))
items=record["items"];ms=record["milestones"]
ids=[item["id"] for item in items];mids=[m["id"] for m in ms]
assert len(ids)==len(set(ids)),"duplicate leaf ID"
assert len(mids)==len(set(mids)),"duplicate milestone ID"
required=[item for item in items if item["required"]]
optional=[item for item in items if not item["required"] and item.get("workOrigin")!="discovered"]
discovered=[item for item in items if item.get("workOrigin")=="discovered"]
assert len(items)==len(required)+len(optional)+len(discovered),"item origin classification is not exhaustive"
assert len(required)==23 and len(optional)==1 and len(discovered)>=18,"proposed baseline changed; update README and source history"
assert len(ms)==5,"expected five proposed milestones"
for item in items:
    assert item["milestoneId"] in mids
    assert all(dep in ids and dep!=item["id"] for dep in item["dependsOn"])
for m in ms:
    assert all(gate in ids for gate in m["gateItemIds"])
    assert all(next(it for it in items if it["id"]==gate)["milestoneId"]==m["id"] for gate in m["gateItemIds"])
gate_ids=[g for m in ms for g in m["gateItemIds"]]
assert len(gate_ids)==len(set(gate_ids))==len(required),"duplicate, orphan or missing gate leaf"
assert set(gate_ids)=={item["id"] for item in required},"required leaves and gate leaves differ"
done=sum(item["state"]=="done" for item in required)
accepted=sum(m["sourceAccepted"] is True for m in ms)
readme=(ROOT/"README.md").read_text(encoding="utf-8")
assert "<!-- project-record:start -->" in readme and "<!-- project-record:end -->" in readme
assert f"{done}/{len(required)}" in readme and f"{accepted}/{len(ms)}" in readme,"README fraction does not match ledger"
issue_links = json.loads((ROOT/"progress/issue-mapping.json").read_text(encoding="utf-8"))["crosswalk"]
assert {1,2,3,4,5,6,8,9,13,14,15,16} == {row["issue"] for row in issue_links}
assert all(set(row["leafIds"]).issubset(set(ids)) for row in issue_links)
assert all(item["owner"].startswith("Agent ") for item in items)
assert all(not (item["required"] and any(next(d for d in items if d["id"] == dep)["required"] is False for dep in item["dependsOn"])) for item in items), "Required release leaf depends on optional work"
assert not any(m["sourceAccepted"] for m in ms),"no owner-approved milestone acceptance yet"
discovered_done=sum(item["state"]=="done" for item in discovered)
print(json.dumps({"provisional_required":{"done":done,"total":len(required)},
 "provisional_discovered":{"done":discovered_done,"total":len(discovered)},
 "accepted_milestones":{"done":accepted,"total":len(ms)},
 "issues_mapped":len(issue_links),
 "source":"progress/ledger.json","official_toolkit_validation":"still required"},indent=2))
