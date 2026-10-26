"""
unit_service.py - 단위 변환 모듈
길이, 넓이, 무게, 부피, 온도, 데이터, 속도, 압력, 시간 등 폭넓은 단위 지원
"""

class UnitService:
    def __init__(self):
        # 단위 카테고리별 정의
        # base_ratio: 기준 단위 1개 대비 크기 (예: 기준단위가 m일 때 km는 1000)
        self.categories = {
            "길이 (Length)": {
                "base": "m",
                "units": {
                    "mm (밀리미터)": 0.001,
                    "cm (센티미터)": 0.01,
                    "m (미터)": 1.0,
                    "km (킬로미터)": 1000.0,
                    "in (인치)": 0.0254,
                    "ft (피트)": 0.3048,
                    "yd (야드)": 0.9144,
                    "mi (마일)": 1609.344,
                    "해리 (Nautical Mile)": 1852.0,
                    "자/척 (尺)": 0.3030303,
                    "간 (間)": 1.8181818,
                    "정 (町)": 109.090909,
                    "리 (里)": 392.727272,
                }
            },
            "넓이 (Area)": {
                "base": "m²",
                "units": {
                    "m² (제곱미터)": 1.0,
                    "km² (제곱킬로미터)": 1000000.0,
                    "a (아르)": 100.0,
                    "ha (헥타르)": 10000.0,
                    "ft² (제곱피트)": 0.092903,
                    "yd² (제곱야드)": 0.836127,
                    "ac (에이커)": 4046.856422,
                    "평 (坪)": 3.305785,
                    "단보 (反)": 991.7355,
                    "정보 (町)": 9917.355,
                }
            },
            "무게 (Weight/Mass)": {
                "base": "g",
                "units": {
                    "mg (밀리그램)": 0.001,
                    "g (그램)": 1.0,
                    "kg (킬로그램)": 1000.0,
                    "t (톤)": 1000000.0,
                    "oz (온스)": 28.349523,
                    "lb (파운드)": 453.59237,
                    "돈 (금 1돈)": 3.75,
                    "냥 (37.5g)": 37.5,
                    "근 (고기/채소 600g)": 600.0,
                    "관 (3.75kg)": 3750.0,
                }
            },
            "부피 (Volume)": {
                "base": "L",
                "units": {
                    "mL / cc (밀리리터)": 0.001,
                    "L (리터)": 1.0,
                    "m³ (세제곱미터)": 1000.0,
                    "fl oz (액량 온스)": 0.0295735,
                    "cup (미국 컵)": 0.236588,
                    "pt (미국 파인트)": 0.473176,
                    "qt (미국 쿼트)": 0.946353,
                    "gal (미국 갤런)": 3.78541,
                    "홉 (0.18L)": 0.18039,
                    "되 (1.8L)": 1.8039,
                    "말 (18L)": 18.039,
                }
            },
            "온도 (Temperature)": {
                "special": "temperature",
                "units": [
                    "°C (섭씨)",
                    "°F (화씨)",
                    "K (켈빈)"
                ]
            },
            "데이터 (Data Storage)": {
                "base": "Byte",
                "units": {
                    "bit (비트)": 0.125,
                    "B (바이트)": 1.0,
                    "KB (킬로바이트)": 1024.0,
                    "MB (메가바이트)": 1024.0 ** 2,
                    "GB (기가바이트)": 1024.0 ** 3,
                    "TB (테라바이트)": 1024.0 ** 4,
                    "PB (페타바이트)": 1024.0 ** 5,
                }
            },
            "속도 (Speed)": {
                "base": "m/s",
                "units": {
                    "m/s (미터 매 초)": 1.0,
                    "km/h (킬로미터 매 시)": 1 / 3.6,
                    "mph (마일 매 시)": 0.44704,
                    "knot (노트)": 0.514444,
                    "ft/s (피트 매 초)": 0.3048,
                    "Mach (마하)": 340.29,
                }
            },
            "압력 (Pressure)": {
                "base": "Pa",
                "units": {
                    "Pa (파스칼)": 1.0,
                    "hPa (헥토파스칼)": 100.0,
                    "kPa (킬로파스칼)": 1000.0,
                    "bar (바)": 100000.0,
                    "psi (파운드/제곱인치)": 6894.757,
                    "atm (표준 기압)": 101325.0,
                    "mmHg / Torr": 133.322,
                }
            },
            "시간 (Time)": {
                "base": "s",
                "units": {
                    "ms (밀리초)": 0.001,
                    "s (초)": 1.0,
                    "min (분)": 60.0,
                    "h (시간)": 3600.0,
                    "d (일)": 86400.0,
                    "wk (주)": 604800.0,
                    "yr (년 - 365일)": 31536000.0,
                }
            }
        }

    def get_categories(self):
        return list(self.categories.keys())

    def get_units(self, category_name):
        cat = self.categories.get(category_name, {})
        if "units" in cat:
            if isinstance(cat["units"], dict):
                return list(cat["units"].keys())
            return cat["units"]
        return []

    def convert(self, category_name: str, value: float, from_unit: str, to_unit: str) -> float:
        """단위 변환 수행"""
        if from_unit == to_unit:
            return value

        cat = self.categories.get(category_name)
        if not cat:
            return value

        # 특수 처리: 온도
        if cat.get("special") == "temperature":
            return self._convert_temperature(value, from_unit, to_unit)

        # 일반 비례 단위
        unit_dict = cat.get("units", {})
        if from_unit not in unit_dict or to_unit not in unit_dict:
            return value

        from_ratio = unit_dict[from_unit]
        to_ratio = unit_dict[to_unit]

        # 기준 단위로 환산 후 목표 단위로 환산
        base_val = value * from_ratio
        result = base_val / to_ratio
        return result

    def _convert_temperature(self, val: float, from_u: str, to_u: str) -> float:
        # 먼저 Celsius(°C)로 변환
        if "°C" in from_u:
            celsius = val
        elif "°F" in from_u:
            celsius = (val - 32.0) * 5.0 / 9.0
        elif "K" in from_u:
            celsius = val - 273.15
        else:
            celsius = val

        # Celsius에서 목표 단위로 변환
        if "°C" in to_u:
            return celsius
        elif "°F" in to_u:
            return (celsius * 9.0 / 5.0) + 32.0
        elif "K" in to_u:
            return celsius + 273.15
        return celsius

    def convert_all(self, category_name: str, value: float, from_unit: str):
        """선택한 단위를 기준으로 해당 카테고리의 모든 단위 변환 결과를 딕셔너리로 반환"""
        units = self.get_units(category_name)
        results = {}
        for u in units:
            results[u] = self.convert(category_name, value, from_unit, u)
        return results


unit_service = UnitService()
