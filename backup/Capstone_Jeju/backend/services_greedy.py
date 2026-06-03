"""
서비스 로직 구현 - 가중치 그리디 알고리즘 버전
기존 코사인 유사도 구조 유지 + 가중치 그리디로 경로 최적화
"""

import math
import random
from typing import List, Tuple, Dict

import numpy as np
from scipy.spatial.distance import cosine

from repositories import PlaceRepository, PlaceData
print("그리디 알고리즘 실행됨")

# ============================================================
# 1. 코사인 유사도
# ============================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """코사인 유사도 계산"""
    return 1 - cosine(vec1, vec2)


# ============================================================
# 2. 설문 → 5차원 사용자 벡터 변환
# ============================================================

def get_user_vector_from_survey(survey_responses: dict) -> List[float]:
    """
    설문 응답을 5차원 벡터로 변환
    [자연, 실내, 활동성, 음식, 문화]
    """
    scores = {
        "nature":   0.5,
        "indoor":   0.5,
        "activity": 0.5,
        "food":     0.5,
        "culture":  0.5,
    }

    if survey_responses.get("style") == "nature":
        scores["nature"]  += 0.3
        scores["culture"] -= 0.1
    elif survey_responses.get("style") == "city":
        scores["nature"]  -= 0.3
        scores["food"]    += 0.2

    if survey_responses.get("place") == "indoor":
        scores["indoor"]   = 1.0
        scores["activity"] -= 0.2
        scores["culture"]  += 0.2
    elif survey_responses.get("place") == "outdoor":
        scores["indoor"]   = 0.0
        scores["activity"] += 0.2
        scores["nature"]   += 0.1

    if survey_responses.get("activity") == "active":
        scores["activity"] += 0.4
        scores["nature"]   += 0.1
    elif survey_responses.get("activity") == "relax":
        scores["activity"] -= 0.4
        scores["food"]     += 0.2
        scores["culture"]  += 0.1

    if survey_responses.get("food") == "local":
        scores["food"] += 0.4
    elif survey_responses.get("food") == "cafe":
        scores["food"]   += 0.2
        scores["indoor"] += 0.1

    if survey_responses.get("culture") == "history":
        scores["culture"] += 0.4
    elif survey_responses.get("culture") == "art":
        scores["culture"] += 0.3
        scores["indoor"]  += 0.1

    return [max(0.0, min(1.0, v)) for v in scores.values()]


# ============================================================
# 3. 하버사인 거리 계산
# ============================================================

def calculate_distance(
    coord1: Tuple[float, float],
    coord2: Tuple[float, float]
) -> float:
    """두 좌표 간 하버사인 거리 계산 (km)"""
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ============================================================
# 4. 장소 점수 계산 (코사인 유사도 + 상황 가중치)
# ============================================================

def calculate_place_score(
    user_vector: List[float],
    place_vector: List[float],
    place_name: str,
    is_rainy: bool = False,
    dust_level: str = "good",
    current_coord: Tuple[float, float] = None,
    place_coord: Tuple[float, float] = None,
) -> float:
    """
    장소 최종 점수 계산
    
    최종 점수 = (코사인 유사도 × 0.4)
              + (날씨 적합도   × 0.3)
              + (거리 근접도   × 0.2)
              + (다양성 노이즈 × 0.1)
    """
    # 벡터 차원 맞추기 (기존 3차원 데이터 대비)
    if len(place_vector) < 5:
        place_vector = place_vector + [0.5] * (5 - len(place_vector))

    is_outdoor = place_vector[1] < 0.5  # indoor 값이 낮으면 실외

    # --- 코사인 유사도 점수 (0 ~ 1) ---
    similarity_score = cosine_similarity(user_vector, place_vector)

    # --- 날씨 적합도 점수 (0 ~ 1) ---
    if is_rainy:
        weather_score = 0.2 if is_outdoor else 1.0   # 비 오면 실외 불리
    elif dust_level in ["bad", "very_bad"]:
        weather_score = 0.3 if is_outdoor else 1.0   # 미세먼지 심하면 실외 불리
    else:
        weather_score = 1.0                           # 맑으면 모두 동일

    # --- 거리 근접도 점수 (0 ~ 1) ---
    # 현재 위치에서 가까울수록 높은 점수
    if current_coord and place_coord:
        dist = calculate_distance(current_coord, place_coord)
        # 최대 50km 기준으로 정규화 (제주도 최대 이동거리)
        distance_score = max(0.0, 1.0 - dist / 50.0)
    else:
        distance_score = 0.5  # 위치 정보 없으면 중간값

    # --- 다양성 노이즈 (매번 다른 결과를 위해) ---
    noise = random.uniform(0.9, 1.1)

    # --- 최종 가중치 합산 ---
    final_score = (
        similarity_score * 0.4 +
        weather_score    * 0.3 +
        distance_score   * 0.2
    ) * noise * 0.1  # 노이즈는 전체에 곱함

    return round(final_score, 4)


