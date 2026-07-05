# -*- coding: utf-8 -*-
"""
국내 대회 정보 수집 스크립트
소스 1: roadrun.co.kr (마라톤·트레일러닝 종합 일정)
소스 2: triathlon.or.kr (대한철인3종협회 대회일정)
+ manual_events.json (수동 관리 목록: 자전거·수영 등 수집 밖 대회)
결과: data.json 갱신. 소스 하나가 실패해도 나머지는 유지된다.
"""
import json, re, sys, unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).date()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

TRAIL_KW = re.compile(r"트레일|TRAIL|트런|스카이레이스|스카이러닝|산악마라톤", re.I)
SKIP_KTF = re.compile(r"교육|세미나|강습회|승급|선발전|워크숍")


def norm_key(name):
    """대회명 정규화 → 중복 판정 키"""
    s = unicodedata.normalize("NFKC", name or "")
    s = re.sub(r"20\d{2}", "", s)
    s = re.sub(r"제?\s*\d+\s*회", "", s)
    s = re.sub(r"[\s\W_]+", "", s).lower()
    return s


def guess_year(month, day):
    """월/일만 있는 날짜의 연도 추정 (지난 달이면 내년으로)"""
    y = TODAY.year
    try:
        d = datetime(y, month, day).date()
    except ValueError:
        return None
    if d < TODAY - timedelta(days=21):
        y += 1
    return f"{y:04d}-{month:02d}-{day:02d}"


def fetch(url, encoding=None):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    if encoding:
        r.encoding = encoding
    return r.text


# ---------------- 소스 1: roadrun.co.kr ----------------
def scrape_roadrun():
    html = fetch("http://www.roadrun.co.kr/schedule/list.php", encoding="euc-kr")
    soup = BeautifulSoup(html, "html.parser")
    events, seen = [], set()
    for a in soup.find_all("a", href=re.compile(r"view\.php\?no=")):
        name = a.get_text(" ", strip=True)
        if not name or len(name) < 4:
            continue
        no = re.search(r"no=(\d+)", a.get("href", ""))
        if not no or no.group(1) in seen:
            continue
        # 날짜·정보가 포함된 조상 요소 탐색
        node, ok = a, None
        for _ in range(5):
            node = node.parent
            if node is None:
                break
            txt = node.get_text(" ", strip=True)
            if re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})\b", txt) and len(txt) > len(name) + 8:
                ok = node
                break
        if ok is None:
            continue
        seen.add(no.group(1))
        txt = ok.get_text(" ", strip=True)
        m = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})\b", txt)
        date = guess_year(int(m.group(1)), int(m.group(2))) if m else None
        # 홈페이지: roadrun 내부가 아닌 첫 외부 링크
        url = None
        for link in ok.find_all("a", href=True):
            h = link["href"]
            if h.startswith("http") and "roadrun" not in h and "javascript" not in h:
                url = h
                break
        # 코스 추출
        courses = ", ".join(dict.fromkeys(re.findall(r"(?:풀|하프|울트라|[0-9.]+\s?[kK][mM]?)\b", txt)))[:60] or None
        # 위치: 대회명 뒤 텍스트에서 전화번호 앞부분
        loc = None
        tail = txt.split(name, 1)[-1]
        tail = re.split(r"[☎☎]|0\d{1,2}[-)]", tail)[0]
        tail = re.sub(r"(?:풀|하프|울트라|[0-9.]+\s?[kK][mM]?)[,\s/]*", "", tail).strip(" ,/-")
        if tail:
            loc = tail[:40]
        events.append({
            "name": name, "cat": "trail" if TRAIL_KW.search(name + " " + txt) else "road",
            "date": date, "loc": loc or "홈페이지 참조", "courses": courses,
            "status": "확인필요", "reg": None, "url": url,
            "note": None, "src": "roadrun",
        })
    if len(events) < 5:
        raise RuntimeError(f"roadrun 파싱 결과가 비정상적으로 적음: {len(events)}")
    return events


