"""
서비스 로직 구현 - 추천 알고리즘 및 날씨 API 연동
"""

import math
from typing import List, Tuple, Dict
from itertools import permutations

import numpy as np
from scipy.spatial.distance import cosine

from repositories import PlaceRepository, PlaceData


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """코사인 유사도 계산 (Scipy의 cosine 거리 사용)"""
    cos_dist = cosine(vec1, vec2)
    return 1 - cos_dist


def get_user_vector_from_survey(survey_responses: dict):
    """
    프론트엔드 설문 데이터를 받아 [자연, 실내, 활동성] 벡터로 변환합니다.
    각 항목은 0.0 ~ 1.0 사이의 값으로 정규화됩니다.
    """
    # 초기 점수 설정
    scores = {"nature": 0.5, "indoor": 0.5, "activity": 0.5}
    
    # 1. 여행 스타일 (자연 vs 도시)
    if survey_responses.get("style") == "nature":
        scores["nature"] += 0.3
    elif survey_responses.get("style") == "city":
        scores["nature"] -= 0.3

    # 2. 선호 장소 (실내 vs 실외)
    if survey_responses.get("place") == "indoor":
        scores["indoor"] = 1.0  # 실내 확정
        scores["activity"] -= 0.2
    elif survey_responses.get("place") == "outdoor":
        scores["indoor"] = 0.0  # 실외 확정
        scores["activity"] += 0.2

    # 3. 활동량 (정적 vs 동적)
    if survey_responses.get("activity") == "active":
        scores["activity"] += 0.4
    elif survey_responses.get("activity") == "relax":
        scores["activity"] -= 0.4

    # 점수 범위 제한 (0.0 ~ 1.0)
    user_vector = [
        max(0.0, min(1.0, scores["nature"])),
        max(0.0, min(1.0, scores["indoor"])),
        max(0.0, min(1.0, scores["activity"]))
    ]
    
    return user_vector


def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """두 좌표 간의 하버사인 거리 계산 (km) - 지구 곡률 반영"""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # 도(degree)를 라디안(radian)으로 변환
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 위도 및 경도 차이
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # 하버사인 공식
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 지구 평균 반지름 (km)
    R = 6371.0
    distance = R * c
    return distance


def recommend_places(
    user_vector: List[float],
    places: Dict[str, PlaceData],
    is_rainy: bool = False
) -> List[Tuple[str, float]]:
    """
    사용자 취향과 상황(비 여부)을 고려한 장소 추천
    
    Args:
        user_vector: 사용자 취향 벡터 [자연 선호, 실내 선호, 활동성 선호]
        places: 장소 이름과 PlaceData 객체를 매핑한 딕셔너리
        is_rainy: 비 오는 날 여부
    
    Returns:
        정렬된 (장소 이름, 최종 점수) 리스트
    """
    results = []
    
    for place_name, place_data in places.items():
        place_vector = place_data.vector
        
        # 기본 코사인 유사도 계산
        base_score = cosine_similarity(user_vector, place_vector)
        
        # 상황 가중치 적용
        final_score = base_score
        
        if is_rainy:
            indoor_flag = place_vector[1]  # 실내여부 (0 or 1)
            if indoor_flag == 0:  # 실외 장소
                final_score *= 0.3  # 70% 감점 (30%만 남음)
            else:  # 실내 장소
                final_score *= 1.5  # 50% 가중치 (150%)
        
        # Nature preference boost: if user likes nature, boost high-nature places
        user_nature = user_vector[0]
        place_nature = place_vector[0]
        if user_nature > 0.7 and place_nature > 0.7:
            # bonus factor up to 1.5
            nature_bonus = 1.0 + (user_nature * place_nature) * 0.3
            final_score *= nature_bonus
        
        # Landmark boost: important landmarks get extra weight
        important_landmarks = ["비자림", "사려니숲길", "절물자연휴양림"]
        if place_name in important_landmarks:
            final_score *= 1.2  # 20% boost
        
        results.append((place_name, final_score))
    
    # 내림차순 정렬 (높은 점수 순)
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def optimize_route(
    places_coords: Dict[str, Tuple[float, float]],
    top_places: List[str]
) -> Tuple[List[str], float]:
    """
    상위 장소의 방문 순서를 최적화 (단순 TSP)
    
    Args:
        places_coords: 장소 이름과 좌표를 매핑한 딕셔너리
        top_places: 상위 장소 이름 리스트
    
    Returns:
        (최적 순서, 총 거리) 튜플
    """
    if len(top_places) < 2:
        return top_places, 0.0
    
    best_route = None
    best_distance = float('inf')
    
    for perm in permutations(top_places):
        total_distance = 0
        for i in range(len(perm) - 1):
            coord1 = places_coords[perm[i]]
            coord2 = places_coords[perm[i + 1]]
            total_distance += calculate_distance(coord1, coord2)
        
        if total_distance < best_distance:
            best_distance = total_distance
            best_route = perm
    
    return list(best_route), best_distance


