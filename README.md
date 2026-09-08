# 제주도 맞춤형 여행 추천 시스템 (Jeju Travel Recommendation)

여행 날짜·시간, 관심사, 숙소 위치, 날씨 조건을 바탕으로 제주 여행안 A/B/C를 만들고 지도와 일정표를 제공하는 풀스택 웹 애플리케이션입니다.

## 🚀 주요 기능

- **설문 기반 취향 분석**: 여행 스타일, 선호 장소, 활동량을 고려한 개인화 추천
- **실시간 날씨 반영**: 기상청 API를 통한 실시간 날씨 데이터로 실내/실외 추천 조정
- **여러 여행안 비교**: 취향 최우선, 날씨 안전, 이동 최소의 A/B/C 코스를 비교 후 선택
- **일정표 편집**: 예상 체류·이동시간, 장소 순서 변경, 장소 제외, 지도·예약 검색 및 PDF 출력
- **경로 정렬**: 숙소 출발지 기준 nearest-neighbor 방문 순서 정렬
- **인터랙티브 지도**: Kakao Maps를 통한 장소 표시 및 경로 시각화
- **백엔드 API**: FastAPI 기반 추천 알고리즘 서버

## 🏗️ 아키텍처

```
프론트엔드 (React) ↔ 백엔드 (FastAPI) ↔ 데이터 (CSV)
       │                         │
   Kakao Maps              OpenWeatherMap API
```

## 📁 프로젝트 구조

```
frontend/                 # React 프론트엔드
├── public/
├── src/
│   ├── components/      # WeatherBar, PlaceCard
│   ├── pages/          # SurveyPage, PlansPage, MapPage
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
python -m pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
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
```

## 🔑 API 키 발급

### Kakao Maps JavaScript API
1. [Kakao Developers](https://developers.kakao.com/) 가입
2. 애플리케이션 생성 → JavaScript 키 발급
3. `.env` 파일의 `REACT_APP_KAKAO_MAP_KEY`에 입력

### OpenWeatherMap
프로젝트 루트 `.env`에 `OPENWEATHER_API_KEY`를 설정합니다. 날씨 키는 서버에서만 사용됩니다.

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

### 4. 일정 및 경로
하버사인 직선거리와 평균 시속 28km를 사용해 예상 이동시간을 계산합니다. 실제 도로 길찾기 API는 프로젝트 범위에서 제외했습니다.

## 🌐 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/recommend` | 설문 기반 장소 추천 |
| GET | `/weather` | 제주도 실시간 날씨 |
| GET | `/places` | 모든 장소 목록 |
| GET | `/health` | 서버 상태 및 장소 수 |

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
