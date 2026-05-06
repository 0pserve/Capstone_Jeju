"""
기상청(KMA) 격자 좌표 변환 유틸리티 모듈.

위경도(WGS84)를 기상청 단기예보 API에서 사용하는 격자 좌표(nx, ny)로 변환합니다.
Lambert Conformal Conic 투영법을 사용하며, 기상청 공식 상수를 적용합니다.

기상청 공식 변환 알고리즘을 따릅니다.
참고: https://www.kma.go.kr/weather/forecast/digital_forecast.jsp
"""

import math


# 기상청 공식 상수
EARTH_RADIUS = 6371.00877  # 지구 반경 (km)
GRID_SPACING = 5.0         # 격자 간격 (km)
STANDARD_LAT1 = 30.0       # 표준 위도 1 (도)
STANDARD_LAT2 = 60.0       # 표준 위도 2 (도)
ORIGIN_LON = 126.0         # 기준점 경도 (도)
ORIGIN_LAT = 38.0          # 기준점 위도 (도)
X_OFFSET = 210 / GRID_SPACING  # 격자 오프셋 X (42)
Y_OFFSET = 675 / GRID_SPACING  # 격자 오프셋 Y (135)


def deg_to_rad(deg: float) -> float:
    """도(degree)를 라디안(radian)으로 변환."""
    return deg * math.pi / 180.0


def rad_to_deg(rad: float) -> float:
    """라디안을 도로 변환."""
    return rad * 180.0 / math.pi


def convert_to_grid(lat: float, lon: float) -> tuple[int, int]:
    """
    위경도를 기상청 격자 좌표(nx, ny)로 변환.

    Parameters
    ----------
    lat : float
        위도 (도, WGS84). 북위는 양수.
    lon : float
        경도 (도, WGS84). 동경은 양수.

    Returns
    -------
    tuple[int, int]
        정수형 격자 좌표 (nx, ny).

    Notes
    -----
    기상청 단기예보 API는 Lambert Conformal Conic 투영법을 사용합니다.
    변환 공식은 기상청 공식 문서를 따릅니다.
    """
    # 상수 정의
    RE = EARTH_RADIUS
    GRID = GRID_SPACING
    SLAT1 = STANDARD_LAT1
    SLAT2 = STANDARD_LAT2
    OLON = ORIGIN_LON
    OLAT = ORIGIN_LAT
    XO = X_OFFSET
    YO = Y_OFFSET

    DEGRAD = math.pi / 180.0  # 도→라디안 변환 계수

    # 격자 단위로 스케일링된 지구 반경
    re = RE / GRID

    # 라디안 변환
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    # 투영 파라미터 계산 (기상청 공식)
    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)

    # 대상점 계산
    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * DEGRAD - olon
    # 경도 차이를 [-π, π] 범위로 조정
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    # 격자 좌표 계산
    x = ra * math.sin(theta) + XO
    y = ro - ra * math.cos(theta) + YO

    # 정수로 변환 (기상청은 1‑based 인덱스이므로 0.5 더한 후 버림)
    nx = int(x + 1.5)
    ny = int(y + 1.5)

    return nx, ny


def convert_to_latlon(nx: int, ny: int) -> tuple[float, float]:
    """
    격자 좌표를 위경도로 역변환 (향후 확장용).

    Parameters
    ----------
    nx : int
        격자 x 좌표.
    ny : int
        격자 y 좌표.

    Returns
    -------
    tuple[float, float]
        위도, 경도 (도).

    Notes
    -----
    현재는 구현되지 않았으나, 구조상 미리 함수를 정의해 둡니다.
    """
    raise NotImplementedError("격자→위경도 역변환은 아직 구현되지 않았습니다.")


if __name__ == "__main__":
    """모듈 테스트 및 검증 코드."""
    # 테스트 케이스: 제주도청 좌표 (33.4890, 126.4983)
    jeju_lat = 33.4890
    jeju_lon = 126.4983

    nx, ny = convert_to_grid(jeju_lat, jeju_lon)
    print(f"[TEST] Jeju City Hall ({jeju_lat}, {jeju_lon}) -> grid (nx={nx}, ny={ny})")

    # 기상청 기준 예상값 근처인지 확인 (nx=52, ny=38 부근)
    expected_nx, expected_ny = 52, 38
    diff = abs(nx - expected_nx) + abs(ny - expected_ny)
    if diff <= 2:
        print(f"[OK] Within expected range (diff {diff}).")
    else:
        print(f"[WARN] Outside expected range (diff {diff}).")

    # 추가 테스트: 서울 (37.5665, 126.9780)
    seoul_lat, seoul_lon = 37.5665, 126.9780
    nx2, ny2 = convert_to_grid(seoul_lat, seoul_lon)
    print(f"[TEST] Seoul ({seoul_lat}, {seoul_lon}) -> grid (nx={nx2}, ny={ny2})")

    # 부산 (35.1796, 129.0756)
    busan_lat, busan_lon = 35.1796, 129.0756
    nx3, ny3 = convert_to_grid(busan_lat, busan_lon)
    print(f"[TEST] Busan ({busan_lat}, {busan_lon}) -> grid (nx={nx3}, ny={ny3})")

    # 기준점 자체 변환 (38.0, 126.0) -> nx=42?, ny=135?
    base_nx, base_ny = convert_to_grid(ORIGIN_LAT, ORIGIN_LON)
    print(f"[TEST] Origin point ({ORIGIN_LAT}, {ORIGIN_LON}) -> grid (nx={base_nx}, ny={base_ny})")
    print(f"       Expected offset: XO={X_OFFSET}, YO={Y_OFFSET}")