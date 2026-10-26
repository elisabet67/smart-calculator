"""
currency_service.py - 실시간 환율 조회 및 환율 변환 모듈
"""

import json
import os
import time
import urllib.request
from datetime import datetime

# 주요 통화 정보 (코드, 한국어 명칭, 기호, 국기 이모지)
CURRENCIES = {
    "KRW": {"name": "대한민국 원", "symbol": "₩", "flag": "🇰🇷", "base_unit": 1},
    "USD": {"name": "미국 달러", "symbol": "$", "flag": "🇺🇸", "base_unit": 1},
    "JPY": {"name": "일본 엔 (100엔)", "symbol": "¥", "flag": "🇯🇵", "base_unit": 100},
    "EUR": {"name": "유럽연합 유로", "symbol": "€", "flag": "🇪🇺", "base_unit": 1},
    "CNY": {"name": "중국 위안", "symbol": "¥", "flag": "🇨🇳", "base_unit": 1},
    "GBP": {"name": "영국 파운드", "symbol": "£", "flag": "🇬🇧", "base_unit": 1},
    "AUD": {"name": "호주 달러", "symbol": "A$", "flag": "🇦🇺", "base_unit": 1},
    "CAD": {"name": "캐나다 달러", "symbol": "C$", "flag": "🇨🇦", "base_unit": 1},
    "CHF": {"name": "스위스 프랑", "symbol": "CHF", "flag": "🇨🇭", "base_unit": 1},
    "HKD": {"name": "홍콩 달러", "symbol": "HK$", "flag": "🇭🇰", "base_unit": 1},
    "SGD": {"name": "싱가포르 달러", "symbol": "S$", "flag": "🇸🇬", "base_unit": 1},
    "TWD": {"name": "대만 달러", "symbol": "NT$", "flag": "🇹🇼", "base_unit": 1},
    "THB": {"name": "태국 바트", "symbol": "฿", "flag": "🇹🇭", "base_unit": 1},
    "VND": {"name": "베트남 동 (100동)", "symbol": "₫", "flag": "🇻🇳", "base_unit": 100},
    "PHP": {"name": "필리핀 페소", "symbol": "₱", "flag": "🇵🇭", "base_unit": 1},
    "INR": {"name": "인도 루피", "symbol": "₹", "flag": "🇮🇳", "base_unit": 1},
    "MYR": {"name": "말레이시아 링깃", "symbol": "RM", "flag": "🇲🇾", "base_unit": 1},
    "IDR": {"name": "인도네시아 루피아 (100루피아)", "symbol": "Rp", "flag": "🇮🇩", "base_unit": 100},
    "NZD": {"name": "뉴질랜드 달러", "symbol": "NZ$", "flag": "🇳🇿", "base_unit": 1},
    "BRL": {"name": "브라질 헤알", "symbol": "R$", "flag": "🇧🇷", "base_unit": 1},
    "MXN": {"name": "멕시코 페소", "symbol": "Mex$", "flag": "🇲🇽", "base_unit": 1},
    "TRY": {"name": "튀르키예 리라", "symbol": "₺", "flag": "🇹🇷", "base_unit": 1},
    "AED": {"name": "UAE 디르함", "symbol": "AED", "flag": "🇦🇪", "base_unit": 1},
    "SAR": {"name": "사우디 리얄", "symbol": "SAR", "flag": "🇸🇦", "base_unit": 1},
}

# 네트워크 오프라인 시 사용할 기본 백업 환율 (USD 기준 1 USD =)
DEFAULT_RATES = {
    "USD": 1.0,
    "KRW": 1320.0,
    "JPY": 152.5,
    "EUR": 0.92,
    "CNY": 7.23,
    "GBP": 0.77,
    "AUD": 1.51,
    "CAD": 1.38,
    "CHF": 0.86,
    "HKD": 7.77,
    "SGD": 1.32,
    "TWD": 32.1,
    "THB": 33.7,
    "VND": 25350.0,
    "PHP": 57.8,
    "INR": 84.1,
    "MYR": 4.34,
    "IDR": 15600.0,
    "NZD": 1.67,
    "BRL": 5.70,
    "MXN": 19.8,
    "TRY": 34.3,
    "AED": 3.67,
    "SAR": 3.75,
}

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exchange_rates_cache.json")


class CurrencyService:
    def __init__(self):
        self.rates = dict(DEFAULT_RATES)
        self.last_update_time = None
        self.is_live = False
        self.load_cache()

    def load_cache(self):
        """저장된 캐시 파일 로드"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rates.update(data.get("rates", {}))
                    self.last_update_time = data.get("timestamp")
                    self.is_live = True
            except Exception:
                pass

    def save_cache(self):
        """환율 데이터 캐시 저장"""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "rates": self.rates,
                    "timestamp": self.last_update_time
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def fetch_latest_rates(self):
        """무료 실시간 환율 API 호출 (USD 기준)"""
        url = "https://open.er-api.com/v6/latest/USD"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    if data.get("result") == "success":
                        new_rates = data.get("rates", {})
                        for code in CURRENCIES:
                            if code in new_rates:
                                self.rates[code] = float(new_rates[code])
                        self.last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.is_live = True
                        self.save_cache()
                        return True, "실시간 환율 업데이트 완료"
        except Exception as e:
            pass

        # 대체 API 시도 (exchangerate-api)
        backup_url = "https://api.exchangerate-api.com/v4/latest/USD"
        try:
            req = urllib.request.Request(
                backup_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    new_rates = data.get("rates", {})
                    for code in CURRENCIES:
                        if code in new_rates:
                            self.rates[code] = float(new_rates[code])
                    self.last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.is_live = True
                    self.save_cache()
                    return True, "실시간 환율 업데이트 완료 (대체 서버)"
        except Exception as e:
            return False, f"오프라인 모드 (저장된 환율 사용)"

    def convert(self, amount: float, from_curr: str, to_curr: str) -> float:
        """환율 계산: from_curr -> to_curr"""
        if from_curr == to_curr:
            return amount
        if from_curr not in self.rates or to_curr not in self.rates:
            return 0.0

        # USD 기준 환율을 경유하여 계산
        rate_from = self.rates[from_curr]  # 1 USD = rate_from FROM
        rate_to = self.rates[to_curr]      # 1 USD = rate_to TO

        # from -> USD -> to
        amount_in_usd = amount / rate_from
        return amount_in_usd * rate_to

    def get_krw_rate_table(self):
        """대한민국 원(KRW) 기준 1단위당 원화 환율 목록 반환"""
        krw_usd = self.rates.get("KRW", 1320.0)
        table = []
        for code, info in CURRENCIES.items():
            if code == "KRW":
                continue
            base_unit = info.get("base_unit", 1)
            usd_rate = self.rates.get(code, 1.0)
            if usd_rate > 0:
                # 1 단위 통화 = (krw_usd / usd_rate) KRW
                # base_unit 이 100인 경우(예: JPY, VND): base_unit 단위 통화의 KRW 환율
                krw_val = (krw_usd / usd_rate) * base_unit
                table.append({
                    "code": code,
                    "name": info["name"],
                    "flag": info["flag"],
                    "symbol": info["symbol"],
                    "base_unit": base_unit,
                    "krw_value": krw_val,
                    "unit_text": f"{base_unit} {code}" if base_unit != 1 else f"1 {code}"
                })
        return table


# 싱글톤 인스턴스
currency_service = CurrencyService()
