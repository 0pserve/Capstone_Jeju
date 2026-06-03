"""
서비스 로직 구현 - 추천 알고리즘 및 날씨 API 연동
코사인 유사도 + 빔 서치 방식으로 개선
"""

import math
import random
from typing import List, Tuple, Dict
from itertools import permutations

import numpy as np
from scipy.spatial.distance import cosine

from repositories import PlaceRepository, PlaceData
print("빔서치 알고리즘 실행됨")

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """코사인 유사도 계산"""
    cos_dist = cosine(vec1, vec2)
    return 1 - cos_dist


def get_user_vector_from_survey(survey_responses: dict):
    """
    설문 데이터를 5차원 벡터로 변환
    [자연, 실내, 활동성, 음식, 문화]
    """
    scores = {
        "nature":   0.5,
        "indoor":   0.5,
        "activity": 0.5,
        "food":     0.5,  # 추가 — 맛집 선호도
        "culture":  0.5,  # 추가 — 문화/역사 선호도
    }

    # 1. 여행 스타일
    if survey_responses.get("style") == "nature":
        scores["nature"]  += 0.3
        scores["culture"] -= 0.1
    elif survey_responses.get("style") == "city":
        scores["nature"]  -= 0.3
        scores["food"]    += 0.2

    # 2. 선호 장소
    if survey_responses.get("place") == "indoor":
        scores["indoor"]   = 1.0
        scores["activity"] -= 0.2
        scores["culture"]  += 0.2
    elif survey_responses.get("place") == "outdoor":
        scores["indoor"]   = 0.0
        scores["activity"] += 0.2
        scores["nature"]   += 0.1

    # 3. 활동량
    if survey_responses.get("activity") == "active":
        scores["activity"] += 0.4
        scores["nature"]   += 0.1
    elif survey_responses.get("activity") == "relax":
        scores["activity"] -= 0.4
        scores["food"]     += 0.2
        scores["culture"]  += 0.1

    # 4. 음식 선호 (새로 추가)
    if survey_responses.get("food") == "local":
        scores["food"] += 0.4
    elif survey_responses.get("food") == "cafe":
        scores["food"]   += 0.2
        scores["indoor"] += 0.1

    # 5. 문화 선호 (새로 추가)
    if survey_responses.get("culture") == "history":
        scores["culture"] += 0.4
    elif survey_responses.get("culture") == "art":
        scores["culture"] += 0.3
        scores["indoor"]  += 0.1

    # 0.0 ~ 1.0 범위 제한
    user_vector = [
        max(0.0, min(1.0, scores["nature"])),
        max(0.0, min(1.0, scores["indoor"])),
        max(0.0, min(1.0, scores["activity"])),
        max(0.0, min(1.0, scores["food"])),
        max(0.0, min(1.0, scores["culture"])),
    ]

    return user_vector


def calculate_distance(
    coord1: Tuple[float, float],
    coord2: Tuple[float, float]
) -> float:
    """하버사인 공식으로 두 좌표 간 실측 거리 계산 (km)"""
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return 6371.0 * c


def recommend_places(
    user_vector: List[float],
    places: Dict[str, PlaceData],
    is_rainy: bool = False,
    dust_level: str = "good"  # 추가 — 미세먼지 수준
) -> List[Tuple[str, float]]:
    """
    코사인 유사도 + 날씨/미세먼지 패널티로 장소 점수 계산
    """
    results = []

    for place_name, place_data in places.items():
        # 장소 벡터도 5차원으로 맞추기
        place_vector = place_data.vector
        if len(place_vector) < 5:
            # 기존 3차원 데이터면 food=0.5, culture=0.5 기본값 추가
            place_vector = place_vector + [0.5, 0.5]

        base_score = cosine_similarity(user_vector, place_vector)
        final_score = base_score

        # 날씨 패널티
        is_outdoor = place_vector[1] < 0.5  # indoor 값이 낮으면 실외
        if is_rainy and is_outdoor:
            final_score *= 0.3
        elif is_rainy and not is_outdoor:
            final_score *= 1.5

        # 미세먼지 패널티 (새로 추가)
        if dust_level in ["bad", "very_bad"] and is_outdoor:
            final_score *= 0.5

        # 다양성을 위한 랜덤 노이즈 추가 (매번 다른 결과)
        noise = random.uniform(0.95, 1.05)
        final_score *= noise

        results.append((place_name, final_score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def beam_search_route(
    places_coords: Dict[str, Tuple[float, float]],
    place_scores: Dict[str, float],
    top_places: List[str],
    beam_width: int = 3  # 후보 경로 수 — 클수록 다양한 경로
) -> Tuple[List[str], float]:
    """
    빔 서치로 경로 최적화
    TSP 대신 사용 — 거리 + 선호도를 함께 고려해서 다양한 경로 생성

    beam_width: 동시에 탐색할 후보 경로 수
    """
    if len(top_places) < 2:
        return top_places, 0.0

    # 초기 빔 — 각 장소를 시작점으로 beam_width개 후보 생성
    beams = [([place], 0.0) for place in top_places[:beam_width]]

    for _ in range(len(top_places) - 1):
        candidates = []

        for current_route, current_cost in beams:
            visited = set(current_route)
            remaining = [p for p in top_places if p not in visited]

            for next_place in remaining:
                last_place = current_route[-1]
                dist = calculate_distance(
                    places_coords[last_place],
                    places_coords[next_place]
                )

                # 비용 = 거리 - 선호도 점수 (선호도 높은 장소 우선)
                preference_bonus = place_scores.get(next_place, 0) * 10
                new_cost = current_cost + dist - preference_bonus

                candidates.append((current_route + [next_place], new_cost))

        # 상위 beam_width개만 유지
        candidates.sort(key=lambda x: x[1])
        beams = candidates[:beam_width]

    # 최적 경로 선택
    best_route, best_cost = beams[0]

    # 실제 총 거리 계산
    total_distance = sum(
        calculate_distance(
            places_coords[best_route[i]],
            places_coords[best_route[i + 1]]
        )
        for i in range(len(best_route) - 1)
    )

    return best_route, round(total_distance, 4)


class RecommendationService:
    """여행 추천 서비스 클래스"""

    def __init__(self, repository: PlaceRepository):
        self.repository = repository

    def get_recommendation(
        self,
        user_vector: List[float],
        is_rainy: bool = False,
        dust_level: str = "good",
        top_n: int = 5
    ) -> dict:
        """추천 결과 생성"""
        

        places = self.repository.get_all_places()
        places_coords = self.repository.get_place_coordinates()

        # 장소 점수 계산
        recommendations = recommend_places(
            user_vector, places, is_rainy, dust_level
        )

        # 상위 N개 선택
        top_places = [place for place, _ in recommendations[:top_n]]
        place_scores = {place: score for place, score in recommendations[:top_n]}

        # 빔 서치로 경로 최적화
        optimized_route, total_distance = beam_search_route(
            places_coords,
            place_scores,
            top_places,
            beam_width=3
        )

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
            "total_distance": total_distance,
            "is_rainy": is_rainy,
            "dust_level": dust_level,
            "message": (
                "비 오는 날 실내 추천입니다." if is_rainy
                else "미세먼지로 실내 추천입니다." if dust_level in ["bad", "very_bad"]
                else "맑은 날 야외 추천입니다."
            )
        }
    print("그리디 알고리즘 실행됨")