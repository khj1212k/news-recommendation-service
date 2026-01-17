import json
import sys

from app.pipeline.pipeline_tasks import (
    assign_topics,
    clean_normalize,
    deduplicate,
    embed_newsletters,
    extract_keywords_task,
    fetch_articles,
    generate_newsletters,
    update_popularity,
)

TASKS = {
    "fetch_articles": fetch_articles,
    "clean_normalize": clean_normalize,
    "deduplicate": deduplicate,
    "extract_keywords": extract_keywords_task,
    "assign_topics": assign_topics,
    "generate_newsletters": generate_newsletters,
    "embed_newsletters": embed_newsletters,
    "update_popularity": update_popularity,
}


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: cli.py <task_name>", file=sys.stderr)
        print("Available tasks: " + ", ".join(sorted(TASKS)), file=sys.stderr)
        return 2

    task_name = sys.argv[1]
    task = TASKS.get(task_name)
    if not task:
        print(f"Unknown task: {task_name}", file=sys.stderr)
        print("Available tasks: " + ", ".join(sorted(TASKS)), file=sys.stderr)
        return 2

    result = task()
    if result is not None:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
