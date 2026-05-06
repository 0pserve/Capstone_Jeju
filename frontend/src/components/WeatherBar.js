import { useEffect, useState } from "react";
import axios from "axios";

function WeatherBar() {
  const [weather, setWeather] = useState(null);

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        // 제주도 격자 좌표 (nx: 53, ny: 38)
        const today = new Date();
        const base_date = today.toISOString().slice(0, 10).replace(/-/g, "");
        const base_time = "0500"; // 기상청은 정해진 시간에만 발표해요

        const res = await axios.get(
          "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst",
          {
            params: {
              serviceKey: process.env.REACT_APP_WEATHER_KEY,
              pageNo: 1,
              numOfRows: 100,
              dataType: "JSON",
              base_date,
              base_time,
              nx: 53,
              ny: 38,
            },
          }
        );

        const items = res.data.response.body.items.item;

        // 기온(T1H), 강수형태(PTY), 풍속(WSD) 추출
        const tmp  = items.find((i) => i.category === "TMP")?.fcstValue  + "°C";
        const pty  = items.find((i) => i.category === "PTY")?.fcstValue;
        const wsd  = items.find((i) => i.category === "WSD")?.fcstValue  + "m/s";

        // 강수형태 숫자를 텍스트로 변환
        const ptyText = { "0": "맑음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기" }[pty] || "맑음";

        setWeather({ tmp, ptyText, wsd });
      } catch (err) {
        console.error("날씨 불러오기 실패:", err);
      }
    };

    fetchWeather();
  }, []);

  return (
    <div>
      <div style={{ background: "#E6F1FB", padding: "8px 24px", fontSize: "13px", display: "flex", gap: "20px", color: "#0C447C" }}>
        {weather ? (
          <>
            <span>제주시 {weather.ptyText} {weather.tmp}</span>
            <span>풍속 {weather.wsd}</span>
            <span>미세먼지 좋음</span>
          </>
        ) : (
          <span>날씨 불러오는 중...</span>
        )}
      </div>
      <div style={{ background: "#FAEEDA", padding: "6px 24px", fontSize: "12px", color: "#633806" }}>
        오후 3시 이후 강풍 예보 — 실외 일정 자동 조정됨
      </div>
    </div>
  );
}

export default WeatherBar;