async def get_weather(api_key: str, lat: float = 33.3642, lon: float = 126.5553) -> dict:
    """
    외부 기상 API(OpenWeatherMap)를 호출하여 날씨 정보 조회
    
    Args:
        api_key: OpenWeatherMap API 키
        lat: 위도 (기본값: 제주도 중심 좌표)
        lon: 경도 (기본값: 제주도 중심 좌표)
    
    Returns:
        날씨 정보 딕셔너리 (is_rainy, description, temperature 등)
    
    Note:
        실제 API 호출을 위해서는 requests 또는 httpx 라이브러리가 필요합니다.
        현재는 스켈레톤 코드만 제공합니다.
    """
    # TODO: 실제 API 호출 구현
    # import httpx
    # 
    # url = f"https://api.openweathermap.org/data/2.5/weather"
    # params = {
    #     "lat": lat,
    #     "lon": lon,
    #     "appid": api_key,
    #     "units": "metric",
    #     "lang": "kr"
    # }
    # 
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(url, params=params)
    #     response.raise_for_status()
    #     data = response.json()
    # 
    #     weather_main = data.get("weather", [{}])[0].get("main", "")
    #     weather_desc = data.get("weather", [{}])[0].get("description", "")
    #     temperature = data.get("main", {}).get("temp", 0)
    # 
    #     # 비 오는 날 판별 (Rain, Drizzle, Thunderstorm)
    #     is_rainy = weather_main.lower() in ["rain", "drizzle", "thunderstorm"]
    # 
    #     return {
    #         "is_rainy": is_rainy,
    #         "weather_main": weather_main,
    #         "weather_description": weather_desc,
    #         "temperature": temperature
    #     }
    
    # 스켈레톤: 기본값 반환
    return {
        "is_rainy": False,
        "weather_main": "Clear",
        "weather_description": "맑음 (스켈레톤)",
        "temperature": 20.0
    }


class RecommendationService:
    """여행 추천 서비스 클래스"""
    
    def __init__(self, repository: PlaceRepository):
        self.repository = repository
    
    def get_recommendation(
        self,
        user_vector: List[float],
        is_rainy: bool = False,
        top_n: int = 3
    ) -> dict:
        """
        여행 추천 결과 생성
        
        Args:
            user_vector: 사용자 취향 벡터
            is_rainy: 비 오는 날 여부
            top_n: 추천할 장소 수
        
        Returns:
            추천 결과 딕셔너리
        """
        # 모든 장소 데이터 조회
        places = self.repository.get_all_places()
        places_coords = self.repository.get_place_coordinates()
        
        # 장소 추천
        recommendations = recommend_places(user_vector, places, is_rainy)
        
        # 상위 N개 선택
        top_places = [place for place, _ in recommendations[:top_n]]
        
        # 경로 최적화
        optimized_route, total_distance = optimize_route(places_coords, top_places)
        
        # 결과 구성
        recommended_places = []
        for place_name, score in recommendations[:top_n]:
            place_data = places[place_name]
            recommended_places.append({
                "name": place_name,
                "vector": place_data.vector,
                "coordinates": list(place_data.coordinates),
                "score": round(score, 4)
            })
        
        return {
            "recommended_places": recommended_places,
            "optimized_route": optimized_route,
            "total_distance": round(total_distance, 4),
            "is_rainy": is_rainy,
            "message": "비 오는 날 실내 추천입니다." if is_rainy else "맑은 날 야외 추천입니다."
        }
