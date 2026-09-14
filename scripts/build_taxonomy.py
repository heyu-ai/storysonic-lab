"""從 RSS 抓取指定節目的所有單集，依關鍵字歸類成主題類別，輸出 CSV 與 Markdown 報告。

用法：
    python3 scripts/build_taxonomy.py [--shows <id1,id2,...>] [--config podcasts.toml] [--output-dir <dir>]

不指定 --shows 時，預設處理 podcasts.toml 內全部節目。
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from storysonic.catalog import fetch_episodes, load_config

# 關鍵字 → 類別。依順序比對，第一個命中的類別生效；全不符歸入「其他」。
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("時事知識類", ["新聞", "知識", "科學", "科普", "STEAM", "數學", "歷史", "地理", "動物", "自然", "宇宙", "環保", "發明", "健康"]),
    ("推理故事類", ["推理", "偵探", "探長", "謀殺", "案件", "謎"]),
    ("語言學習類", ["英文", "英語", "台語", "閩南語", "日文", "語言"]),
    ("寓言童話類", ["寓言", "童話", "伊索", "格林", "安徒生", "民間故事", "神話", "傳說"]),
    ("生活故事類", ["生活", "親子", "情緒", "友情", "勇氣", "成長", "家人", "睡前"]),
    ("繪本故事類", ["繪本"]),
    ("原創故事類", ["原創", "冒險", "魔法", "奇幻", "龍", "精靈", "王國", "旅程", "英雄"]),
]
DEFAULT_CATEGORY = "故事類"


def classify_title(title: str) -> str:
    for category, keywords in CATEGORY_RULES:
        if any(kw in title for kw in keywords):
            return category
    return DEFAULT_CATEGORY


def clean_topic(title: str) -> str:
    """去除集數前綴（EP.nnn、第n集等）與上下集標記，保留故事本名。"""
    t = re.sub(r"^(?:EP|SP|ep|第)[\.\s]?\d+[\s\-\|—－]+", "", title)
    t = re.sub(r"[（(][上中下]\s*集[）)]", "", t)
    t = re.sub(r"\s*[（(]上[）)]|\s*[（(]下[）)]", "", t)
    t = t.strip("｜|—－ \t")
    return t.strip() or title.strip()


def build_taxonomy(shows_cfg, show_ids: list[str]) -> dict:
    """
    回傳結構：
    {
        show_id: {
            "name": str,
            "categories": {
                category: [topic_name, ...]
            }
        }
    }
    """
    result = {}
    for sid in show_ids:
        show = shows_cfg[sid]
        print(f"  抓取 {show.name} …", flush=True)
        try:
            episodes = fetch_episodes(show)
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"  ⚠ 無法抓取 {show.name}：{exc}", file=sys.stderr)
            result[sid] = {"name": show.name, "categories": {}, "error": str(exc)}
            continue

        categories: dict[str, set[str]] = defaultdict(set)
        for ep in episodes:
            topic = clean_topic(ep["title"])
            category = classify_title(ep["title"])
            categories[category].add(topic)

        result[sid] = {
            "name": show.name,
            "categories": {cat: sorted(topics) for cat, topics in sorted(categories.items())},
        }
        total = sum(len(t) for t in categories.values())
        print(f"    → {len(episodes)} 集，{len(categories)} 個類別，{total} 個主題", flush=True)

    return result


def write_csv(taxonomy: dict, output_path: Path) -> None:
    rows = []
    for sid, data in taxonomy.items():
        for category, topics in data["categories"].items():
            for topic in topics:
                rows.append({
                    "show_id": sid,
                    "show_name": data["name"],
                    "category": category,
                    "topic_name": topic,
                })
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["show_id", "show_name", "category", "topic_name"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  CSV → {output_path}（{len(rows)} 筆）")


def write_markdown(taxonomy: dict, output_path: Path, query_date: str) -> None:
    lines = [
        "# Podcast 節目主題分類研究",
        "",
        f"查核日期：{query_date}",
        "",
        "每個節目的單集標題依關鍵字歸入類別；主題名稱已去除集數前綴與上下集標記。",
        "",
    ]
    for data in taxonomy.values():
        lines.append(f"## {data['name']}")
        lines.append("")
        if "error" in data:
            lines.append(f"> ⚠ 無法取得：{data['error']}")
            lines.append("")
            continue
        total_topics = sum(len(t) for t in data["categories"].values())
        lines.append(f"共 {len(data['categories'])} 個類別、{total_topics} 個主題。")
        lines.append("")
        for category, topics in data["categories"].items():
            lines.append(f"### {category}（{len(topics)} 個主題）")
            lines.append("")
            for topic in topics:
                lines.append(f"- {topic}")
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Markdown → {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="建立 Podcast 主題分類研究報告")
    parser.add_argument("--config", type=Path, default=Path("podcasts.toml"))
    parser.add_argument("--shows", help="逗號分隔的 show ID，預設全部")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    _, shows_cfg = load_config(args.config)

    if args.shows:
        requested = [s.strip() for s in args.shows.split(",")]
        unknown = [s for s in requested if s not in shows_cfg]
        if unknown:
            print(f"未知 show ID：{unknown}；可用：{list(shows_cfg)}", file=sys.stderr)
            return 1
        show_ids = requested
    else:
        show_ids = list(shows_cfg)

    today = datetime.now(tz=UTC).date().isoformat()
    output_dir = args.output_dir or Path(f"docs/research/{today}-podcast-taxonomy")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"處理 {len(show_ids)} 個節目，輸出到 {output_dir}")
    taxonomy = build_taxonomy(shows_cfg, show_ids)

    write_csv(taxonomy, output_dir / "taxonomy.csv")
    write_markdown(taxonomy, output_dir / "README.md", today)

    print("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
