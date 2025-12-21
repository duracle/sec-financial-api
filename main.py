from fastapi import FastAPI, HTTPException
import requests

app = FastAPI(title="SEC Raw Data Explorer", version="2.5")

# ✅ SEC가 요구하는 필수 헤더 (이메일 포함)
HEADERS = {
    "User-Agent": "Individual Researcher (duracle@gmail.com)",
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

# ----------------------------------------------------------------------------
# 1. 기업 검색 (Ticker -> CIK)
# ----------------------------------------------------------------------------
@app.get("/search")
def search_company(q: str):
    # 실제로는 SEC의 ticker_to_cik JSON을 연동하는 것이 좋으나, 우선 Mock 데이터로 구현
    mapping = {
        "nvidia": {"name": "NVIDIA CORP", "ticker": "NVDA", "cik": "0001045810"},
        "apple": {"name": "APPLE INC", "ticker": "AAPL", "cik": "0000320193"},
        "tesla": {"name": "TESLA INC", "ticker": "TSLA", "cik": "0001318605"},
        "microsoft": {"name": "MICROSOFT CORP", "ticker": "MSFT", "cik": "0000789019"}
    }
    key = q.lower()
    if key in mapping:
        return mapping[key]
    raise HTTPException(status_code=404, detail="Company not found. Please try Nvidia, Apple, etc.")

# ----------------------------------------------------------------------------
# 2. 공시 목록 조회 (GPT가 사용자에게 10-K, 10-Q 선택지를 제시할 때 사용)
# ----------------------------------------------------------------------------
@app.get("/filings")
def get_filings(cik: str):
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="SEC submissions fetch failed.")
    
    data = res.json()
    recent = data.get("filings", {}).get("recent", {})
    
    filings = []
    for i, form in enumerate(recent.get("form", [])):
        if form in ["10-K", "10-Q"]:
            filings.append({
                "date": recent["reportDate"][i],
                "form": form,
                "accessionNumber": recent["accessionNumber"][i], # 10K/10Q 고유 ID
                "primaryDocument": recent["primaryDocument"][i]
            })
    return {"entityName": data.get("entityName"), "filings": filings[:10]}

# ----------------------------------------------------------------------------
# 3. 핵심: 원문 계정 항목 나열 (/report/raw)
# ----------------------------------------------------------------------------
@app.get("/report/raw")
def get_raw_report(cik: str, accessionNumber: str):
    """
    특정 보고서(accessionNumber)의 모든 XBRL 원문 데이터를 필터링 없이 가져옵니다.
    """
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/api/xbrl/company_facts/CIK{padded_cik}.json"
    
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="SEC facts fetch failed.")
    
    full_data = res.json()
    facts = full_data.get("facts", {})
    
    output_data = {}

    # 모든 Taxonomy(us-gaap, dei, srt 등)를 순회하며 해당 보고서 번호 데이터만 추출
    for taxonomy in facts:
        for concept, details in facts[taxonomy].items():
            units = details.get("units", {})
            for unit_type in units:
                for entry in units[unit_type]:
                    # 사용자가 선택한 그 시점의 보고서(accessionNumber) 데이터만 매칭
                    if entry.get("accn") == accessionNumber:
                        # 중복 방지를 위해 가장 최신 'end' 날짜 기준 혹은 'frame' 기준으로 저장
                        output_data[concept] = {
                            "value": entry.get("val"),
                            "unit": unit_type,
                            "end_date": entry.get("end"),
                            "label": details.get("description", concept) # 원문 설명
                        }
    
    if not output_data:
        raise HTTPException(status_code=404, detail="No data found for this specific report.")

    return {
        "entityName": full_data.get("entityName"),
        "reportID": accessionNumber,
        "raw_items_count": len(output_data),
        "items": output_data
    }
