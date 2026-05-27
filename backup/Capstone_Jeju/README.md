# 제주도 맞춤형 여행 추천 시스템 (Jeju Travel Recommendation)

실시간 날씨와 사용자 설문을 기반으로 제주도 여행 장소를 추천하고 최적화된 경로를 제공하는 풀스택 웹 애플리케이션입니다.

## 🚀 주요 기능

- **설문 기반 취향 분석**: 여행 스타일, 선호 장소, 활동량을 고려한 개인화 추천
- **실시간 날씨 반영**: 기상청 API를 통한 실시간 날씨 데이터로 실내/실외 추천 조정
- **경로 최적화**: TSP(Traveling Salesman Problem) 알고리즘으로 이동 경로 최소화
- **인터랙티브 지도**: Kakao Maps를 통한 장소 표시 및 경로 시각화
- **백엔드 API**: FastAPI 기반 추천 알고리즘 서버

## 🏗️ 아키텍처

```
프론트엔드 (React) ↔ 백엔드 (FastAPI) ↔ 데이터 (CSV)
       │                         │
   Kakao Maps              기상청 API
```

## 📁 프로젝트 구조

```
frontend/                 # React 프론트엔드
├── public/
├── src/
│   ├── components/      # WeatherBar, PlaceCard
│   ├── pages/          # SurveyPage, MapPage
│   └── App.js
├── package.json
└── .env.example

backend/                  # FastAPI 백엔드
├── main.py              # FastAPI 앱
├── services.py          # 추천 알고리즘
├── repositories.py      # 데이터 로더
├── models.py            # Pydantic 모델
├── data/                # 제주도 장소 CSV
└── requirements.txt
```

## 🛠️ 설치 및 실행

### 1. 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

백엔드 서버가 `http://localhost:8000`에서 실행됩니다.

### 2. 프론트엔드 실행

```bash
cd frontend
npm install
npm start
```

프론트엔드 개발 서버가 `http://localhost:3000`에서 실행됩니다.

### 3. 환경 변수 설정

프론트엔드 `.env` 파일 생성 (`.env.example` 참조):

```env
REACT_APP_KAKAO_MAP_KEY=your_kakao_map_key_here
REACT_APP_WEATHER_KEY=your_weather_api_key_here
```

## 🔑 API 키 발급

### Kakao Maps JavaScript API
1. [Kakao Developers](https://developers.kakao.com/) 가입
2. 애플리케이션 생성 → JavaScript 키 발급
3. `.env` 파일의 `REACT_APP_KAKAO_MAP_KEY`에 입력

### 기상청 날씨 API
1. [기상청 날씨开放API](https://data.go.kr/) 가입
2. 일반 인증키 발급
3. `.env` 파일의 `REACT_APP_WEATHER_KEY`에 입력

## 📊 데이터

- `backend/data/jeju_all_tagged_places_3.csv`: 1359개 제주도 장소 데이터
  - 각 장소는 제목, 태그 벡터(자연/실내/활동성), 좌표 포함
  - 태그 벡터는 [0.0~1.0] 범위로 정규화

## 🧠 알고리즘

### 1. 사용자 벡터 변환
설문 응답(`style`, `place`, `activity`)을 [자연 선호, 실내 선호, 활동성 선호] 3차원 벡터로 변환

### 2. 코사인 유사도 기반 추천
사용자 벡터와 장소 벡터 간의 코사인 유사도 계산

### 3. 날씨 가중치 적용
비 오는 날(`is_rainy=True`) 경우 실외 장소 패널티 적용

### 4. TSP 경로 최적화
추천된 장소들 간의 하버사인 거리를 기반으로 최단 경로 계산

## 🌐 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/recommend` | 설문 기반 장소 추천 |
| GET | `/weather` | 제주도 실시간 날씨 |
| GET | `/places` | 모든 장소 목록 |

## 🧪 테스트

```bash
# 백엔드 테스트
cd backend
pytest

# 프론트엔드 테스트
cd frontend
npm test
```

## 📄 라이선스

MIT License

## 👥 기여

버그 리포트 및 기능 제안은 Issue로 등록해주세요.
