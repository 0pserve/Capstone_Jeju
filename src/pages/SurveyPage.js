import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// 설문 선택지 데이터
const OPTIONS = {
  activities: ["자연 / 트레킹", "맛집 탐방", "카페 투어", "문화 / 박물관", "쇼핑", "해수욕"],
  people:     ["혼자", "2인", "3~4인", "5인 이상"],
  location:   ["제주시", "서귀포시", "애월", "성산"],
  weather:    ["비와도 괜찮아요", "날씨 좋을 때만 실외", "실내 위주로"],
};

// 백엔드 API 기본 URL
const API_BASE = "http://localhost:8000";

// 버튼 하나 — 선택됐는지에 따라 색이 바뀔요
function OptionBtn({ label, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "8px 16px", borderRadius: "8px", cursor: "pointer", fontSize: "13px",
        border: selected ? "1.5px solid #378ADD" : "0.5px solid #ddd",
        background: selected ? "#E6F1FB" : "white",
        color: selected ? "#0C447C" : "#333",
        fontWeight: selected ? "500" : "400",
      }}
    >
      {label}
    </button>
  );
}

function SurveyPage() {
  const navigate = useNavigate();
  const [activities, setActivities] = useState([]); // 여러 개 선택 가능
  const [people,     setPeople]     = useState("");  // 1개만 선택
  const [location,   setLocation]   = useState("");
  const [weather,    setWeather]    = useState("");
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);

  // 활동은 토글(여러 개 선택), 나머지는 단일 선택
  const toggleActivity = (item) =>
    setActivities((prev) =>
      prev.includes(item) ? prev.filter((a) => a !== item) : [...prev, item]
    );

  // 설문 데이터를 백엔드가 기대하는 형식으로 변환
  const mapToSurvey = () => {
    // 간단한 매핑 로직 (실제로는 더 정교해야 함)
    let style = "nature";
    if (activities.some(a => a.includes("문화") || a.includes("쇼핑"))) {
      style = "city";
    }

    let place = "outdoor";
    if (weather === "실내 위주로") {
      place = "indoor";
    }

    let activity = "relax";
    if (activities.some(a => a.includes("맛집") || a.includes("카페") || a.includes("트레킹"))) {
      activity = "active";
    }

    const is_rainy = weather !== "비와도 괜찮아요"; // 간단한 가정
    const top_n = 5;

    return { style, place, activity, is_rainy, top_n };
  };

  const handleSubmit = async () => {
    // 필수 선택 확인
    if (activities.length === 0 || !people || !location || !weather) {
      alert("모든 항목을 선택해주세요.");
      return;
    }

    const surveyData = mapToSurvey();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/recommend`, surveyData);
      // 응답 데이터를 MapPage로 전달
      navigate("/map", { state: { recommendation: response.data } });
    } catch (err) {
      console.error("추천 요청 실패:", err);
      setError("추천 서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "560px", margin: "0 auto", padding: "2rem 1rem" }}>
      <h2 style={{ fontSize: "20px", fontWeight: "500", marginBottom: "6px" }}>어떤 여행을 원하시나요?</h2>
      <p style={{ fontSize: "14px", color: "#888", marginBottom: "2rem" }}>
        선택한 취향과 실시간 날씨를 반영해서 최적 동선을 추천해드려요
      </p>

      {[
        { label: "선호하는 활동", items: OPTIONS.activities, selected: activities, onClick: toggleActivity },
        { label: "여행 인원",     items: OPTIONS.people,     selected: [people],   onClick: setPeople },
        { label: "숙소 위치",     items: OPTIONS.location,   selected: [location], onClick: setLocation },
        { label: "날씨 민감도",   items: OPTIONS.weather,    selected: [weather],  onClick: setWeather },
      ].map(({ label, items, selected, onClick }) => (
        <div key={label} style={{ marginBottom: "1.5rem" }}>
          <p style={{ fontWeight: "500", fontSize: "14px", marginBottom: "10px" }}>{label}</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {items.map((item) => (
              <OptionBtn key={item} label={item} selected={selected.includes(item)} onClick={() => onClick(item)} />
            ))}
          </div>
        </div>
      ))}

      {error && (
        <div style={{ color: "#e74c3c", fontSize: "14px", marginBottom: "1rem", padding: "8px", background: "#ffeaea", borderRadius: "4px" }}>
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          width: "100%", padding: "14px", borderRadius: "8px", border: "none",
          background: loading ? "#aaa" : "#378ADD", color: "white", fontSize: "15px", fontWeight: "500", cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "추천 생성 중..." : "추천 경로 생성하기"}
      </button>
    </div>
  );
}

export default SurveyPage;