import math, os
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus
from backend.repositories import PlaceData, PlaceRepository

Coordinate = Tuple[float, float]
KEYWORDS = {"nature": ("자연", "공원", "숲", "오름", "관광"), "food": ("음식", "한식", "양식", "식당"), "cafe": ("카페", "커피", "찻집", "제과"), "culture": ("문화", "박물관", "미술", "역사"), "shopping": ("쇼핑", "시장", "면세"), "beach": ("해변", "해수욕", "항구")}

def cosine_similarity(left, right):
    denominator = math.sqrt(sum(x*x for x in left))*math.sqrt(sum(x*x for x in right))
    return sum(a*b for a,b in zip(left,right))/denominator if denominator else 0.0

def get_user_vector_from_survey(survey):
    scores = {"nature": .8 if survey["style"] == "nature" else .2, "indoor": 1 if survey["place"] == "indoor" else 0, "activity": .9 if survey["activity"] == "active" else .2}
    return [scores["nature"], scores["indoor"], scores["activity"]]

def calculate_distance(a: Coordinate, b: Coordinate):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a,*b)); x = math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371*2*math.atan2(math.sqrt(x),math.sqrt(1-x))

def bonus(place, interests):
    searchable=f"{place.category} {place.overview}".lower()
    return min(.18*sum(any(word in searchable for word in KEYWORDS[item]) for item in interests), .36)

def recommend_places(vector, places, rainy=False, interests=()):
    scored=[]
    for name, place in places.items():
        score=cosine_similarity(vector,place.vector)+bonus(place,interests)
        if rainy: score*=1.25 if place.tag in {"indoor","mixed"} else .35
        scored.append((name,score))
    return sorted(scored,key=lambda item:item[1],reverse=True)

def optimize_route(coordinates, names, start=None):
    remaining=set(names); route=[]; current=start or coordinates[names[0]]
    while remaining:
        name=min(remaining,key=lambda n:calculate_distance(current,coordinates[n])); route.append(name); remaining.remove(name); current=coordinates[name]
    points=([start] if start else [])+[coordinates[n] for n in route]
    return route, sum(calculate_distance(points[i],points[i+1]) for i in range(len(points)-1))

def place_type(place):
    text=f"{place.category} {place.overview}".lower()
    if any(x in text for x in KEYWORDS["cafe"]): return "cafe"
    if any(x in text for x in KEYWORDS["food"]): return "restaurant"
    if any(x in text for x in KEYWORDS["shopping"]): return "shopping"
    return "attraction"

def duration(place): return 60 if place_type(place) in {"cafe","restaurant","shopping"} else 120 if place.tag == "outdoor" else 90
def clock(minutes): return f"{minutes//60:02d}:{minutes%60:02d}"

async def get_weather(lat=33.3642, lon=126.5553):
    key=os.getenv("OPENWEATHER_API_KEY")
    if not key: raise RuntimeError("OPENWEATHER_API_KEY is not configured")
    import httpx
    async with httpx.AsyncClient(timeout=8) as client:
        response=await client.get("https://api.openweathermap.org/data/2.5/weather",params={"lat":lat,"lon":lon,"appid":key,"units":"metric","lang":"kr"}); response.raise_for_status()
    data=response.json(); item=data.get("weather",[{}])[0]; main=item.get("main","")
    return {"is_rainy":main.lower() in {"rain","drizzle","thunderstorm","snow"},"weather_description":item.get("description","정보 없음"),"temperature":data.get("main",{}).get("temp"),"source":"openweather"}

class RecommendationService:
    def __init__(self, repository: PlaceRepository): self.repository=repository
    def build_plan(self, ident,title,subtitle,reason,ranked,places,start,top_n,start_time,end_time):
        names=[n for n,_ in ranked[:top_n]]; route,total=optimize_route(self.repository.get_place_coordinates(),names,start); scores=dict(ranked); cursor=sum(int(x)*v for x,v in zip(start_time.split(':'),(60,1))); limit=sum(int(x)*v for x,v in zip(end_time.split(':'),(60,1))); previous=start; items=[]
        for name in route:
            place=places[name]; travel=max(8,math.ceil(calculate_distance(previous,place.coordinates)/28*60)); stay=duration(place)
            if cursor+travel+stay>limit and items: continue
            cursor+=travel; arrival=clock(cursor); cursor+=stay; kind=place_type(place); query=quote_plus(f"{name} {place.address}")
            items.append({"name":name,"vector":place.vector,"coordinates":list(place.coordinates),"score":round(scores[name],4),"category":place.category,"address":place.address,"overview":place.overview,"place_type":kind,"estimated_duration_minutes":stay,"arrival_time":arrival,"departure_time":clock(cursor),"travel_minutes_from_previous":travel,"map_search_url":f"https://map.kakao.com/?q={query}","booking_search_url":f"https://search.naver.com/search.naver?query={quote_plus(name+' 예약')}" if kind=="restaurant" else ""}); previous=place.coordinates
        return {"id":ident,"title":title,"subtitle":subtitle,"reason":reason,"total_distance":round(total,2),"total_minutes":cursor-sum(int(x)*v for x,v in zip(start_time.split(':'),(60,1))),"places":items}
    def get_recommendation(self,user_vector,is_rainy=False,top_n=5,interests=None,start_coordinates=None,start_time="09:00",end_time="19:00"):
        places=self.repository.get_all_places(); start=start_coordinates or (33.4996,126.5312); ranked=recommend_places(user_vector,places,is_rainy,interests or []); weather=recommend_places(user_vector,places,True,interests or []); nearby=sorted(ranked,key=lambda x:calculate_distance(start,places[x[0]].coordinates)-5*x[1])
        return {"plans":[self.build_plan("preference","A. 취향 최우선 코스","선호 활동 중심","선택한 관심사를 가장 많이 반영했습니다.",ranked,places,start,top_n,start_time,end_time),self.build_plan("weather","B. 날씨 안전 코스","실내·복합 장소 중심","비가 와도 즐길 수 있는 장소를 우선했습니다.",weather,places,start,top_n,start_time,end_time),self.build_plan("nearby","C. 이동 최소 코스","숙소 주변 중심","숙소 출발 이동 부담을 줄였습니다.",nearby,places,start,top_n,start_time,end_time)],"message":"이동 시간은 직선거리와 평균 속도에 따른 추정값입니다."}
