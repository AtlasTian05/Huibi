"""Explicit opt-in real API smoke test: python -m scripts.live_smoke_test --run-live.

Consumes DeepSeek credits. Uses a temporary account and synthetic essays/table.
Deletes its submissions, sessions and account; never prints credentials.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import secrets
import time
from pathlib import Path
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from src.exam_types import GENERAL, IELTS, IELTS_TASK1
from src.official_rubrics import DIMENSION_LABELS
from src.storage import db

TEXT_ESSAY = """Public libraries remain important even when information is widely available online.
They provide a quiet place where students can concentrate without paying for a seat or a drink.
For example, a student who shares a small apartment with several family members may find it difficult
to study at home. A library offers a practical alternative and gives that student access to books,
computers and reliable internet connections.

Libraries also help people develop the skills needed to evaluate information. Although search engines
return thousands of results, not every website is trustworthy. Librarians can teach readers to compare
sources and identify unsupported claims. These skills are especially valuable for younger learners.

Admittedly, maintaining library buildings costs public money. However, libraries can combine physical
services with digital collections instead of choosing only one approach. In my view, this combination
makes libraries a worthwhile investment because it supports both equal access and independent learning."""

IMAGE_ESSAY = """The table compares the percentages of students who used a public library in two cities
in 2010, 2015 and 2020.

Overall, library use increased substantially in both places over the period. City A consistently recorded
a higher proportion than City B, although the difference between them became smaller by the final year.

In 2010, 40 percent of students in City A used a public library, compared with 30 percent in City B.
By 2015, the figures had risen to 55 and 45 percent respectively. Both cities therefore experienced
an increase of 15 percentage points during the first five years, and the gap remained at ten points.

The upward trend continued between 2015 and 2020. Library use reached 70 percent in City A, while
City B finished at 65 percent. The latter city saw a larger increase in this second period, rising by
20 percentage points rather than 15. Consequently, the difference between the cities narrowed to
five percentage points in 2020."""


def table_image() -> bytes:
    """Black-and-white synthetic data table; labels/values carry all meaning."""
    image = Image.new("RGB", (1000, 480), "white")
    draw = ImageDraw.Draw(image)
    font_file = Path("/System/Library/Fonts/Helvetica.ttc")
    font = ImageFont.truetype(str(font_file), 30) if font_file.exists() else ImageFont.load_default(size=24)
    draw.text((50, 40), "Students using public libraries (%)", fill="black", font=font)
    rows = [["City / Year", "2010", "2015", "2020"], ["City A", "40", "55", "70"], ["City B", "30", "45", "65"]]
    for row_index, row in enumerate(rows):
        y = 145 + row_index * 85
        draw.line((50, y - 15, 950, y - 15), fill="#b0b0b0", width=1)
        for column, text in enumerate(row):
            draw.text((65 + column * 225, y), text, fill="black", font=font)
    draw.text((50, 420), "Synthetic educational test data", fill="#555555", font=font)
    output = io.BytesIO()
    image.save(output, "JPEG", quality=95)
    return output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true", help="Explicitly authorize billable real model requests")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if not args.run_live:
        parser.error("Add --run-live to authorize real DeepSeek requests")
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    account = "live_smoke_" + uuid4().hex[:10]
    credentials = {"username": account, "password": secrets.token_urlsafe(24)}
    directory = Path("reports")
    directory.mkdir(exist_ok=True)
    raw_image = table_image()
    (directory / "live-task1-table.jpg").write_bytes(raw_image)
    cases = [
        (
            "text",
            {"essay_text": TEXT_ESSAY, "exam_type": GENERAL, "essay_topic": "Are public libraries still important?"},
        ),
        (
            "image",
            {
                "essay_text": IMAGE_ESSAY,
                "exam_type": IELTS,
                "exam_subtype": IELTS_TASK1,
                "essay_topic": "Summarise the information in the table about student library use.",
                "essay_image_b64": base64.b64encode(raw_image).decode(),
                "essay_image_mime": "image/jpeg",
            },
        ),
    ]
    report = []
    with httpx.Client(base_url=args.base_url, timeout=600, trust_env=False) as client:
        try:
            client.post("/api/auth/register", json=credentials).raise_for_status()
            client.post("/api/auth/login", json=credentials).raise_for_status()
            for name, payload in cases:
                print(f"START {name}: real model + graph + PostgreSQL", flush=True)
                start = time.monotonic()
                response = client.post("/api/reviews", json=payload)
                if response.status_code != 201:
                    raise RuntimeError(f"{name}: HTTP {response.status_code}; inspect server-side diagnostics")
                result = response.json()
                assert result.get("primary_score") is not None and not result.get("score_error"), (
                    f"{name}: scoring failed"
                )
                dimensions = result.get("feedback_dimensions") or {}
                assert set(dimensions) == set(DIMENSION_LABELS), f"{name}: missing feedback dimensions"
                assert all(
                    item.get("strengths") and item.get("improvements") and item.get("tips")
                    for item in dimensions.values()
                ), f"{name}: empty feedback content"
                assert (result.get("coach_plan") or {}).get("action_items"), f"{name}: missing coaching plan"
                assert (result.get("coach_plan") or {}).get("model_essay", {}).get("text"), (
                    f"{name}: missing AI example"
                )
                if name == "image":
                    assert result.get("image_analysis"), "No image analysis"
                    analysis = result["image_analysis"]
                    assert all(value in analysis for value in ["40", "30", "70", "65"]), (
                        "Image analysis missed table values"
                    )
                    assert client.get(result["image_url"]).content == raw_image
                history = client.get("/api/submissions").json()
                assert any(row["id"] == result["id"] and row["essay_text"] == payload["essay_text"] for row in history)
                entry = {
                    "case": name,
                    "score": result["primary_score"],
                    "max": result["primary_max"],
                    "feedback_dimensions": len(result["feedback_dimensions"]),
                    "has_image_analysis": bool(result.get("image_analysis")),
                    "elapsed_seconds": round(time.monotonic() - start, 1),
                    "passed": True,
                }
                report.append(entry)
                (directory / "live-smoke-summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
                print(json.dumps(entry, ensure_ascii=False), flush=True)
            answer = client.post(
                "/api/questions", json={"question": "How can I write a clear topic sentence?", "exam_type": GENERAL}
            )
            answer.raise_for_status()
            assert answer.json().get("answer", "").strip(), "Empty knowledge answer"
            print("PASS knowledge question: real response (vector knowledge base not built)", flush=True)
        finally:
            for row in db.get_user_history(account):
                db.delete_submission(row["id"], account)
            with db.get_connection() as conn:
                if conn.execute("SELECT to_regclass('web_sessions')").fetchone()[0]:
                    conn.execute("DELETE FROM web_sessions WHERE username = %s", (account,))
                conn.execute("DELETE FROM users WHERE username = %s", (account,))
            print("Temporary test account, submissions and uploaded image cleaned up.", flush=True)
    print("LIVE_SMOKE_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
