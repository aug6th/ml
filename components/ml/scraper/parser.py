from __future__ import annotations
from datetime import datetime
from bs4 import BeautifulSoup
from ml.hate_speech import RawPost

def parse_gallery_page(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[tuple[str, str]] = []
    for tr in soup.select("tr.ub-content:not(.notice)"):
        post_id_elem = tr.select_one("td.gall_num")
        if not post_id_elem:
            continue
        post_id = post_id_elem.text.strip()
        if not post_id.isdigit():
            continue
        title_elem = tr.select_one("td.gall_tit a")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        if not title:
            continue
        posts.append((post_id, title))
    return posts

def parse_post_detail(html: str, gallery: str, post_id: str, title: str) -> RawPost | None:
    soup = BeautifulSoup(html, "html.parser")
    if "/error/deleted/" in html or "해당 갤러리는 존재하지 않습니다" in html:
        return None
    content_elem = soup.select_one("div.write_div")
    if not content_elem:
        content_elem = soup.select_one("div.s_write")
    if not content_elem:
        content_elem = soup.select_one(".writing_view_box .inner")
    if not content_elem:
        return None
    content = content_elem.get_text(strip=True)
    if not content:
        return None
    author = None
    author_elem = soup.select_one(".gall_writer .nickname em") or soup.select_one(".gall_writer .nickname")
    if author_elem:
        author = author_elem.get_text(strip=True)
    created_at = None
    date_elem = soup.select_one(".gall_date")
    if date_elem:
        date_str = date_elem.get("title") or date_elem.get_text(strip=True)
        for fmt in ["%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
            try:
                created_at = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                pass
    return RawPost(
        post_id=post_id,
        gallery=gallery,
        title=title,
        content=content,
        author=author,
        created_at=created_at,
        comments=[],
        url=f"https://gall.dcinside.com/board/view?id={gallery}&no={post_id}",
    )
