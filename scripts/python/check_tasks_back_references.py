import json
from pathlib import Path
import re


ADR_FOR_CH = {
    "ADR-0002": ["CH02"],
    "ADR-0019": ["CH02"],
    "ADR-0003": ["CH03"],
    "ADR-0004": ["CH04"],
    "ADR-0006": ["CH05"],
    "ADR-0007": ["CH05", "CH06"],
    "ADR-0005": ["CH07"],
    "ADR-0011": ["CH07", "CH10"],
    "ADR-0008": ["CH10"],
    "ADR-0015": ["CH09"],
    "ADR-0018": ["CH01", "CH06", "CH07"],
    "ADR-0024": ["CH06", "CH07"],
    "ADR-0023": ["CH05"],
}


def load_tasks_back(root: Path) -> list[dict]:
    path = root / ".taskmaster" / "tasks" / "tasks_back.json"
    return json.loads(path.read_text(encoding="utf-8"))


def collect_adr_ids(root: Path) -> set[str]:
    adr_dir = root / "docs" / "adr"
    ids: set[str] = set()
    if not adr_dir.exists():
        return ids
    for f in adr_dir.glob("ADR-*.md"):
        m = re.match(r"ADR-(\d{4})", f.stem)
        if m:
            ids.add(f"ADR-{m.group(1)}")
    return ids


def collect_overlay_paths(root: Path) -> set[str]:
    # Prefer inferring the overlay folder from existing task overlay_refs.
    overlays_root = root / "docs" / "architecture" / "overlays"

    overlay_prd_dir = None
    try:
        tasks_all = load_tasks_back(root)
    except Exception:
        tasks_all = []

    pat = re.compile(r"^docs/architecture/overlays/([^/]+)/08/", re.IGNORECASE)
    for t in tasks_all:
        refs = t.get("overlay_refs") or []
        if not isinstance(refs, list):
            refs = [refs]
        for ref in refs:
            m = pat.match(str(ref).replace("\\", "/"))
            if m:
                overlay_prd_dir = m.group(1)
                break
        if overlay_prd_dir:
            break

    if not overlay_prd_dir and overlays_root.exists():
        prd_dirs = [p.name for p in overlays_root.iterdir() if p.is_dir()]
        if len(prd_dirs) == 1:
            overlay_prd_dir = prd_dirs[0]

    if not overlay_prd_dir:
        return set()

    overlay_root = overlays_root / overlay_prd_dir / "08"
    if not overlay_root.exists():
        return set()

    paths: set[str] = set()
    for p in overlay_root.glob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(root)
        paths.add(str(rel).replace("\\", "/"))
    return paths


def run_check(root: Path) -> bool:
    """Validate new NG tasks in tasks_back.json against ADR/Overlay maps.

    Returns True if everything is consistent, False if any problem is found.
    """

    tasks = load_tasks_back(root)
    adr_ids = collect_adr_ids(root)
    overlay_paths = collect_overlay_paths(root)

    new_ids = {f"NG-00{i}" for i in range(23, 34)}
    new_tasks = [t for t in tasks if t.get("id") in new_ids]

    print(f"new_tasks_count: {len(new_tasks)}")
    print(f"known ADR ids (sample): {sorted(adr_ids)[:10]} ...")
    print(f"overlay files: {sorted(overlay_paths)}")

    has_error = False

    for t in sorted(new_tasks, key=lambda x: x["id"]):
        tid = t["id"]
        story_id = t.get("story_id")
        print(f"\n== {tid} ==")
        print(f"story_id: {story_id}")

        # ADR refs
        missing_adrs = [a for a in t.get("adr_refs", []) if a not in adr_ids]
        if missing_adrs:
            print(f"  missing ADRs: {missing_adrs}")
            has_error = True
        else:
            print("  adr_refs OK")

        # chapter_refs vs ADR_FOR_CH
        expected_ch: set[str] = set()
        for adr in t.get("adr_refs", []):
            expected_ch.update(ADR_FOR_CH.get(adr, []))
        current_ch = set(t.get("chapter_refs", []))
        missing_ch = expected_ch - current_ch
        extra_ch = current_ch - expected_ch
        if missing_ch:
            print(f"  missing chapter_refs (from ADR): {sorted(missing_ch)}")
            has_error = True
        if extra_ch:
            print(f"  extra chapter_refs (not implied by ADR map): {sorted(extra_ch)}")
            has_error = True
        if not missing_ch and not extra_ch:
            print("  chapter_refs consistent with ADR map")

        # overlay refs
        refs = [p.replace("\\", "/") for p in t.get("overlay_refs", [])]
        if not refs:
            print("  overlay_refs: (missing)")
            has_error = True
        else:
            missing_overlays = [p for p in refs if p not in overlay_paths]
            if missing_overlays:
                print(f"  missing overlays: {missing_overlays}")
                has_error = True
            else:
                print("  overlay_refs OK")

    return not has_error


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    ok = run_check(root)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
