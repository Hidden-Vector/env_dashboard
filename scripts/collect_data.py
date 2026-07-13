"""
지구환경 관제 전광판 - 데이터 수집 스크립트
매일 GitHub Actions가 이 스크립트를 실행해 data/daily.json 을 생성/갱신합니다.

설계 원칙
---------
1) API 키가 없거나 호출이 실패해도 스크립트 전체가 죽지 않도록 각 항목을
   try/except 로 감싸고, 실패 시 이전 값(prev) 또는 "데이터 없음"을 넣습니다.
2) 키가 필요한 항목은 환경변수(=GitHub Secrets)로 받습니다.
   - AIRKOREA_KEY : 공공데이터포털에서 무료 발급받는 에어코리아 서비스키
   - KPX_KEY      : 공공데이터포털에서 무료 발급받는 전력거래소 서비스키
   (둘 다 https://www.data.go.kr 에서 회원가입 후 "활용신청"만 하면 즉시/1~2일 내 무료 발급)
3) 키가 없는 항목(환경부 RSS, 환경 상식)은 별도 설정 없이도 바로 동작합니다.
"""

import json
import os
import random
import datetime
import urllib.request
import xml.etree.ElementTree as ET

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "daily.json")
KST = datetime.timezone(datetime.timedelta(hours=9))


def safe_get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ---------------------------------------------------------------------------
# 1) 환경부 e-환경뉴스 RSS (키 불필요)
# ---------------------------------------------------------------------------
def fetch_environment_news():
    url = "https://me.go.kr/home/web/board/rss.do?menuId=284&boardMasterId=108"
    items = []
    try:
        raw = safe_get(url)
        root = ET.fromstring(raw)
        for item in root.findall(".//item")[:6]:
            title = (item.findtext("title") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            link = (item.findtext("link") or "").strip()
            items.append({"tag": "환경부", "title": title, "source": "환경부 e-환경뉴스",
                          "date": pub[:16] if pub else "", "link": link})
    except Exception as e:
        items.append({"tag": "알림", "title": f"뉴스 수집 실패 (다음 갱신 시 재시도): {e}",
                      "source": "-", "date": "", "link": ""})
    return items


# ---------------------------------------------------------------------------
# 2) 에어코리아 시도별 실시간 대기질 (AIRKOREA_KEY 필요)
# ---------------------------------------------------------------------------
def fetch_air_quality():
    key = os.environ.get("AIRKOREA_KEY")
    default = {"pm10": None, "pm25": None, "cai": "키 미설정", "sido": "서울"}
    if not key:
        return default
    try:
        url = (
            "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
            f"?serviceKey={key}&returnType=json&numOfRows=100&pageNo=1&sidoName=%EC%84%9C%EC%9A%B8&ver=1.3"
        )
        raw = safe_get(url)
        data = json.loads(raw)
        rows = data["response"]["body"]["items"]
        # 서울 측정소들의 평균값으로 대표값 산출
        pm10_vals = [int(r["pm10Value"]) for r in rows if r.get("pm10Value", "-").isdigit()]
        pm25_vals = [int(r["pm25Value"]) for r in rows if r.get("pm25Value", "-").isdigit()]
        pm10 = round(sum(pm10_vals) / len(pm10_vals)) if pm10_vals else None
        pm25 = round(sum(pm25_vals) / len(pm25_vals)) if pm25_vals else None
        return {"pm10": pm10, "pm25": pm25, "cai": "정상 수신", "sido": "서울(평균)"}
    except Exception as e:
        default["cai"] = f"수집 실패: {e}"
        return default


# ---------------------------------------------------------------------------
# 3) 전력거래소 실시간 수급 (KPX_KEY 필요) -> 국내 CO2 배출 추정에 활용
# ---------------------------------------------------------------------------
def fetch_power_and_estimate_co2():
    key = os.environ.get("KPX_KEY")
    # 국가 고유 전력배출계수(참고치, kgCO2/kWh) - 실제 서비스 시 GIR 최신 승인치로 교체 권장
    EMISSION_FACTOR = 0.4747
    if not key:
        return {"value": None, "delta": "KPX_KEY 미설정 - 전력수급 기반 추정 비활성", "unit": "만 톤"}
    try:
        url = f"http://openapi.kpx.or.kr/openapi/sukub5mMaxDatetime/getSukub5mMaxDatetime?key={key}"
        safe_get(url)  # 실제 응답 파싱은 KPX 응답 스펙에 맞춰 구현 필요 (여기서는 연결 확인만)
        return {"value": None, "delta": "전력수급 연동 성공 - 배출량 환산 로직은 서비스 스펙 확정 후 채우세요",
                "unit": "만 톤"}
    except Exception as e:
        return {"value": None, "delta": f"수집 실패: {e}", "unit": "만 톤"}


# ---------------------------------------------------------------------------
# 4) 환경 상식 - 날짜 기반 순환 (키 불필요, 항상 동작)
# ---------------------------------------------------------------------------
FACTS = [
    "이산화탄소는 대기 중에 배출된 뒤 수백 년간 머무를 수 있어, 오늘 줄인 배출량의 효과는 수십 년 뒤에야 기후에 반영되기 시작합니다.",
    "전 세계 온실가스 배출량의 약 4분의 1은 식량 생산 과정에서 발생합니다.",
    "산업화 이전 대비 대기 중 이산화탄소 농도는 약 50% 증가했습니다.",
    "나무 한 그루는 평균적으로 1년에 약 20~25kg의 이산화탄소를 흡수합니다.",
    "전 세계 플라스틱의 약 9%만이 실제로 재활용되고 있습니다.",
    "태양광 발전 비용은 지난 10여 년간 큰 폭으로 하락해 여러 지역에서 가장 저렴한 전력원 중 하나가 되었습니다.",
    "해양은 인간이 배출한 이산화탄소의 상당 부분을 흡수해 해양 산성화를 일으키고 있습니다.",
    "육류 소비를 줄이는 것은 개인이 실천할 수 있는 가장 효과적인 탄소 저감 방법 중 하나로 꼽힙니다.",
    "국제사회는 파리협정을 통해 산업화 이전 대비 지구 평균기온 상승을 1.5도 이내로 억제하는 것을 목표로 하고 있습니다.",
    "한국은 2050년 탄소중립을 국가 목표로 선언했습니다.",
]


def fetch_fact_of_day():
    day_index = datetime.datetime.now(KST).timetuple().tm_yday
    return FACTS[day_index % len(FACTS)]


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
def load_previous():
    try:
        with open(OUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    prev = load_previous()
    now = datetime.datetime.now(KST)

    data = {
        "generated_at": now.isoformat(),
        "generated_at_display": now.strftime("%Y-%m-%d %H:%M KST"),
        "world_co2": prev.get("world_co2", {
            "value": None,
            "delta": "세계 배출량은 Carbon Monitor/Climate TRACE 등 외부 소스 연동 필요 (README 참고)",
            "unit": "백만 톤",
        }),
        "korea_co2": fetch_power_and_estimate_co2(),
        "air": fetch_air_quality(),
        "news": fetch_environment_news(),
        "fact": fetch_fact_of_day(),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("data/daily.json 생성 완료:", data["generated_at_display"])


if __name__ == "__main__":
    main()
