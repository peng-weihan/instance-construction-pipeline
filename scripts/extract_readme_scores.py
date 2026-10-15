"""Export published README score cells without interpreting them as raw runs."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    lines = (ROOT / "upstream/EdgeBench/README.md").read_text().splitlines()
    models = ["Claude Opus 4.8", "GPT-5.5", "GPT-5.4", "GLM-5.1", "DS-V4-Pro"]
    active = False
    records = []
    for line in lines:
        if line.startswith("| Task | Category |"):
            active = True
            continue
        if not active:
            continue
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0].startswith(":-"):
            continue
        assert len(cells) == 7, cells
        for model, series in zip(models, cells[2:]):
            values = series.split("/")
            assert len(values) == 6, (cells[0], model, series)
            for hours, value in zip([2, 4, 6, 8, 10, 12], values):
                records.append({"task_id": cells[0], "readme_category": cells[1],
                                "model": model, "hours": hours,
                                "published_score": "" if value == "—" else float(value),
                                "source": "upstream/EdgeBench/README.md",
                                "note": "Published rounded aggregate; not raw run-level data."})
    assert len(records) == 51 * 5 * 6, len(records)
    with (ROOT / "research/published_scores.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(f"Exported {len(records)} cells for 51 tasks, 5 models, 6 time budgets; missing cells remain empty.")


if __name__ == "__main__":
    main()