# ---------------- 소스 2: triathlon.or.kr ----------------
def scrape_ktf():
    events = []
    for page in (1, 2):
        html = fetch(f"https://triathlon.or.kr/events/tour/?vType=list&sYear={TODAY.year}&page={page}")
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=re.compile(r"mode=overview&tourcd=")):
            name = a.get_text(" ", strip=True)
            row = a.find_parent("tr") or a.find_parent("li") or a.parent
            txt = row.get_text(" ", strip=True) if row else name
            title = re.split(r"장소\s*:", name)[0].strip() or name
            if SKIP_KTF.search(title):
                continue
            m = re.search(r"(20\d{2})\.(\d{1,2})\.(\d{1,2})", txt)
            date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else None
            status = "확인필요"
            for s in ("접수중", "접수예정", "접수마감"):
                if s in txt:
                    status = s
                    break
            lm = re.search(r"장소\s*:\s*(.+?)(?:코스\s*:|$)", txt)
            cm = re.search(r"코스\s*:\s*(.+?)(?:\d{4}\.|$)", txt)
            href = a["href"]
            url = href if href.startswith("http") else "https://triathlon.or.kr" + href
            title = re.sub(r"[\(\[][^\)\]]*(?:마감|접수|예정)[^\)\]]*[\)\]]", "", title).strip()
            events.append({
                "name": title, "cat": "triathlon", "date": date,
                "loc": (lm.group(1).strip()[:40] if lm else "홈페이지 참조"),
                "courses": (cm.group(1).strip()[:60] if cm else None),
                "status": status, "reg": None, "url": url, "note": None, "src": "ktf",
            })
    # tourcd 중복 제거 (최신 우선)
    uniq = {}
    for e in events:
        uniq.setdefault(norm_key(e["name"]) + (e["date"] or ""), e)
    events = list(uniq.values())
    if len(events) < 3:
        raise RuntimeError(f"triathlon.or.kr 파싱 결과가 비정상적으로 적음: {len(events)}")
    return events


# ---------------- 병합 ----------------
def is_past(e):
    d = e.get("date")
    if not d or len(d) < 10:
        return False
    try:
        return datetime.strptime(d, "%Y-%m-%d").date() < TODAY
    except ValueError:
        return False


def main():
    data_path = ROOT / "data.json"
    manual_path = ROOT / "manual_events.json"
    prev = json.loads(data_path.read_text(encoding="utf-8")) if data_path.exists() else {"events": []}
    manual = json.loads(manual_path.read_text(encoding="utf-8")) if manual_path.exists() else []

    log = {}
    scraped = []
    for label, fn in (("roadrun", scrape_roadrun), ("triathlon.or.kr", scrape_ktf)):
        try:
            got = fn()
            scraped += got
            log[label] = f"성공 ({len(got)}건)"
        except Exception as ex:
            log[label] = f"실패: {ex}"
            # 실패 시 이전 data.json에서 해당 소스 이벤트 유지
            src = "roadrun" if label == "roadrun" else "ktf"
            scraped += [e for e in prev.get("events", []) if e.get("src") == src]

    # 수동 목록을 기준으로 병합: 스크랩 결과가 같은 대회면 날짜·상태 갱신
    merged = {norm_key(e["name"]): dict(e) for e in manual}
    for s in scraped:
        k = norm_key(s["name"])
        if k in merged:
            m = merged[k]
            m["date"] = s["date"] or m.get("date")
            if s["status"] != "확인필요":
                m["status"] = s["status"]
            m["url"] = m.get("url") or s.get("url")
            m["src"] = s.get("src")
        else:
            merged[k] = s

    events = [e for e in merged.values() if not is_past(e)]
    events.sort(key=lambda e: e.get("date") or "9999")

    # 신규 접수 시작 감지: 이전 실행에서 접수중이 아니었다가 이번에 접수중이 된 대회
    prev_status = {norm_key(e.get("name", "")): e.get("status") for e in prev.get("events", [])}
    for e in events:
        was = prev_status.get(norm_key(e["name"]))
        e["justOpened"] = bool(e.get("status") == "접수중" and was is not None and was != "접수중")

    out = {
        "lastUpdated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "sourceLog": log,
        "events": events,
    }
    data_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"완료: {len(events)}건 저장 / {log}")


if __name__ == "__main__":
    sys.exit(main())
