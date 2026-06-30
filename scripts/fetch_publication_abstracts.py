from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import textwrap
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUB_DIR = ROOT / "_publications"
OUTPUT_DIR = ROOT / "outputs"
CACHE_PATH = OUTPUT_DIR / "publication_abstracts_cache.json"
REPORT_PATH = OUTPUT_DIR / "publication_abstracts_report.json"


def scalar_value(front_matter: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.*)$", front_matter, re.MULTILINE)
    if not match:
        return ""
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    value = value.replace("''", "'")
    return html.unescape(value)


def split_front_matter(text: str) -> tuple[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    return text[4:end], text[end + 4 :]


def normalize_title(title: str) -> str:
    title = html.unescape(title).lower()
    title = re.sub(r"<[^>]+>", " ", title)
    title = re.sub(r"[\W_]+", " ", title, flags=re.UNICODE)
    return re.sub(r"\s+", " ", title).strip()


def title_score(a: str, b: str) -> float:
    na = normalize_title(a)
    nb = normalize_title(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def clean_abstract(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^Abstract\s*[:.\-]\s*", "", text, flags=re.IGNORECASE)
    text = repair_mojibake(text)
    return text


def repair_mojibake(text: str) -> str:
    markers = ("涓", "浠", "鍥", "瑙", "璁", "鐨", "鏄", "浜", "鈥", "檚")
    if sum(text.count(marker) for marker in markers) < 3:
        return text
    try:
        repaired = text.encode("gbk", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        return text
    if len(repaired) > len(text) * 0.45:
        return repaired
    return text


def garbled_score(text: str) -> int:
    markers = ("涓", "浠", "鍥", "瑙", "璁", "鐨", "鏄", "浜", "绔", "犵", "€")
    return sum(text.count(marker) for marker in markers)


def normalize_doi(doi: str | None) -> str:
    doi = (doi or "").strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi


def request_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JennettaGong.github.io metadata updater (mailto:example@example.com)"
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def semantic_scholar(title: str, year: str) -> dict | None:
    fields = "title,abstract,year,venue,externalIds,url"
    query = urllib.parse.urlencode({"query": title, "limit": "5", "fields": fields})
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{query}"
    try:
        data = request_json(url)
    except Exception as exc:
        return {"error": f"semantic_scholar: {exc}"}
    best = None
    for paper in data.get("data", []):
        score = title_score(title, paper.get("title", ""))
        if year and paper.get("year") and str(paper.get("year")) != str(year):
            score -= 0.05
        abstract = clean_abstract(paper.get("abstract", ""))
        candidate = {
            "source": "Semantic Scholar",
            "score": round(score, 3),
            "matched_title": paper.get("title", ""),
            "year": paper.get("year"),
            "url": paper.get("url", ""),
            "doi": (paper.get("externalIds") or {}).get("DOI", ""),
            "abstract": abstract,
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    return best


def openalex_abstract(index: dict | None) -> str:
    if not index:
        return ""
    words: list[str | None] = []
    for word, positions in index.items():
        for position in positions:
            while len(words) <= position:
                words.append(None)
            words[position] = word
    return clean_abstract(" ".join(word or "" for word in words))


def openalex(title: str, year: str) -> dict | None:
    params = {
        "search": title,
        "per-page": "5",
        "select": "title,abstract_inverted_index,publication_year,doi,id",
    }
    if year:
        params["filter"] = f"from_publication_date:{year}-01-01,to_publication_date:{year}-12-31"
    url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
    try:
        data = request_json(url)
    except Exception as exc:
        return {"error": f"openalex: {exc}"}
    best = None
    for work in data.get("results", []):
        score = title_score(title, work.get("title", ""))
        abstract = openalex_abstract(work.get("abstract_inverted_index"))
        candidate = {
            "source": "OpenAlex",
            "score": round(score, 3),
            "matched_title": work.get("title", ""),
            "year": work.get("publication_year"),
            "url": work.get("id", ""),
            "doi": work.get("doi", ""),
            "abstract": abstract,
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    return best


def crossref_by_doi(doi: str, title: str) -> dict | None:
    doi = normalize_doi(doi)
    if not doi:
        return None
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    try:
        data = request_json(url)
    except Exception as exc:
        return {"error": f"crossref_doi: {exc}"}
    item = data.get("message", {})
    matched_title = " ".join(item.get("title") or [])
    return {
        "source": "Crossref",
        "score": round(title_score(title, matched_title), 3),
        "matched_title": matched_title,
        "year": (((item.get("published-print") or item.get("published-online") or {}).get("date-parts") or [[None]])[0][0]),
        "url": item.get("URL", ""),
        "doi": item.get("DOI", ""),
        "abstract": clean_abstract(item.get("abstract", "")),
    }


def crossref_search(title: str, year: str) -> dict | None:
    params = {"query.title": title, "rows": "3"}
    if year:
        params["filter"] = f"from-pub-date:{year}-01-01,until-pub-date:{year}-12-31"
    url = f"https://api.crossref.org/works?{urllib.parse.urlencode(params)}"
    try:
        data = request_json(url)
    except Exception as exc:
        return {"error": f"crossref_search: {exc}"}
    best = None
    for item in (data.get("message", {}).get("items") or []):
        matched_title = " ".join(item.get("title") or [])
        candidate = {
            "source": "Crossref",
            "score": round(title_score(title, matched_title), 3),
            "matched_title": matched_title,
            "year": (((item.get("published-print") or item.get("published-online") or {}).get("date-parts") or [[None]])[0][0]),
            "url": item.get("URL", ""),
            "doi": item.get("DOI", ""),
            "abstract": clean_abstract(item.get("abstract", "")),
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    return best


def arxiv_search(title: str, year: str) -> dict | None:
    params = {
        "search_query": f"all:{title}",
        "start": "0",
        "max_results": "5",
    }
    url = f"https://export.arxiv.org/api/query?{urllib.parse.urlencode(params)}"
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "JennettaGong.github.io metadata updater"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            xml_text = response.read().decode("utf-8")
    except Exception as exc:
        return {"error": f"arxiv: {exc}"}
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    best = None
    for entry in root.findall("atom:entry", ns):
        matched_title = clean_abstract(entry.findtext("atom:title", "", ns))
        abstract = clean_abstract(entry.findtext("atom:summary", "", ns))
        published = entry.findtext("atom:published", "", ns)
        candidate = {
            "source": "arXiv",
            "score": round(title_score(title, matched_title), 3),
            "matched_title": matched_title,
            "year": published[:4],
            "url": entry.findtext("atom:id", "", ns),
            "doi": "",
            "abstract": abstract,
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    return best


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def find_abstract(path: Path, title: str, year: str, cache: dict) -> dict:
    key = str(path.relative_to(ROOT)).replace("\\", "/")
    if key in cache:
        result = cache[key]
        candidates = result.get("candidates", [])
        if result.get("status") != "found" and not any(
            (candidate.get("source") or "").startswith("Crossref") for candidate in candidates
        ):
            dois = sorted({normalize_doi(candidate.get("doi")) for candidate in candidates if candidate.get("doi")})
            for doi in dois:
                crossref_candidate = crossref_by_doi(doi, title)
                if crossref_candidate:
                    candidates.append(crossref_candidate)
                time.sleep(0.2)
            crossref_candidate = crossref_search(title, year)
            if crossref_candidate:
                candidates.append(crossref_candidate)
        if result.get("status") != "found" and not any(candidate.get("source") == "arXiv" for candidate in candidates):
            arxiv_candidate = arxiv_search(title, year)
            if arxiv_candidate:
                candidates.append(arxiv_candidate)
            time.sleep(3.1)
        result["candidates"] = candidates
        selected = select_result(title, year, candidates)
        if selected.get("status") == "found":
            result.update(selected)
        cache[key] = result
        save_cache(cache)
        return result

    candidates = []
    s2 = semantic_scholar(title, year)
    if s2:
        candidates.append(s2)
    time.sleep(1.1)
    oa = openalex(title, year)
    if oa:
        candidates.append(oa)
    time.sleep(0.2)

    result = {
        "title": title,
        "year": year,
        "status": "missing",
        "candidates": candidates,
    }
    result.update(select_result(title, year, candidates))
    cache[key] = result
    save_cache(cache)
    return result


def select_result(title: str, year: str, candidates: list[dict]) -> dict:
    trusted_dois = {
        normalize_doi(candidate.get("doi"))
        for candidate in candidates
        if candidate.get("score", 0) >= 0.98 and normalize_doi(candidate.get("doi"))
    }
    useful = []
    for candidate in candidates:
        abstract = clean_abstract(candidate.get("abstract", ""))
        if not abstract or garbled_score(abstract) > 8:
            continue
        doi = normalize_doi(candidate.get("doi"))
        score = candidate.get("score", 0)
        if score >= 0.82 or (doi and doi in trusted_dois):
            updated = {**candidate, "abstract": abstract, "doi": doi or candidate.get("doi", "")}
            useful.append(updated)
    if not useful:
        return {"status": "missing"}
    best = max(useful, key=lambda candidate: (candidate.get("score", 0), len(candidate["abstract"])))
    return {"status": "found", **best}


def format_yaml_block(key: str, value: str) -> str:
    value = clean_abstract(value).replace("---", "- - -")
    wrapped = textwrap.wrap(value, width=100, break_long_words=False, break_on_hyphens=False)
    if not wrapped:
        return f"{key}: \"\""
    return key + ": >-\n" + "\n".join(f"  {line}" for line in wrapped)


def remove_existing_abstract(front_matter: str) -> str:
    lines = front_matter.splitlines()
    output: list[str] = []
    skip_block = False
    for line in lines:
        if skip_block:
            if line.startswith(" ") or not line.strip():
                continue
            skip_block = False
        if re.match(r"^abstract:\s*[>|]", line):
            skip_block = True
            continue
        if re.match(r"^abstract:\s*", line):
            continue
        output.append(line)
    return "\n".join(output)


def insert_abstract(front_matter: str, abstract: str) -> str:
    front_matter = remove_existing_abstract(front_matter)
    block = format_yaml_block("abstract", abstract)
    if re.search(r"^citation:", front_matter, re.MULTILINE):
        return re.sub(r"^(citation:.*)$", rf"\1\n{block}", front_matter, count=1, flags=re.MULTILINE)
    return front_matter.rstrip() + "\n" + block


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write found abstracts to front matter")
    args = parser.parse_args()

    cache = load_cache()
    report = []
    changed = 0
    for path in sorted(PUB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8-sig")
        split = split_front_matter(text)
        if not split:
            report.append({"file": str(path.relative_to(ROOT)), "status": "bad_front_matter"})
            continue
        front_matter, body = split
        title = scalar_value(front_matter, "title")
        year = scalar_value(front_matter, "year")
        result = find_abstract(path, title, year, cache)
        item = {"file": str(path.relative_to(ROOT)), **result}
        report.append(item)
        if args.write and result.get("status") == "found":
            new_front_matter = insert_abstract(front_matter, result["abstract"])
            new_text = "---\n" + new_front_matter.rstrip() + "\n---" + body
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                changed += 1

    OUTPUT_DIR.mkdir(exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    found = sum(1 for item in report if item.get("status") == "found")
    print(f"total={len(report)} found={found} changed={changed} report={REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
