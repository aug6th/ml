import asyncio
from pathlib import Path

from ml.http.core import Client


async def fetch_raw_html(path: str, params: dict | None) -> None:
    async with Client(
        "https://gall.dcinside.com",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    ) as http:
        resp = await http.get(path, params)
        text = resp.text

        print("status:", resp.status_code, "len(text):", len(text))

        out_dir = Path("input/dcinside_raw")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "response.html"
        out_path.write_text(text, encoding="utf-8")
        print("saved to:", out_path)


def test_raw_dcbest() -> None:
    asyncio.run(
        fetch_raw_html(
            "/board/lists",
            {"id": "dcbest", "page": 1},
        )
    )


def test_raw_baseball() -> None:
    asyncio.run(
        fetch_raw_html(
            "/board/lists",
            {"id": "baseball_new11", "page": 1},
        )
    )


if __name__ == "__main__":  # 직접 돌릴 때
    asyncio.run(
        fetch_raw_html(
            "/board/lists",
            {"id": "dcbest", "page": 1},
        )
    )
