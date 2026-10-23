#!/usr/bin/env python3
"""Generate deterministic guard-post blueprints from original SCO navmeshes.

Read-only; scene edits are handled separately. No implied LOS/collision proof.
"""
import math
from collections import defaultdict, deque
from scene_tactics import decode_scene, SceneError


def blueprint(scene_bytes: bytes, map_no: int):
    if map_no not in range(1, 6):
        raise SceneError("Unknown original invasion map")
    scene = decode_scene(scene_bytes)
    entries = {}
    for obj in scene["objects"]:
        if obj["type"] == 1:
            if obj["entry"] in entries:
                raise SceneError("Duplicate original spawn entry")
            entries[obj["entry"]] = obj["position"]
    if 0 not in entries or 1 not in entries:
        raise SceneError("Missing survivor entries")
    zombies = [entries[i] for i in range(32, 41) if i in entries]
    if len(zombies) < 2:
        raise SceneError("Missing invasion spawns")
    markers = (2, 3, 4) if map_no == 4 else (41, 42, 43)
    if any(i in entries for i in markers):
        raise SceneError("Existing entry would be overwritten")
    vertices, faces = scene["vertices"], scene["faces"]
    home = entries[0]
    adj = defaultdict(set)
    for a, b in scene["edges"]:
        adj[a].add(b)
        adj[b].add(a)
    closest = min(range(len(vertices)), key=lambda i: math.dist(vertices[i][:2], home[:2]))
    reachable = {closest}
    queue = deque([closest])
    while queue:
        for neighbor in adj[queue.popleft()]:
            if neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)
    enemy_center = (sum(p[0] for p in zombies)/len(zombies),
                    sum(p[1] for p in zombies)/len(zombies))
    direction = math.atan2(enemy_center[1]-home[1], enemy_center[0]-home[0])
    candidates = []
    for face in faces:
        if not set(face).issubset(reachable):
            continue
        point = tuple(sum(vertices[i][axis] for i in face)/len(face) for axis in range(3))
        distance = math.dist(point[:2], home[:2])
        hostile_distance = min(math.dist(point[:2], p[:2]) for p in zombies)
        if 7 <= distance <= 25 and abs(point[2]-home[2]) <= 3.2 and hostile_distance >= 15:
            candidates.append(point)
    if len(candidates) < 3:
        raise SceneError("Insufficient reachable defence candidates")
    selected = []
    for target in (direction, direction+2*math.pi/3, direction-2*math.pi/3):
        def score(p):
            angle = math.atan2(p[1]-home[1], p[0]-home[0])
            error = abs((angle-target+math.pi) % (2*math.pi)-math.pi)
            return (15*error + abs(math.dist(p[:2], home[:2])-16), round(p[0],6),round(p[1],6))
        candidate = next((p for p in sorted(candidates,key=score)
                         if all(math.dist(p[:2], q[:2]) >= 9 for q in selected)),None)
        if candidate is None:
            raise SceneError("Insufficient post separation")
        selected.append(candidate)
    return {"map_id": f"tbfc_invasion_{map_no}", "entry_ids": list(markers),
            "positions": [[round(n,3) for n in p] for p in selected],
            "mesh_vertices":len(vertices),"candidate_faces":len(candidates),
            "verified_in_engine":False,
            "warning":"Mesh-connected candidates, not verified lines of sight or obstacle clearance"}
