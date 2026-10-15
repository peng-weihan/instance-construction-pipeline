"""Extract task IDs and categories from EdgeBench paper Table 7, stdlib only."""
from collections import Counter
import csv
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.cell = None
        self.row = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table" and attrs.get("id", "").startswith("A7.T7"):
            self.active = True
        if self.active and tag == "tr":
            self.row = []
        if self.active and tag in ("td", "th"):
            self.cell = []

    def handle_data(self, data):
        if self.active and self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if self.active and tag in ("td", "th") and self.cell is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.cell = None
        if self.active and tag == "tr" and self.row:
            self.rows.append(self.row)
        if self.active and tag == "table":
            self.active = False


def main():
    parser = TableParser()
    parser.feed((ROOT / "research/sources/edgebench-paper.html").read_text())
    public = {json.loads(line)["task_id"] for line in
              (ROOT / "data/EdgeBench/tasks.jsonl").read_text().splitlines() if line}
    category = None
    records = []
    for row in parser.rows:
        if len(row) == 1:
            category = row[0]
        elif len(row) == 2 and row[0] != "Task":
            task_id = re.sub(r"\s+", "", row[0])
            assert re.fullmatch(r"[a-z0-9_]+", task_id), task_id
            records.append({"task_id": task_id, "official_category": category,
                            "public_task_definition": task_id in public,
                            "source": "https://arxiv.org/html/2607.05155v1#A7.T7"})
    assert len(records) == len({r["task_id"] for r in records}) == 134, len(records)
    assert sum(r["public_task_definition"] for r in records) == 51
    out = ROOT / "research/full_task_inventory.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    counts = Counter(r["official_category"] for r in records)
    public_counts = Counter(r["official_category"] for r in records if r["public_task_definition"])
    summary = {k: {"full": v, "public": public_counts[k],
                   "public_fraction": round(public_counts[k] / v, 4)} for k, v in counts.items()}
    (ROOT / "research/category_counts.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
