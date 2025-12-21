# 📁 main.py
# SEC Financial Data API (Enhanced Version with XBRL Parser)
# Author: [Your Name]
# Date: 2025-12-21

from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup

app = FastAPI(
    title="SEC Financial API (Enhanced)",
    description="Search SEC company filings and extract structured financial data from XBRL or HTML reports.",
    version="2.0"
)

# ✅ SEC API 규정상 User-Agent 필수
HEADERS = {
    "User-Agent": "YourAppName contact@yourdomain.com"
}

BASE_SEC = "https://data.sec.gov"
BASE_EDGAR = "https://www.sec.gov/cgi-bin/browse-edgar"

# ----------------------------------------------------------------------------
# 1️⃣ COMPANY SEARCH
# ----------------------------------------------------------------------------
@app.get("/search")
def search_companies(q: str):
    """기업명으로 SEC에서 검색"""
    url = f"https://data.sec.gov/submissions/CIK0001045810.json"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Search failed.")
    return res.json()

# ----------------------------------------------------------------------------
# 2️⃣ COMPANY INFO
# ----------------------------------------------------------------------------
@app.get("/company")
def get_company_info(cik: str):
    """기업 기본 정보 조회"""
    url = f"{BASE_SEC}/submissions/CIK{cik.zfill(10)}.json"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Company info fetch failed.")
    return res.json()

# ----------------------------------------------------------------------------
# 3️⃣ LATEST 10-K / 10-Q
# ----------------------------------------------------------------------------
@app.get("/filing/10K")
def get_10k(ticker: str):
    """최신 10-K 보고서 조회"""
    cik = get_cik_by_ticker(ticker)
    url = f"{BASE_EDGAR}?action=getcompany&CIK={cik}&type=10-K&owner=exclude&count=1"
    return {"ticker": ticker, "type": "10-K", "url": url}

@app.get("/filing/10Q")
def get_10q(ticker: str):
    """최신 10-Q 보고서 조회"""
    cik = get_cik_by_ticker(ticker)
    url = f"{BASE_EDGAR}?action=getcompany&CIK={cik}&type=10-Q&owner=exclude&count=1"
    return {"ticker": ticker, "type": "10-Q", "url": url}

# ----------------------------------------------------------------------------
# 4️⃣ XBRL JSON API (공식 SEC API)
# ----------------------------------------------------------------------------
@app.get("/xbrl")
def get_xbrl_concept(cik: str, concept: str):
    """
    SEC XBRL JSON API에서 특정 재무 항목 불러오기
    예: Revenues, NetIncomeLoss, Assets, CashAndCashEquivalentsAtCarryingValue
    """
    url = f"{BASE_SEC}/api/xbrl/company_concept/CIK{cik.zfill(10)}/us-gaap/{concept}.json"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise HTTPException(status_code=404, detail="XBRL concept not found.")
    return res.json()

# ----------------------------------------------------------------------------
# 5️⃣ HTML 문서 파서 (XBRL이 아닌 HTML 보고서에서 직접 데이터 추출)
# ----------------------------------------------------------------------------
@app.get("/extract")
def extract_from_html(url: str):
    """
    SEC 보고서(HTML)에서 주요 재무 데이터 자동 추출
    """
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

            # 주요 재무 항목 탐지
            if any(k in joined for k in ["revenue", "net income", "assets", "cash flow", "liabilities"]):
                data[" | ".join(cells[:2])] = cells[2:] if len(cells) > 2 else None

    return {"url": url, "extracted_items": data}

# ----------------------------------------------------------------------------
# 6️⃣ UTILITIES
# ----------------------------------------------------------------------------
def get_cik_by_ticker(ticker: str) -> str:
    """티커 → CIK 변환 (샘플용, 실제 구현 시 로컬 DB or SEC mapping 사용 권장)"""
    mapping = {
        "NVDA": "0001045810",
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        "AMZN": "0001018724"
    }
    return mapping.get(ticker.upper(), "0001045810")

# ----------------------------------------------------------------------------
# 7️⃣ ROOT
# ----------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "SEC Financial API (Enhanced with XBRL Parser)",
        "endpoints": [
            "/search?q=",
            "/company?cik=",
            "/filing/10K?ticker=",
            "/filing/10Q?ticker=",
            "/xbrl?cik=&concept=",
            "/extract?url="
        ]
    }
