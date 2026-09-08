import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.models import UserSurvey, RecommendResponse
from backend.repositories import InMemoryPlaceRepository
from backend.services import RecommendationService, get_weather, get_user_vector_from_survey

app=FastAPI(title="제주 맞춤 여행 플래너 API",version="2.0.0")
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ALLOW_ORIGINS","http://localhost:3000").split(","),allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
BUILD_DIR=os.path.join(os.path.dirname(__file__),"..","frontend","build")
if os.path.isdir(BUILD_DIR): app.mount("/static",StaticFiles(directory=os.path.join(BUILD_DIR,"static")),name="static")
repository=InMemoryPlaceRepository(); service=RecommendationService(repository)

@app.get("/")
async def root():
    if os.path.isdir(BUILD_DIR): return FileResponse(os.path.join(BUILD_DIR,"index.html"))
    return {"message":"Jeju travel planner API", "docs":"/docs"}

@app.post("/recommend",response_model=RecommendResponse)
async def recommend(survey: UserSurvey):
    weather={"is_rainy":survey.weather_tolerance=="indoor","weather_description":"설문 날씨 조건","source":"survey"}
    try: weather=await get_weather(survey.start_lat,survey.start_lng)
    except Exception: pass
    result=service.get_recommendation(get_user_vector_from_survey(survey.model_dump()),bool(weather["is_rainy"]) or survey.weather_tolerance=="indoor",survey.top_n,survey.interests,(survey.start_lat,survey.start_lng),survey.start_time,survey.end_time)
    return RecommendResponse(plans=result["plans"],weather=weather,message=result["message"])

@app.get("/weather")
async def weather(lat:float=Query(33.3642),lon:float=Query(126.5553)):
    try: return await get_weather(lat,lon)
    except RuntimeError as error: raise HTTPException(503,str(error))
    except Exception as error: raise HTTPException(502,f"날씨 조회 오류: {error}")

@app.get("/health")
async def health(): return {"status":"ok","places":len(repository.get_all_places())}

@app.get("/places")
async def places(): return {name:{"coordinates":list(place.coordinates),"category":place.category} for name,place in repository.get_all_places().items()}
