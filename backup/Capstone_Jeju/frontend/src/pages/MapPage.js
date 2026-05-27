import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import PlaceCard from "../components/PlaceCard";

function MapPage() {
  const mapRef = useRef(null);
  const location = useLocation();
  const recommendation = location.state?.recommendation;

  // 백엔드 응답이 없을 경우 기본 데이터
  const defaultPlaces = [
    { id: 1, name: "한림공원", time: "09:00", duration: "2시간", type: "실외", lat: 33.399, lng: 126.261 },
    { id: 2, name: "협재 해수욕장", time: "11:30", duration: "1.5시간", type: "실외", lat: 33.394, lng: 126.239 },
    { id: 3, name: "애월 카페거리", time: "14:00", duration: "2시간", type: "실내", lat: 33.461, lng: 126.313 },
    { id: 4, name: "민속자연사박물관", time: "16:00", duration: "1.5시간", type: "실내", lat: 33.511, lng: 126.521 },
    { id: 5, name: "흑돼지 거리", time: "18:30", duration: "1시간", type: "맛집", lat: 33.499, lng: 126.531 },
  ];

  // 추천 데이터를 UI 형식으로 변환
  const places = recommendation
    ? recommendation.recommended_places.map((place, index) => ({
        id: index + 1,
        name: place.name,
        time: `${9 + index * 2}:00`, // 간단한 시간 생성
        duration: "1.5시간",
        type: place.vector[1] > 0.5 ? "실내" : "실외", // 실내 점수에 따라
        lat: place.coordinates[0],
        lng: place.coordinates[1],
        score: place.score,
      }))
    : defaultPlaces;

  // 경로 최적화 순서가 있다면 그 순서대로 정렬
  const routeOrder = recommendation?.optimized_route || places.map(p => p.name);
  const sortedPlaces = [...places].sort((a, b) => 
    routeOrder.indexOf(a.name) - routeOrder.indexOf(b.name)
  );

  useEffect(() => {
    console.log('MapPage useEffect running, sortedPlaces:', sortedPlaces);
    const { kakao } = window;
    console.log('window.kakao:', kakao);
    if (!kakao) {
      console.error('Kakao maps not loaded');
      return;
    }

    // 지도 중심을 첫 번째 장소로 설정
    const centerLat = sortedPlaces.length > 0 ? sortedPlaces[0].lat : 33.450701;
    const centerLng = sortedPlaces.length > 0 ? sortedPlaces[0].lng : 126.570667;
    console.log('Center:', centerLat, centerLng);

    const map = new kakao.maps.Map(mapRef.current, {
      center: new kakao.maps.LatLng(centerLat, centerLng),
      level: 10,
    });

    // 마커 + 말풍선
    sortedPlaces.forEach((place) => {
      const marker = new kakao.maps.Marker({
        position: new kakao.maps.LatLng(place.lat, place.lng),
        map,
      });
      const info = new kakao.maps.InfoWindow({
        content: `<div style="padding:6px;font-size:13px">${place.name}</div>`,
      });
      kakao.maps.event.addListener(marker, "click", () => info.open(map, marker));
    });

    // 경로선 연결
    const path = sortedPlaces.map((p) => new kakao.maps.LatLng(p.lat, p.lng));
    new kakao.maps.Polyline({
      map,
      path,
      strokeWeight: 3,
      strokeColor: "#378ADD",
      strokeOpacity: 0.7,
      strokeStyle: "shortdash",
    });
  }, [sortedPlaces]);

  return (
    <div style={{ display: "flex", height: "calc(100vh - 88px)" }}>
      <div ref={mapRef} style={{ flex: 1 }} />
      <div style={{ width: "280px", borderLeft: "0.5px solid #eee", overflowY: "auto", background: "white" }}>
        <div style={{ padding: "14px 16px", borderBottom: "0.5px solid #eee", fontWeight: "500", fontSize: "14px" }}>
          {recommendation ? "추천 동선" : "오늘의 추천 동선"}
        </div>
        {sortedPlaces.map((place) => (
          <PlaceCard
            key={place.id}
            number={place.id}
            name={place.name}
            time={place.time}
            duration={place.duration}
            type={place.type}
          />
        ))}
        {recommendation && (
          <div style={{ padding: "12px 16px", fontSize: "12px", color: "#666", borderTop: "0.5px solid #eee" }}>
            <div>총 거리: {recommendation.total_distance.toFixed(1)} km</div>
            <div>날씨: {recommendation.is_rainy ? "비" : "맑음"}</div>
            <div>{recommendation.message}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MapPage;