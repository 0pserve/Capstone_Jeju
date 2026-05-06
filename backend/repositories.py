"""
Repository 패턴 구현 - 장소 데이터 접근 계층
하드코딩된 데이터를 분리하고, 향후 SQLite/CSV 연결을 위한 인터페이스 제공
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional


class PlaceData:
    """장소 데이터 클래스"""
    def __init__(self, name: str, vector: List[float], coordinates: Tuple[float, float]):
        self.name = name
        self.vector = vector  # [자연친화도, 실내여부, 활동성]
        self.coordinates = coordinates  # (위도, 경도)


class PlaceRepository(ABC):
    """장소 Repository 추상 클래스"""
    
    @abstractmethod
    def get_all_places(self) -> Dict[str, PlaceData]:
        """모든 장소 데이터 조회"""
        pass
    
    @abstractmethod
    def get_place_by_name(self, name: str) -> Optional[PlaceData]:
        """이름으로 특정 장소 조회"""
        pass
    
    @abstractmethod
    def get_place_vectors(self) -> Dict[str, List[float]]:
        """장소 이름과 벡터만 조회"""
        pass
    
    @abstractmethod
    def get_place_coordinates(self) -> Dict[str, Tuple[float, float]]:
        """장소 이름과 좌표만 조회"""
        pass


class InMemoryPlaceRepository(PlaceRepository):
    """인메모리 장소 Repository (기본 구현)"""
    
    def __init__(self):
        self._places: Dict[str, PlaceData] = {}
        self._initialize_default_places()
    
    def _initialize_default_places(self):
        """CSV 파일에서 제주도 장소 데이터 로드"""
        import csv
        import os
        csv_path = os.path.join(os.path.dirname(__file__), "data", "jeju_all_tagged_places_3.csv")
        
        # 태그를 벡터로 변환하는 함수
        def tag_to_vector(tag: str) -> list:
            if tag == "indoor":
                return [0.2, 1.0, 0.3]   # [nature, indoor, activity]
            else:  # outdoor
                return [0.8, 0.0, 0.7]
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = row['title']
                    tag = row['tag']
                    # mapx = longitude, mapy = latitude
                    try:
                        lon = float(row['mapx'])
                        lat = float(row['mapy'])
                    except ValueError:
                        continue  # 좌표 변환 실패 시 건너뜀
                    vector = tag_to_vector(tag)
                    coordinates = (lat, lon)  # (latitude, longitude)
                    self._places[title] = PlaceData(
                        name=title,
                        vector=vector,
                        coordinates=coordinates
                    )
            print(f"[Repository] Loaded {len(self._places)} places from CSV")
        except FileNotFoundError:
            print(f"[Repository] CSV file not found: {csv_path}, falling back to default places")
            # 폴백: 기본 데이터 유지 (원래의 default_places)
            default_places = {
                "성산일출봉": {
                    "vector": [1.0, 0, 0.9],
                    "coordinates": (33.458, 126.942)
                },
                "아쿠아플라넷": {
                    "vector": [0.2, 1, 0.4],
                    "coordinates": (33.240, 126.427)
                },
                "비자림": {
                    "vector": [0.9, 0, 0.6],
                    "coordinates": (33.487, 126.809)
                },
                "제주현대미술관": {
                    "vector": [0.3, 1, 0.3],
                    "coordinates": (33.511, 126.523)
                }
            }
            for name, data in default_places.items():
                self._places[name] = PlaceData(
                    name=name,
                    vector=data["vector"],
                    coordinates=data["coordinates"]
                )
    
    def get_all_places(self) -> Dict[str, PlaceData]:
        return self._places.copy()
    
    def get_place_by_name(self, name: str) -> Optional[PlaceData]:
        return self._places.get(name)
    
    def get_place_vectors(self) -> Dict[str, List[float]]:
        return {name: place.vector for name, place in self._places.items()}
    
    def get_place_coordinates(self) -> Dict[str, Tuple[float, float]]:
        return {name: place.coordinates for name, place in self._places.items()}
    
    def add_place(self, name: str, vector: List[float], coordinates: Tuple[float, float]):
        """새 장소 추가 (확장용)"""
        self._places[name] = PlaceData(name=name, vector=vector, coordinates=coordinates)
    
    def remove_place(self, name: str) -> bool:
        """장소 삭제 (확장용)"""
        if name in self._places:
            del self._places[name]
            return True
        return False


# 향후 SQLite/CSV Repository 구현 예시:
# 
# class SQLitePlaceRepository(PlaceRepository):
#     """SQLite 기반 장소 Repository"""
#     
#     def __init__(self, db_path: str):
#         self.db_path = db_path
#         self._init_db()
#     
#     def _init_db(self):
#         import sqlite3
#         with sqlite3.connect(self.db_path) as conn:
#             conn.execute("""
#                 CREATE TABLE IF NOT EXISTS places (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     name TEXT UNIQUE NOT NULL,
#                     nature_score REAL,
#                     indoor_flag INTEGER,
#                     activity_score REAL,
#                     latitude REAL,
#                     longitude REAL
#                 )
#             """)
#     
#     def get_all_places(self) -> Dict[str, PlaceData]:
#         import sqlite3
#         with sqlite3.connect(self.db_path) as conn:
#             cursor = conn.execute("SELECT name, nature_score, indoor_flag, activity_score, latitude, longitude FROM places")
#             places = {}
#             for row in cursor.fetchall():
#                 name = row[0]
#                 vector = [row[1], row[2], row[3]]
#                 coordinates = (row[4], row[5])
#                 places[name] = PlaceData(name=name, vector=vector, coordinates=coordinates)
#             return places
# 
# 
# class CSVPlaceRepository(PlaceRepository):
#     """CSV 파일 기반 장소 Repository"""
#     
#     def __init__(self, csv_path: str):
#         import pandas as pd
#         self.df = pd.read_csv(csv_path)
#     
#     def get_all_places(self) -> Dict[str, PlaceData]:
#         places = {}
#         for _, row in self.df.iterrows():
#             name = row['name']
#             vector = [row['nature_score'], row['indoor_flag'], row['activity_score']]
#             coordinates = (row['latitude'], row['longitude'])
#             places[name] = PlaceData(name=name, vector=vector, coordinates=coordinates)
#         return places
