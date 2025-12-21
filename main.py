from fastapi import FastAPI, HTTPException, Query
import requests
from typing import Optional

app = FastAPI(title="SEC Raw Data Explorer", version="2.2")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FinancialBot/1.0; +mailto:duracle@gmail.com)",
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

# 1. 기업 검색 및 CIK 획득
@app.get("/search")
def search_company(q: str):
    # 실제 운영시에는 SEC의 ticker.txt 또는 별도 DB 연결 권장
    mapping = {
        "nvidia": {"name": "NVIDIA CORP", "ticker": "NVDA", "cik": "0001045810"},
        "apple": {"name": "APPLE INC", "ticker": "AAPL", "cik": "0000320193"},
        "tesla": {"name": "TESLA INC", "ticker": "TSLA", "cik": "0001318605"}
    }
    result = mapping.get(q.lower())
    if not result:
        raise HTTPException(status_code=404, detail="Company not found in mock data")
    return result

# 2. 최신 공시 목록 확인 (10-K, 10-Q 리스트 제공)
@app.get("/filings")
def get_filings(cik: str):
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    
    recent_filings = data.get("filings", {}).get("recent", {})
    filings_list = []
    
    # 10-K, 10-Q 필터링 (GPT가 사용자에게 선택지를 제시할 수 있도록 함)
    for i, form in enumerate(recent_filings.get("form", [])):
        if form in ["10-K", "10-Q"]:
            filings_list.append({
                "accessionNumber": recent_filings["accessionNumber"][i],
                "reportDate": recent_filings["reportDate"][i],
                "form": form,
                "primaryDocument": recent_filings["primaryDocument"][i]
            })
    return {"entityName": data.get("entityName"), "filings": filings_list[:10]}

# 3. 핵심: 특정 시점의 모든 원문 계정 항목 나열
@app.get("/report/raw")
def get_raw_report(cik: str, accessionNumber: str):
    """
    사용자가 선택한 보고서(accessionNumber)에 포함된 
    모든 XBRL 계정 과목과 수치를 필터링 없이 그대로 반환합니다.
    """
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/api/xbrl/company_facts/CIK{padded_cik}.json"
    
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="SEC Data Fetch Failed")
    
    full_data = res.json()
    acc_num_clean = accessionNumber.replace("-", "")
    
    raw_facts = {}
    facts_data = full_data.get("facts", {})

    # 모든 Taxonomy (us-gaap, dei 등)를 순회하며 해당 보고서 번호에 해당하는 수치만 추출
    for taxonomy in facts_data:
        for concept, details in facts_data[taxonomy].items():
            units = details.get("units", {})
            for unit_type in units:
                for entry in units[unit_type]:
                    # 사용자가 선택한 특정 보고서(accessionNumber)의 데이터만 필터링
                    if entry.get("accn") == accessionNumber:
                        if concept not in raw_facts:
                            raw_facts[concept] = []
                        raw_facts[concept].append({
                            "val": entry.get("val"),
                            "end": entry.get("end"),
                            "frame": entry.get("frame", "N/A"),
                            "unit": unit_type
                        })
    
    return {
        "entityName": full_data.get("entityName"),
        "accessionNumber": accessionNumber,
        "item_count": len(raw_facts),
        "data": raw_facts
    }
