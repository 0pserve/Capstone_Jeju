"""
FastAPI 메인 애플리케이션 - 상황 인식 기반 제주도 여행 추천 알고리즘
"""

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models import UserSurvey, RecommendResponse, PlaceInfo
from repositories import InMemoryPlaceRepository
from services import RecommendationService, get_weather, get_user_vector_from_survey

app = FastAPI(
    title="제주도 여행 추천 API",
    description="상황 인식 기반 제주도 여행 추천 알고리즘 FastAPI 서버",
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

# 정적 파일 서빙 (프론트엔드 빌드)
BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "jeju-travel-master", "build")
if os.path.exists(BUILD_DIR):
    # 정적 자산 (CSS, JS, 이미지)는 /static 경로로 제공
    app.mount("/static", StaticFiles(directory=os.path.join(BUILD_DIR, "static")), name="static")
    print(f"[Static] Serving static files from {BUILD_DIR}/static")
else:
    print(f"[Static] Build directory not found: {BUILD_DIR}")

# Repository 및 Service 초기화
place_repository = InMemoryPlaceRepository()
recommendation_service = RecommendationService(repository=place_repository)


@app.get("/")
async def serve_frontend():
    """프론트엔드 index.html 제공"""
    if os.path.exists(BUILD_DIR):
        return FileResponse(os.path.join(BUILD_DIR, "index.html"))
    else:
        raise HTTPException(status_code=404, detail="Frontend build not found")


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(survey: UserSurvey):
    """
    설문 기반 여행 장소 추천 엔드포인트
    
    - style: 여행 스타일 (nature/city)
    - place: 선호 장소 (indoor/outdoor)
    - activity: 활동량 (active/relax)
    - is_rainy: 비 오는 날 여부 (기본값: False)
    - top_n: 추천할 장소 수 (기본값: 3)
    """
    try:
        # 설문 데이터를 벡터로 변환
        user_vector = get_user_vector_from_survey({
            "style": survey.style,
            "place": survey.place,
            "activity": survey.activity
        })
        
        result = recommendation_service.get_recommendation(
            user_vector=user_vector,
            is_rainy=survey.is_rainy,
            top_n=survey.top_n
        )
        
        return RecommendResponse(
            recommended_places=[
                PlaceInfo(**place) for place in result["recommended_places"]
            ],
            optimized_route=result["optimized_route"],
            total_distance=result["total_distance"],
            is_rainy=result["is_rainy"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 처리 중 오류 발생: {str(e)}")


@app.get("/weather")
async def weather(
    api_key: str = Query(..., description="OpenWeatherMap API 키"),
    lat: float = Query(33.3642, description="위도 (기본값: 제주도 중심)"),
    lon: float = Query(126.5553, description="경도 (기본값: 제주도 중심)")
):
    """
    날씨 정보 조회 엔드포인트
    
    OpenWeatherMap API를 호출하여 현재 날씨 정보를 반환합니다.
    """
    try:
        weather_data = await get_weather(api_key=api_key, lat=lat, lon=lon)
        return weather_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"날씨 조회 중 오류 발생: {str(e)}")


@app.get("/places")
async def get_places():
    """등록된 모든 장소 정보 조회"""
    places = place_repository.get_all_places()
    return {
        name: {
            "vector": place.vector,
            "coordinates": list(place.coordinates)
        }
        for name, place in places.items()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
