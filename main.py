# main.py
# SEC Financial API (Enhanced with Full Company Facts)
# Author: duracle
# Date: 2025-12-21

from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup

app = FastAPI(
    title="SEC Financial API (Full Company Facts Version)",
    description="Fetch all XBRL-reported financial items directly from SEC for each company.",
    version="2.1"
)

# ✅ SEC API 접근용 헤더 (이메일 필수)
HEADERS = {
    "User-Agent": "sec-financial-api/1.0 (duracle@gmail.com)",
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
    "Referer": "https://www.sec.gov"
}

BASE_SEC = "https://data.sec.gov"
BASE_EDGAR = "https://www.sec.gov/cgi-bin/browse-edgar"

# ----------------------------------------------------------------------------
# 기본 검색/정보
# ----------------------------------------------------------------------------
@app.get("/search")
def search_companies(q: str):
    if q.lower() == "nvidia":
        return {"company_name": "NVIDIA CORP", "ticker": "NVDA", "cik": "0001045810"}
    elif q.lower() == "apple":
        return {"company_name": "APPLE INC", "ticker": "AAPL", "cik": "0000320193"}
    elif q.lower() == "microsoft":
        return {"company_name": "MICROSOFT CORP", "ticker": "MSFT", "cik": "0000789019"}
    elif q.lower() == "amazon":
        return {"company_name": "AMAZON.COM INC", "ticker": "AMZN", "cik": "0001018724"}
    else:
        return {"detail": f"No mock data for query {q}"}

@app.get("/company")
def get_company_info(cik: str):
    """기업 기본 정보 조회"""
    url = f"{BASE_SEC}/submissions/CIK{cik.zfill(10)}.json"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="Failed to fetch company info")
    return res.json()

# ----------------------------------------------------------------------------
# 10-K / 10-Q 링크
# ----------------------------------------------------------------------------
@app.get("/filing/10K")
def get_10k(ticker: str):
    cik = get_cik_by_ticker(ticker)
    url = f"{BASE_EDGAR}?action=getcompany&CIK={cik}&type=10-K&owner=exclude&count=1"
    return {"ticker": ticker, "type": "10-K", "url": url}

@app.get("/filing/10Q")
def get_10q(ticker: str):
    cik = get_cik_by_ticker(ticker)
    url = f"{BASE_EDGAR}?action=getcompany&CIK={cik}&type=10-Q&owner=exclude&count=1"
    return {"ticker": ticker, "type": "10-Q", "url": url}

# ----------------------------------------------------------------------------
# XBRL 개별 Concept 조회
# ----------------------------------------------------------------------------
@app.get("/xbrl")
def get_xbrl_concept(cik: str, concept: str):
    cik = cik.zfill(10)
    url = f"{BASE_SEC}/api/xbrl/company_concept/CIK{cik}/us-gaap/{concept}.json"
    print(f"[DEBUG] Requesting SEC URL: {url}")
    res = requests.get(url, headers=HEADERS)
    print(f"[DEBUG] SEC Response Code: {res.status_code}")
    if res.status_code == 200:
        return res.json()
    elif res.status_code == 403:
        raise HTTPException(status_code=403, detail="SEC access denied (check User-Agent header).")
    elif res.status_code == 404:
        raise HTTPException(status_code=404, detail="XBRL concept not found.")
    else:
        raise HTTPException(status_code=res.status_code, detail=f"Unexpected SEC response: {res.text[:200]}")

# ----------------------------------------------------------------------------
# ✅ 회사 전체 재무 항목 (Company Facts) 나열
# ----------------------------------------------------------------------------
@app.get("/facts")
def get_company_facts(cik: str):
    """
    기업이 SEC에 보고한 모든 XBRL 재무 항목을 그대로 나열.
    (us-gaap, dei, srt 전체 포함)
    """
    cik = cik.zfill(10)
    url = f"{BASE_SEC}/api/xbrl/company_facts/CIK{cik}.json"
    print(f"[DEBUG] Fetching company facts: {url}")
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="Failed to fetch company facts from SEC.")

    data = res.json()
    entity_name = data.get("entityName", "Unknown Entity")
    facts = data.get("facts", {})

    # 전체 계정명 추출
    all_concepts = {}
    for section, items in facts.items():
        all_concepts[section] = list(items.keys())

    return {
        "entityName": entity_name,
        "sections": list(all_concepts.keys()),
        "total_sections": len(all_concepts),
        "concepts": all_concepts
    }

# ----------------------------------------------------------------------------
# HTML 문서 파서 (기존 유지)
# ----------------------------------------------------------------------------
@app.get("/extract")
def extract_from_html(url: str):
    """SEC 보고서(HTML)에서 주요 재무 데이터 자동 추출"""
    try:
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch document: {str(e)}")

    soup = BeautifulSoup(res.text, "html.parser")
    tables = soup.find_all("table")
    data = {}

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            joined = " ".join(cells).lower()
            if any(k in joined for k in ["revenue", "net income", "assets", "cash flow", "liabilities"]):
                key = " | ".join(cells[:2])
                val = cells[2:] if len(cells) > 2 else None
                data[key] = val

    return {"url": url, "extracted_items": data}

# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------
def get_cik_by_ticker(ticker: str) -> str:
    mapping = {
        "NVDA": "0001045810",
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        "AMZN": "0001018724"
    }
    return mapping.get(ticker.upper(), ticker)

# ----------------------------------------------------------------------------
# Root Endpoint
# ----------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "SEC Financial API (Enhanced with Full Company Facts)",
        "endpoints": [
            "/search?q=",
            "/company?cik=",
            "/filing/10K?ticker=",
            "/filing/10Q?ticker=",
            "/xbrl?cik=&concept=",
            "/facts?cik=",
            "/extract?url="
        ]
    }