# ============================================================
# 5. 장소 추천 (점수 계산 + 정렬)
# ============================================================

def recommend_places(
    user_vector: List[float],
    places: Dict[str, PlaceData],
    is_rainy: bool = False,
    dust_level: str = "good",
    start_coord: Tuple[float, float] = None,
) -> List[Tuple[str, float]]:
    """
    모든 장소 점수 계산 후 내림차순 정렬
    """
    results = []

    for place_name, place_data in places.items():
        score = calculate_place_score(
            user_vector      = user_vector,
            place_vector     = place_data.vector,
            place_name       = place_name,
            is_rainy         = is_rainy,
            dust_level       = dust_level,
            current_coord    = start_coord,
            place_coord      = place_data.coordinates,
        )
        results.append((place_name, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ============================================================
# 6. 가중치 그리디 경로 최적화
# ============================================================

def greedy_route(
    places_coords: Dict[str, Tuple[float, float]],
    place_scores: Dict[str, float],
    top_places: List[str],
    start_coord: Tuple[float, float] = None,
) -> Tuple[List[str], float]:
    """
    가중치 그리디 알고리즘으로 경로 최적화

    동작 방식:
      1. 현재 위치에서 가장 가까우면서 점수 높은 장소 선택
      2. 선택한 장소로 이동 후 반복
      3. 모든 장소 방문할 때까지 반복

    선택 기준:
      그리디 점수 = 장소 선호도 점수 / 이동 거리
      → 선호도 높고 가까운 장소일수록 먼저 방문
    """
    if len(top_places) < 2:
        return top_places, 0.0

    unvisited  = list(top_places)
    route      = []
    total_dist = 0.0

    # 시작 위치 (없으면 첫 번째 장소 좌표 사용)
    current_coord = start_coord or places_coords[top_places[0]]

    while unvisited:
        best_place     = None
        best_greedy    = -float("inf")

        for place in unvisited:
            coord = places_coords[place]
            dist  = calculate_distance(current_coord, coord)

            preference = place_scores.get(place, 0.1)

            # 거리가 0이면 나누기 방지
            dist = max(dist, 0.01)

            # 그리디 점수 = 선호도 / 거리
            # → 선호도 높고 가까울수록 높은 점수
            greedy_score = preference / dist

            if greedy_score > best_greedy:
                best_greedy = greedy_score
                best_place  = place

        # 선택된 장소로 이동
        coord       = places_coords[best_place]
        total_dist += calculate_distance(current_coord, coord)
        current_coord = coord

        route.append(best_place)
        unvisited.remove(best_place)

    return route, round(total_dist, 4)


# ============================================================
# 7. 추천 서비스 클래스
# ============================================================

class RecommendationService:
    """여행 추천 서비스 클래스 — 가중치 그리디 버전"""

    def __init__(self, repository: PlaceRepository):
        self.repository = repository

    def get_recommendation(
        self,
        user_vector: List[float],
        is_rainy:   bool = False,
        dust_level: str  = "good",
        top_n:      int  = 5,
        start_coord: Tuple[float, float] = None,
    ) -> dict:
        """
        추천 결과 생성

        Args:
            user_vector:  사용자 취향 벡터 (5차원)
            is_rainy:     비 오는 날 여부
            dust_level:   미세먼지 수준 (good / normal / bad / very_bad)
            top_n:        추천 장소 수
            start_coord:  사용자 시작 위치 (숙소 좌표)
        """
        places       = self.repository.get_all_places()
        places_coords = self.repository.get_place_coordinates()

        # 장소 점수 계산
        recommendations = recommend_places(
            user_vector  = user_vector,
            places       = places,
            is_rainy     = is_rainy,
            dust_level   = dust_level,
            start_coord  = start_coord,
        )

        top_places   = [p for p, _ in recommendations[:top_n]]
        place_scores = {p: s for p, s in recommendations[:top_n]}

        # 가중치 그리디로 경로 최적화
        optimized_route, total_distance = greedy_route(
            places_coords = places_coords,
            place_scores  = place_scores,
            top_places    = top_places,
            start_coord   = start_coord,
        )

        recommended_places = []
        for place_name, score in recommendations[:top_n]:
            place_data = places[place_name]
            recommended_places.append({
                "name":        place_name,
                "vector":      place_data.vector,
                "coordinates": list(place_data.coordinates),
                "score":       score,
            })

        # 상황 메시지
        if is_rainy:
            message = "비 오는 날 실내 위주로 추천했어요."
        elif dust_level in ["bad", "very_bad"]:
            message = "미세먼지가 심해 실내 위주로 추천했어요."
        else:
            message = "맑은 날씨에 맞춰 야외 코스를 추천했어요."

        return {
            "recommended_places": recommended_places,
            "optimized_route":    optimized_route,
            "total_distance":     total_distance,
            "is_rainy":           is_rainy,
            "dust_level":         dust_level,
            "message":            message,
        }
