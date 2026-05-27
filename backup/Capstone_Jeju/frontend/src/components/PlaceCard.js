// 장소 카드 하나 — MapPage에서 여러 번 재사용돼요
function PlaceCard({ number, name, time, duration, type }) {
  const tagStyle = {
    실외: { background: "#EAF3DE", color: "#27500A" },
    실내: { background: "#E6F1FB", color: "#0C447C" },
    맛집: { background: "#FAEEDA", color: "#633806" },
  };

  return (
    <div style={{ padding: "12px 16px", borderBottom: "0.5px solid #eee" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span style={{
          width: "22px", height: "22px", borderRadius: "50%",
          background: "#378ADD", color: "white",
          fontSize: "11px", textAlign: "center", lineHeight: "22px", flexShrink: 0,
        }}>
          {number}
        </span>
        <span style={{ fontSize: "14px", fontWeight: "500" }}>{name}</span>
      </div>
      <div style={{ paddingLeft: "30px", marginTop: "4px", fontSize: "12px", color: "#888", display: "flex", alignItems: "center", gap: "6px" }}>
        <span>{time} · {duration}</span>
        <span style={{ padding: "2px 8px", borderRadius: "10px", fontSize: "11px", ...tagStyle[type] }}>
          {type}
        </span>
      </div>
    </div>
  );
}

export default PlaceCard;