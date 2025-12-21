from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional
import re
from datetime import datetime

app = FastAPI(
    title="SEC Financial Data API",
    description="API to fetch latest 10-K and 10-Q filings from SEC EDGAR",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SEC EDGAR API 헤더 (User-Agent 필수)
HEADERS = {
    'User-Agent': 'SEC Financial API contact@example.com'
}

def get_cik_from_ticker(ticker: str) -> Optional[str]:
    """티커 심볼로 CIK 번호 조회"""
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        companies = response.json()
        ticker_upper = ticker.upper()
        
        for company in companies.values():
            if company['ticker'] == ticker_upper:
                # CIK를 10자리로 패딩
                return str(company['cik_str']).zfill(10)
        
        return None
    except Exception as e:
        print(f"Error getting CIK: {e}")
        return None

def get_latest_filing(cik: str, form_type: str) -> dict:
    """최신 10-K 또는 10-Q 파일링 조회"""
    try:
        # SEC EDGAR submissions API
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        data = response.json()
        filings = data.get('filings', {}).get('recent', {})
        
        # 해당 form type의 최신 파일링 찾기
        for i, form in enumerate(filings.get('form', [])):
            if form == form_type:
                accession_number = filings['accessionNumber'][i]
                filing_date = filings['filingDate'][i]
                primary_document = filings['primaryDocument'][i]
                
                # 파일 URL 생성
                accession_clean = accession_number.replace('-', '')
                document_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_document}"
                
                return {
                    "company_name": data.get('name', 'N/A'),
                    "cik": cik,
                    "form_type": form_type,
                    "filing_date": filing_date,
                    "accession_number": accession_number,
                    "document_url": document_url,
                    "edgar_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}&dateb=&owner=exclude&count=1"
                }
        
        return None
    except Exception as e:
        print(f"Error getting filing: {e}")
        return None

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "SEC Financial Data API",
        "endpoints": {
            "/filing/{ticker}": "Get latest 10-K or 10-Q for a ticker",
            "/10k/{ticker}": "Get latest 10-K filing",
            "/10q/{ticker}": "Get latest 10-Q filing",
            "/docs": "OpenAPI documentation"
        }
    }

@app.get("/filing/{ticker}")
async def get_filing(ticker: str, form_type: Optional[str] = "10-K"):
    """
    특정 티커의 최신 SEC 파일링 조회
    
    Parameters:
    - ticker: 주식 티커 심볼 (예: AAPL, TSLA)
    - form_type: 파일링 유형 (10-K 또는 10-Q, 기본값: 10-K)
    """
    if form_type not in ["10-K", "10-Q"]:
        raise HTTPException(status_code=400, detail="form_type must be '10-K' or '10-Q'")
    
    # CIK 조회
    cik = get_cik_from_ticker(ticker)
    if not cik:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
    
    # 파일링 조회
    filing = get_latest_filing(cik, form_type)
    if not filing:
        raise HTTPException(status_code=404, detail=f"No {form_type} filing found for {ticker}")
    
    return filing

@app.get("/10k/{ticker}")
async def get_10k(ticker: str):
    """특정 티커의 최신 10-K 파일링 조회"""
    return await get_filing(ticker, "10-K")

@app.get("/10q/{ticker}")
async def get_10q(ticker: str):
    """특정 티커의 최신 10-Q 파일링 조회"""
    return await get_filing(ticker, "10-Q")

@app.get("/openapi.json")
async def get_openapi_schema():
    """GPTs Action용 OpenAPI 스키마"""
    return app.openapi()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
