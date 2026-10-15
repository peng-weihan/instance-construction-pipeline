"""Cross-check research tables, blueprints and local delivery links; no network."""
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read_csv(name):
    with (ROOT / "research" / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    inventory = read_csv("full_task_inventory.csv")
    taxonomy = read_csv("task_taxonomy.csv")
    scores = read_csv("published_scores.csv")
    ids = {row["task_id"] for row in taxonomy}
    assert len(inventory) == len({r["task_id"] for r in inventory}) == 134
    assert len(taxonomy) == len(ids) == 51
    assert ids == {r["task_id"] for r in inventory if r["public_task_definition"] == "True"}
    assert all(len(row) == 21 and None not in row for row in taxonomy)
    assert len(scores) == len({(r["task_id"], r["model"], r["hours"]) for r in scores}) == 1530
    assert {r["task_id"] for r in scores} == ids
    stats = json.loads((ROOT / "research/task_taxonomy_stats.json").read_text())
    assert Counter(r["mechanism_primary_research"] for r in taxonomy) == stats["research_mechanisms"]
    assert Counter(r["official_category"] for r in taxonomy) == stats["official_categories"]
    official = {r["task_id"]: r["official_category"] for r in inventory}
    assert all(official[r["task_id"]] == r["official_category"] for r in taxonomy)

    blueprint = json.loads((ROOT / "research/instance_blueprints.json").read_text())
    assert blueprint["status"] == "design_proposal_not_implemented_or_calibrated"
    assert len(blueprint["families"]) == len({r["family_id"] for r in blueprint["families"]}) == 3
    for family in blueprint["families"]:
        references = family.get("inspiration_task_ids", [])
        if "inspiration_task_id" in family:
            references = references + [family["inspiration_task_id"]]
        assert set(references) <= set(official), references
        for reference in set(references) - ids:
            assert family.get("inspiration_source_scope", {}).get(reference) == "paper_only_not_in_public_51"

    output = ROOT / "research/artifact_validation.json"
    checked_links = 0
    for document in [ROOT / "README.md", ROOT / "ANALYSIS_REPORT.md",
                     ROOT / "research/drafts/07-cross-validation.md"]:
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            if "://" in target or target.startswith("#"):
                continue
            path = (document.parent / target.split("#", 1)[0]).resolve()
            assert path.exists() or path == output, (document, target)
            checked_links += 1
    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed", "inventory_tasks": len(inventory),
        "public_tasks_classified": len(taxonomy), "taxonomy_fields": 21,
        "published_score_cells": len(scores), "proposal_families": 3,
        "local_delivery_links_checked": checked_links,
        "source_integrity": "See source_manifest.json and reference_copy_manifest.json.",
        "scope": "Research artifacts only; no generated-instance or benchmark-runtime validation."
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
