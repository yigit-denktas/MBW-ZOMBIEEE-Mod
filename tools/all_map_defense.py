#!/usr/bin/env python3
"""Optional guard posts for all five original 2012 invasion scenes (never input RAR).

Requires City tactical patch already applied. Replaces only our 27th trigger,
not the original 25. Each map retains its own original spawn entries and navmesh.
"""
from pathlib import Path
import struct
from map_blueprints import blueprint
from scene_tactics import decode_scene, SceneError
from city_defense import scene_index, SCENE_BASE, POS_BASE, LOCAL0, DIVISIONS
from patch_defenders import PatchError, mission_bounds


def add_markers(data, entries, positions):
    scene = decode_scene(data)
    used = {o["entry"] for o in scene["objects"] if o["type"] == 1}
    if len(entries) != 3 or any(i in used for i in entries):
        raise SceneError("Map marker ID collision")
    added = []
    for entry, (x, y, z) in zip(entries, positions):
        added.append(struct.pack("<iii12fi", 1, 0, 0,
            1,0,0,0,1,0,0,0,1, x,y,z,0) + struct.pack("<ii3f",entry,0,1,1,1))
    result = (data[:8] + struct.pack("<i",len(scene["objects"])+3)
              + data[12:scene["object_end"]] + b"".join(added)
              + data[scene["object_end"]:])
    check=decode_scene(result)
    if (check["vertices"]!=scene["vertices"] or check["faces"]!=scene["faces"]
            or len(check["objects"])!=len(scene["objects"])+3):
        raise SceneError("SCO overlay failed round-trip")
    return result


def five_map_orders(scene_ids):
    ops = [["2211", "1", str(LOCAL0)], ["4","0"]]
    for idx, num in enumerate(range(1, 6)):
        if idx:
            ops.append(["5","0"])
        ops.append(["31","2",str(LOCAL0),str(SCENE_BASE+scene_ids[num])])
        entry_ids = (2,3,4) if num == 4 else (41,42,43)
        for group, entry in zip(DIVISIONS, entry_ids):
            pos = POS_BASE + 120
            ops.extend([
                ["1780","2",str(pos),str(entry)],
                ["1791","3","0",str(group),str(pos)],
                ["1790","3","0",str(group),"0"],
            ])
    ops.append(["3","0"])
    return " ".join(["5.000000","0.000000","100000000.000000",
                     "1","417","0",str(len(ops)),
                     *(v for row in ops for v in row)])


def replace_city_orders(mission, scene_ids):
    lines=mission.splitlines(keepends=True)
    count_row, count, end=mission_bounds(lines)
    if count != 27 or lines[count_row].strip() != "27":
        raise PatchError("All-map defence requires the 27-trigger City tactical module")
    old=lines[end-1].split()
    if len(old)<25 or old[:4]!=["5.000000","0.000000","100000000.000000","3"]:
        raise PatchError("Unexpected City-only order trigger; refusing replacement")
    newline="\r\n" if "\r\n" in mission else "\n"
    lines[end-1]=five_map_orders(scene_ids)+newline
    changed="".join(lines)
    if mission_bounds(changed.splitlines(keepends=True))[1] != 27:
        raise PatchError("Mission trigger count changed unexpectedly")
    return changed


def apply_module(module:Path):
    module=Path(module)
    mission_path=module/"mission_templates.txt"
    scene_ids={n:scene_index(module/"scenes.txt",f"scn_tbfc_invasion_{n}")
               for n in range(1,6)}
    changed_mission=replace_city_orders(
        mission_path.read_bytes().decode("utf-8"),scene_ids)
    staged={}
    summary={}
    for num in range(1,6):
        path=module/"SceneObj"/f"scn_tbfc_invasion_{num}.sco"
        data=path.read_bytes()
        if num == 4:
            # City overlay was applied before this command.
            existing={o["entry"] for o in decode_scene(data)["objects"] if o["type"]==1}
            if not {2,3,4}.issubset(existing):
                raise SceneError("City tactical markers not installed")
            summary[str(num)]={"entries":[2,3,4],"already_installed":True}
            continue
        plan=blueprint(data,num)
        staged[path]=add_markers(data,plan["entry_ids"],plan["positions"])
        summary[str(num)]=plan
    originals={p:p.read_bytes() for p in staged}
    originals[mission_path]=mission_path.read_bytes()
    try:
        for path,data in staged.items():
            path.write_bytes(data)
        mission_path.write_bytes(changed_mission.encode("utf-8"))
    except Exception:
        for path,data in originals.items():
            path.write_bytes(data)
        raise
    return {"enabled":True,"maps":summary,"final_trigger_count":27,
            "runtime_verified":False,
            "warning":"No actual WSE2 navigation, line of sight or combat verification"}
