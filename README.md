# SEC Financial API

SEC EDGAR에서 최신 10-K 및 10-Q 재무 보고서를 조회하는 FastAPI 기반 API입니다.

## 기능

- 티커 심볼로 최신 10-K/10-Q 파일링 조회
- GPTs Custom Actions와 호환되는 OpenAPI 스키마 제공
- SEC EDGAR 공식 데이터 소스 사용

## API 엔드포인트

### 1. 최신 파일링 조회
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

### 2. 최신 10-K 조회
```
GET /10k/{ticker}
```

**예시:**
```bash
curl https://your-app.onrender.com/10k/TSLA
```

### 3. 최신 10-Q 조회
```
GET /10q/{ticker}
```

**예시:**
```bash
curl https://your-app.onrender.com/10q/MSFT
```

## 응답 예시

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

3. **또는 수동 Schema 입력**
```yaml
openapi: 3.1.0
info:
  title: SEC Financial Data API
  version: 1.0.0
servers:
  - url: https://your-app.onrender.com
paths:
  /filing/{ticker}:
    get:
      operationId: getFilingByTicker
      summary: Get latest SEC filing for a ticker
      parameters:
        - name: ticker
          in: path
          required: true
          schema:
            type: string
          description: Stock ticker symbol
        - name: form_type
          in: query
          schema:
            type: string
            enum: ["10-K", "10-Q"]
            default: "10-K"
      responses:
        '200':
          description: Successful response
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
          description: Successful response
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
          description: Successful response
```

4. **GPT Instructions 예시**
```
You are a financial analyst assistant with access to SEC filings. 
When users ask about company financials, use the SEC API to fetch 
the latest 10-K or 10-Q filings and provide relevant information.

Available actions:
- Get latest 10-K annual report
- Get latest 10-Q quarterly report
- Search by ticker symbol (e.g., AAPL, TSLA, MSFT)
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
curl http://localhost:8000/10k/AAPL
```

## 주의사항

- SEC EDGAR API는 rate limiting이 있으므로 과도한 요청은 피하세요
- User-Agent 헤더는 SEC 요구사항입니다 (이메일 주소 포함 권장)
- 무료 Render 플랜은 15분 비활성 후 sleep 모드로 전환됩니다

## 라이선스

MIT License
