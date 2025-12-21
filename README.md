# SEC Financial API

SEC EDGAR에서 최신 10-K 및 10-Q 재무 보고서를 조회하는 FastAPI 기반 API입니다.

## 기능

- 기업명 또는 티커로 회사 검색
- 회사 상세 정보 조회 (CIK, 티커, 산업 분류, 세그먼트)
- 티커 심볼로 최신 10-K/10-Q 파일링 조회
- GPTs Custom Actions와 호환되는 OpenAPI 스키마 제공
- SEC EDGAR 공식 데이터 소스 사용

## API 엔드포인트

### 1. 회사 검색
```
GET /search?q={query}
```

**Parameters:**
- `q` (필수): 검색어 - 회사명 또는 티커 (최소 2자)

**예시:**
```bash
curl https://your-app.onrender.com/search?q=apple
curl https://your-app.onrender.com/search?q=TSLA
```

**응답 예시:**
```json
{
  "query": "apple",
  "count": 3,
  "results": [
    {
      "company_name": "Apple Inc.",
      "ticker": "AAPL",
      "cik": "0000320193"
    },
    {
      "company_name": "Apple Hospitality REIT, Inc.",
      "ticker": "APLE",
      "cik": "0001418121"
    }
  ]
}
```

### 2. 회사 상세 정보 조회
```
GET /company/{cik_or_ticker}
```

**Parameters:**
- `cik_or_ticker` (필수): CIK 번호 또는 티커 심볼

**예시:**
```bash
curl https://your-app.onrender.com/company/AAPL
curl https://your-app.onrender.com/company/0000320193
```

**응답 예시:**
```json
{
  "company_name": "Apple Inc.",
  "cik": "0000320193",
  "ticker": "AAPL",
  "sic": "3571",
  "industry": "ELECTRONIC COMPUTERS",
  "fiscal_year_end": "0930",
  "state_of_incorporation": "CA",
  "business_address": {
    "street": "ONE APPLE PARK WAY",
    "city": "CUPERTINO",
    "state": "CA",
    "zip": "95014"
  }
}
```

### 3. 최신 파일링 조회
```
GET /filing/{ticker}?form_type=10-K
```

**Parameters:**
- `ticker` (필수): 주식 티커 심볼 (예: AAPL, TSLA, MSFT)
- `form_type` (선택): 10-K 또는 10-Q (기본값: 10-K)

**예시:**
```bash
curl https://your-app.onrender.com/filing/AAPL?form_type=10-K
```

### 4. 최신 10-K 조회
```
GET /10k/{ticker}
```

**예시:**
```bash
curl https://your-app.onrender.com/10k/TSLA
```

### 5. 최신 10-Q 조회
```
GET /10q/{ticker}
```

**예시:**
```bash
curl https://your-app.onrender.com/10q/MSFT
```

## 파일링 응답 예시

```json
{
  "company_name": "Apple Inc.",
  "cik": "0000320193",
  "form_type": "10-K",
  "filing_date": "2023-11-03",
  "accession_number": "0000320193-23-000106",
  "document_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
  "edgar_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K&dateb=&owner=exclude&count=1"
}
```

## GPTs 사용 워크플로우

GPT가 사용자와 상호작용하는 권장 흐름:

1. **사용자 입력**: "애플 10-K 보고서 찾아줘"

2. **회사 검색**: 
   ```
   GET /search?q=apple
   ```
   여러 결과가 나오면 사용자에게 확인 요청

3. **회사 정보 제시**:
   ```
   GET /company/AAPL
   ```
   - 회사명: Apple Inc.
   - 티커: AAPL
   - CIK: 0000320193
   - 산업: ELECTRONIC COMPUTERS

4. **사용자 확인**: "맞습니다, 조회해주세요"

5. **파일링 조회**:
   ```
   GET /10k/AAPL
   ```

## Render 배포 방법

1. **GitHub에 코드 푸시**
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/sec-financial-api.git
git push -u origin main
```

2. **Render 설정**
   - [Render](https://render.com)에 로그인
   - "New +" → "Web Service" 클릭
   - GitHub 저장소 연결 (`sec-financial-api`)
   - 설정:
     - **Name**: `sec-financial-api`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - "Create Web Service" 클릭

3. **배포 완료**
   - 배포 URL: `https://sec-financial-api.onrender.com`

## GPTs Custom Action 설정

1. **ChatGPT에서 GPT 생성**
   - ChatGPT → "Explore GPTs" → "Create a GPT"
   - Configure → "Create new action" 클릭

2. **Schema 가져오기**
   - Authentication: None
   - Schema에 다음 URL 입력:
   ```
   https://your-app.onrender.com/openapi.json
   ```

3. **GPT Instructions 예시**
```
You are a SEC filings assistant. When users ask about company financials:

1. If they provide a company name (not ticker):
   - Use /search to find matching companies
   - Present top results with company name, ticker, and CIK
   - Ask user to confirm which company they mean

2. Once company is confirmed:
   - Use /company/{ticker} to show detailed company info
   - Present: company name, ticker, CIK, industry/segment
   - Ask user to confirm before fetching filings

3. After confirmation:
   - Use /10k/{ticker} for annual reports
   - Use /10q/{ticker} for quarterly reports
   - Provide the filing date and document URL

Always show company details before fetching filings to ensure accuracy.

Available actions:
- Search companies by name or ticker
- Get company details (CIK, ticker, industry, segments)
- Get latest 10-K annual report
- Get latest 10-Q quarterly report
```

4. **수동 Schema (선택사항)**

Schema를 자동으로 가져오는 것이 더 쉽지만, 수동으로 입력하려면:

```yaml
openapi: 3.1.0
info:
  title: SEC Financial Data API
  version: 1.0.0
servers:
  - url: https://your-app.onrender.com
paths:
  /search:
    get:
      operationId: searchCompanies
      summary: Search companies by name or ticker
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
          description: Search query (company name or ticker)
      responses:
        '200':
          description: Search results
  /company/{identifier}:
    get:
      operationId: getCompanyInfo
      summary: Get company details by CIK or ticker
      parameters:
        - name: identifier
          in: path
          required: true
          schema:
            type: string
          description: CIK number or ticker symbol
      responses:
        '200':
          description: Company information
  /10k/{ticker}:
    get:
      operationId: get10K
      summary: Get latest 10-K filing
      parameters:
        - name: ticker
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Filing information
  /10q/{ticker}:
    get:
      operationId: get10Q
      summary: Get latest 10-Q filing
      parameters:
        - name: ticker
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Filing information
```

## 로컬 테스트

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python main.py

# 테스트
curl http://localhost:8000/search?q=apple
curl http://localhost:8000/company/AAPL
curl http://localhost:8000/10k/AAPL
```

## 사용 예시

### 1단계: 회사 검색
```bash
curl "https://your-app.onrender.com/search?q=tesla"
```

### 2단계: 회사 정보 확인
```bash
curl "https://your-app.onrender.com/company/TSLA"
```

### 3단계: 파일링 조회
```bash
curl "https://your-app.onrender.com/10k/TSLA"
```

## 주의사항

- SEC EDGAR API는 rate limiting이 있으므로 과도한 요청은 피하세요
- User-Agent 헤더는 SEC 요구사항입니다 (이메일 주소 포함 권장)
- 무료 Render 플랜은 15분 비활성 후 sleep 모드로 전환됩니다
- 회사명 검색 시 부분 일치로 작동하므로 정확한 검색어 사용 권장

## 라이선스

MIT License
