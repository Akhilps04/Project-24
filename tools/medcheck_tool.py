# tools/medcheck_tool.py
"""
Simple simulated medication-check tool.
Flags same-time dosing conflicts and a few hard-coded drug interactions.
"""

def medcheck(meds):
    """
    meds: list of dicts with keys 'name' and optional 'time' (HH:MM)
    returns: list of flags
    """
    times = {}
    flags = []
    names = [m["name"] for m in meds]
    for m in meds:
        t = m.get("time", "00:00")
        times.setdefault(t, []).append(m["name"])
    for t, names_at_time in times.items():
        if len(names_at_time) > 1:
            flags.append({"type":"timing_conflict","time":t,"meds":names_at_time})
    # basic interaction rules
    if "Warfarin" in names and "Aspirin" in names:
        flags.append({"type":"interaction","pair":["Warfarin","Aspirin"],"severity":"high","note":"Bleeding risk"})
    if "Metformin" in names and "Contrast" in names:
        flags.append({"type":"interaction","pair":["Metformin","Contrast"],"severity":"moderate","note":"Consider holding Metformin around contrast imaging"})
    return flags
