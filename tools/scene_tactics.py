#!/usr/bin/env python3
"""Read Warband SCO scenes and create a reversible City guard-post overlay.

Derives candidate posts from connected AI-navmesh faces, not invented coordinates.
Runtime movement, geometry clearance, and line-of-sight remain unverified.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, deque
import json
import math
from pathlib import Path
import struct

MAGIC = -717
ENTRY_TYPE = 1
GUARD_ENTRIES = (2, 3, 4)
ZOMBIE_ENTRIES = range(32, 41)


class SceneError(ValueError):
    pass


def decode_scene(data: bytes) -> dict:
    offset = 0

    def read(fmt):
        nonlocal offset
        n = struct.calcsize("<" + fmt)
        if offset + n > len(data):
            raise SceneError("Truncated SCO")
        values = struct.unpack_from("<" + fmt, data, offset)
        offset += n
        return values[0] if len(values) == 1 else values

    magic = read("i")
    version, count = read("ii") if magic == MAGIC else (0, magic)
    if version not in range(8) or not 0 <= count <= 300000:
        raise SceneError("Unsupported version/object count")
    objects = []
    for _ in range(count):
        meta, subkind, unused = read("iii")
        matrix = read("12f")
        size = read("i")
        if not 0 <= size <= 65536 or offset + size > len(data):
            raise SceneError("Invalid object name")
        name = data[offset:offset + size].decode("utf-8", errors="replace")
        offset += size
        variation = read("i")
        variation2 = read("i") if version >= 2 else 0
        scale = read("3f") if version >= 3 else (1., 1., 1.)
        objects.append({"type": meta, "entry": variation, "name": name,
                        "position": matrix[9:12], "scale": scale})
    object_end = offset
    vertices, edges, faces = [], [], []
    if version >= 4:
        section_size = read("i")
        mesh_start = offset
        if not 0 <= section_size <= len(data) - offset:
            raise SceneError("Invalid mesh length")
        nv = read("i")
        if not 0 <= nv <= 1000000:
            raise SceneError("Invalid vertex count")
        vertices = [read("3f") for _ in range(nv)]
        ne = read("i")
        if not 0 <= ne <= 3000000:
            raise SceneError("Invalid edge count")
        for _ in range(ne):
            read("i")
            a, b = read("ii")
            read("ii")
            if not 0 <= a < nv or not 0 <= b < nv:
                raise SceneError("Invalid navmesh edge")
            edges.append((a, b))
        nf = read("i")
        if not 0 <= nf <= 3000000:
            raise SceneError("Invalid face count")
        for _ in range(nf):
            n = read("i")
            if n not in (3, 4):
                raise SceneError("Unsupported AI face")
            indices = tuple(read("i") for _ in range(n))
            if any(not 0 <= v < nv for v in indices):
                raise SceneError("Invalid face vertex")
            for _ in range(n):
                read("i")
            if read("i") > 0:
                read("i")
            faces.append(indices)
        if offset - mesh_start != section_size:
            raise SceneError("Mesh section length mismatch")
    return {"version": version, "objects": objects, "object_end": object_end,
            "vertices": vertices, "edges": edges, "faces": faces}


def dist(a, b):
    return math.dist(a[:2], b[:2])


def plan_city(data: bytes) -> dict:
    scene = decode_scene(data)
    entries = {}
    for obj in scene["objects"]:
        if obj["type"] != ENTRY_TYPE:
            continue
        key = obj["entry"]
        if key in entries:
            raise SceneError("Duplicate entry: " + str(key))
        entries[key] = obj["position"]
    if 0 not in entries or 1 not in entries:
        raise SceneError("Missing survivor spawn entries")
    if any(e in entries for e in GUARD_ENTRIES):
        raise SceneError("Guard entries already exist")
    enemies = [entries[i] for i in ZOMBIE_ENTRIES if i in entries]
    if len(enemies) < 2 or not scene["faces"] or not scene["edges"]:
        raise SceneError("Insufficient invasion/navmesh data")

    home = entries[0]
    vertices = scene["vertices"]
    links = defaultdict(set)
    for a, b in scene["edges"]:
        links[a].add(b)
        links[b].add(a)
    start = min(range(len(vertices)), key=lambda i: dist(vertices[i], home))
    reachable = {start}
    queue = deque([start])
    while queue:
        for nxt in links[queue.popleft()]:
            if nxt not in reachable:
                reachable.add(nxt)
                queue.append(nxt)

    enemy_center = (sum(p[0] for p in enemies) / len(enemies),
                    sum(p[1] for p in enemies) / len(enemies))
    forward = math.atan2(enemy_center[1] - home[1], enemy_center[0] - home[0])
    bearings = (forward, forward + 2 * math.pi / 3, forward - 2 * math.pi / 3)
    candidates = []
    for face in scene["faces"]:
        if not set(face).issubset(reachable):
            continue
        center = tuple(sum(vertices[i][axis] for i in face) / len(face)
                       for axis in range(3))
        d = dist(center, home)
        if 9 <= d <= 24 and abs(center[2] - home[2]) <= 2.5 and min(
                dist(center, enemy) for enemy in enemies) >= 28:
            candidates.append(center)
    if len(candidates) < 3:
        raise SceneError("Not enough reachable walkable guard-post candidates")
    posts = []
    for bearing in bearings:
        def score(pt):
            angle = math.atan2(pt[1]-home[1], pt[0]-home[0])
            error = abs((angle-bearing+math.pi) % (2*math.pi)-math.pi)
            return (15 * error + abs(dist(pt, home) - 16), pt[0], pt[1])
        candidate = next((v for v in sorted(candidates, key=score)
                          if all(dist(v, prior) > 10 for prior in posts)), None)
        if candidate is None:
            raise SceneError("Cannot space three guard posts")
        posts.append(candidate)

    return {"map": "tbfc_invasion_4",
            "survivor_entry": 0,
            "zombie_entries": sorted(i for i in ZOMBIE_ENTRIES if i in entries),
            "nav_vertices": len(vertices), "nav_faces": len(scene["faces"]),
            "nav_reachable_vertices": len(reachable),
            "guard_posts": [{"entry": e,
                             "position": [round(x, 3) for x in pt],
                             "distance_from_survivors": round(dist(pt, home), 1)}
                            for e, pt in zip(GUARD_ENTRIES, posts)],
            "limitations": "Mesh-connected candidate positions only; game movement/clearance/LOS remain unverified."}


def apply_city_overlay(data: bytes, plan: dict) -> bytes:
    scene = decode_scene(data)
    if scene["version"] < 3:
        raise SceneError("Unsupported SCO version")
    if any(o["type"] == ENTRY_TYPE and o["entry"] in GUARD_ENTRIES
           for o in scene["objects"]):
        raise SceneError("Overlay already installed")
    if [post["entry"] for post in plan["guard_posts"]] != list(GUARD_ENTRIES):
        raise SceneError("Unexpected guard entry IDs")
    appended = []
    for post in plan["guard_posts"]:
        x, y, z = post["position"]
        appended.append(struct.pack("<iii12fi", 1, 0, 0,
                          1,0,0,0,1,0,0,0,1,x,y,z,0)
                        + struct.pack("<ii3f", post["entry"],0,1,1,1))
    return (data[:8] + struct.pack("<i", len(scene["objects"])+3)
            + data[12:scene["object_end"]]
            + b"".join(appended) + data[scene["object_end"]:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--write", type=Path, help="Write new scene COPY; source never overwritten")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    original = args.scene.read_bytes()
    plan = plan_city(original)
    if args.write:
        target = args.write.resolve()
        if target == args.scene.resolve() or target.exists():
            parser.error("Refusing to overwrite an existing/source scene")
        patched = apply_city_overlay(original, plan)
        check = decode_scene(patched)
        if len(check["objects"]) != len(decode_scene(original)["objects"])+3:
            raise SceneError("Roundtrip validation failed")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(patched)
        plan["output_bytes"] = len(patched)
    result = json.dumps(plan, indent=2) + "\n"
    if args.report:
        args.report.write_text(result, encoding="utf-8")
    print(result)


if __name__ == "__main__":
    main()
