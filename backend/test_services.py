from backend.repositories import PlaceData
from backend.services import calculate_distance, optimize_route, recommend_places

def test_distance_zero(): assert calculate_distance((33.5,126.5),(33.5,126.5)) == 0
def test_rain_prefers_indoor():
    places={"out":PlaceData("out",[.8,0,.7],(33.5,126.5),"outdoor"),"in":PlaceData("in",[.2,1,.3],(33.51,126.51),"indoor")}
    assert recommend_places([.5,.5,.5],places,True)[0][0] == "in"
def test_origin_route():
    route,_=optimize_route({"far":(33.7,126.8),"near":(33.501,126.501)},["far","near"],(33.5,126.5)); assert route[0] == "near"
