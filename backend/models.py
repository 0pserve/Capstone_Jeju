"""
Pydantic 모델 정의 - 요청(Request) 및 응답(Response) 데이터 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class UserSurvey(BaseModel):
    """설문 기반 추천 요청 모델"""
    style: str = Field(..., description="여행 스타일: nature 또는 city")
    place: str = Field(..., description="선호 장소: indoor 또는 outdoor")
    activity: str = Field(..., description="활동량: active 또는 relax")
    is_rainy: bool = Field(
        default=False,
        description="비 오는 날 여부"
    )
    top_n: int = Field(
        default=3,
        ge=1,
        le=10,
        description="추천할 장소 수"
    )


class RecommendRequest(BaseModel):
    """여행 추천 요청 모델"""
    user_vector: List[float] = Field(
        ...,
        min_items=3,
        max_items=3,
        description="사용자 취향 벡터 [자연 선호, 실내 선호, 활동성 선호]"
    )
    is_rainy: bool = Field(
        default=False,
        description="비 오는 날 여부"
    )
    top_n: int = Field(
        default=3,
        ge=1,
        le=10,
        description="추천할 장소 수"
    )


class PlaceInfo(BaseModel):
    """장소 정보 모델"""
    name: str
    vector: List[float]
    coordinates: List[float]
    score: float


class RecommendResponse(BaseModel):
    """여행 추천 응답 모델"""
    recommended_places: List[PlaceInfo]
    optimized_route: List[str]
    total_distance: float
    is_rainy: bool
    message: Optional[str] = None
