"""
calculator_core.py - 전자계산기 수식 파싱 및 계산 코어 엔진
"""

import math
import re

class CalculatorCore:
    def __init__(self):
        self.history = []

    def clean_expression(self, expr: str) -> str:
        """사용자 입력 수식을 파이썬 eval 가능한 안전한 수식으로 정규화"""
        expr = expr.strip()
        # 특수 기호 변환
        expr = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
        expr = expr.replace("π", f"({math.pi})").replace("e", f"({math.e})")
        # 거듭제곱 ^ -> **
        expr = expr.replace("^", "**")
        return expr

    def evaluate(self, expr: str):
        """
        수식을 평가하여 결과값을 문자열로 반환
        성공 시 (True, 결과문자열), 실패 시 (False, 오류메시지)
        """
        if not expr or not expr.strip():
            return False, "입력 없음"

        cleaned = self.clean_expression(expr)

        # 허용된 함수 및 상수 딕셔너리
        safe_env = {
            "sin": lambda x: math.sin(math.radians(x)),  # 각도(degree) 기준
            "cos": lambda x: math.cos(math.radians(x)),
            "tan": lambda x: math.tan(math.radians(x)),
            "asin": lambda x: math.degrees(math.asin(x)),
            "acos": lambda x: math.degrees(math.acos(x)),
            "atan": lambda x: math.degrees(math.atan(x)),
            "sqrt": math.sqrt,
            "log": math.log10,
            "ln": math.log,
            "abs": abs,
            "pi": math.pi,
            "e": math.e,
        }

        # 정규식 검증: 허용된 문자, 연산자, 식별자만 포함되었는지 검사
        # 허용: 숫자, +, -, *, /, %, (, ), ., **, 쉼표, 영문자(위 함수명)
        pattern = r"^[0-9\+\-\*\/\%\(\)\.\s\,\^a-zA-Z_]+$"
        if not re.match(pattern, cleaned):
            return False, "잘못된 문자가 포함되어 있습니다"

        # 함수명 화이트리스트 검사
        words = re.findall(r"[a-zA-Z_]+", cleaned)
        for w in words:
            if w not in safe_env:
                return False, f"지원되지 않는 연산/함수: {w}"

        try:
            # 안전한 환경에서 eval 실행
            result = eval(cleaned, {"__builtins__": None}, safe_env)

            # 복소수 방지
            if isinstance(result, complex):
                return False, "허수 결과는 지원하지 않습니다"

            # 부동소수점 오차 정밀 다듬기
            if isinstance(result, float):
                # 정수형으로 정확히 떨어지는 경우
                if result.is_integer() and abs(result) < 1e14:
                    formatted = str(int(result))
                else:
                    # 유효숫자 12자리 반올림
                    rounded = round(result, 10)
                    if rounded.is_integer() and abs(rounded) < 1e14:
                        formatted = str(int(rounded))
                    else:
                        # 소수점 끝 0 제거
                        formatted = f"{rounded:.10f}".rstrip("0").rstrip(".")
            else:
                formatted = str(result)

            # 계산 기록 추가
            record = {
                "expr": expr,
                "result": formatted
            }
            self.history.append(record)
            if len(self.history) > 100:
                self.history.pop(0)

            return True, formatted

        except ZeroDivisionError:
            return False, "0으로 나눌 수 없습니다"
        except OverflowError:
            return False, "오버플로 (수가 너무 큽니다)"
        except ValueError as e:
            return False, "연산 오류 (예: 음수의 제곱근)"
        except SyntaxError:
            return False, "수식 문법 오류"
        except Exception as e:
            return False, f"오류: {str(e)}"

    def get_history(self):
        return list(reversed(self.history))

    def clear_history(self):
        self.history.clear()


calculator_core = CalculatorCore()
