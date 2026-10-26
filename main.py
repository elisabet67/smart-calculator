"""
main.py - 전자계산기 프로그램 (환율 보기 & 단위 변환 통합 GUI)
"""

import ctypes
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Windows High DPI 인식 설정 (글자 및 그래픽 선명도 개선)
try:
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

from calculator_core import calculator_core
from unit_service import unit_service
from currency_service import currency_service, CURRENCIES


class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("스마트 전자계산기 - 환율 & 단위변환")
        self.geometry("500x740")
        self.minsize(460, 680)

        # 다크 테마 색상 팔레트
        self.colors = {
            "bg": "#18181b",              # 메인 배경
            "card_bg": "#27272a",         # 카드/패널 배경
            "border": "#3f3f46",          # 테두리
            "text": "#f4f4f5",            # 메인 텍스트
            "subtext": "#a1a1aa",         # 보조 텍스트
            "accent": "#3b82f6",          # 주요 포인트 (블루)
            "accent_hover": "#2563eb",
            "btn_num": "#27272a",         # 숫자 버튼
            "btn_num_hover": "#3f3f46",
            "btn_op": "#3b82f6",          # 연산자 버튼
            "btn_op_hover": "#2563eb",
            "btn_func": "#3f3f46",        # 함수/보조 버튼
            "btn_func_hover": "#52525b",
            "btn_eq": "#10b981",          # 등호 버튼 (그린)
            "btn_eq_hover": "#059669",
            "btn_danger": "#ef4444",      # C/초기화 버튼 (레드)
            "btn_danger_hover": "#dc2626",
            "active_tab": "#3b82f6",
            "inactive_tab": "#27272a",
        }

        self.configure(bg=self.colors["bg"])

        # 계산기 상태 변수
        self.current_expr = ""
        self.last_result = ""
        self.should_reset_input = False

        # 스타일 설정
        self.setup_styles()

        # UI 레이아웃 구성
        self.create_header()
        self.create_tab_bar()

        # 각 모드별 프레임 컨테이너
        self.content_frame = tk.Frame(self, bg=self.colors["bg"])
        self.content_frame.pack(fill="both", expand=True, padx=14, pady=(6, 12))

        # 프레임들 생성
        self.calc_frame = tk.Frame(self.content_frame, bg=self.colors["bg"])
        self.unit_frame = tk.Frame(self.content_frame, bg=self.colors["bg"])
        self.exchange_frame = tk.Frame(self.content_frame, bg=self.colors["bg"])
        self.history_frame = tk.Frame(self.content_frame, bg=self.colors["bg"])

        # 각 탭 뷰 초기화
        self.build_calc_tab()
        self.build_unit_tab()
        self.build_exchange_tab()
        self.build_history_tab()

        # 키보드 이벤트 바인딩
        self.bind_all("<Key>", self.handle_keypress)

        # 기본 탭 열기
        self.switch_tab("calc")

        # 환율 백그라운드 로드
        self.refresh_rates_threaded()

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Combobox 스타일
        style.configure("TCombobox",
                        fieldbackground=self.colors["card_bg"],
                        background=self.colors["border"],
                        foreground=self.colors["text"],
                        arrowcolor=self.colors["text"],
                        darkcolor=self.colors["border"],
                        lightcolor=self.colors["border"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", self.colors["card_bg"])],
                  selectbackground=[("readonly", self.colors["accent"])],
                  selectforeground=[("readonly", "#ffffff")])

        # Treeview 스타일
        style.configure("Treeview",
                        background=self.colors["card_bg"],
                        foreground=self.colors["text"],
                        fieldbackground=self.colors["card_bg"],
                        rowheight=32,
                        font=("Malgun Gothic", 10))
        style.configure("Treeview.Heading",
                        background=self.colors["border"],
                        foreground=self.colors["text"],
                        font=("Malgun Gothic", 10, "bold"),
                        relief="flat")
        style.map("Treeview",
                  background=[("selected", self.colors["accent"])],
                  foreground=[("selected", "#ffffff")])

        # Scrollbar 스타일
        style.configure("Vertical.TScrollbar",
                        background=self.colors["border"],
                        troughcolor=self.colors["bg"],
                        arrowcolor=self.colors["text"])

    def create_header(self):
        header = tk.Frame(self, bg=self.colors["bg"], height=40)
        header.pack(fill="x", padx=16, pady=(12, 4))

        title_lbl = tk.Label(header, text="전자계산기", font=("Malgun Gothic", 14, "bold"),
                             fg=self.colors["text"], bg=self.colors["bg"])
        title_lbl.pack(side="left")

        subtitle = tk.Label(header, text="단위변환 · 실시간 환율", font=("Malgun Gothic", 10),
                            fg=self.colors["subtext"], bg=self.colors["bg"])
        subtitle.pack(side="left", padx=8, pady=(4, 0))

    def create_tab_bar(self):
        tab_bar = tk.Frame(self, bg=self.colors["bg"])
        tab_bar.pack(fill="x", padx=14, pady=6)

        self.tab_buttons = {}
        tabs = [
            ("calc", "🧮 계산기"),
            ("unit", "⚖️ 단위변환"),
            ("exchange", "💱 실시간 환율"),
            ("history", "📜 계산기록"),
        ]

        for tab_id, text in tabs:
            btn = tk.Button(
                tab_bar,
                text=text,
                font=("Malgun Gothic", 10, "bold"),
                fg=self.colors["subtext"],
                bg=self.colors["inactive_tab"],
                activebackground=self.colors["accent"],
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=12,
                pady=7,
                cursor="hand2",
                command=lambda t=tab_id: self.switch_tab(t)
            )
            btn.pack(side="left", expand=True, fill="x", padx=2)
            self.tab_buttons[tab_id] = btn

    def switch_tab(self, tab_id):
        self.active_tab = tab_id
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(bg=self.colors["active_tab"], fg="#ffffff")
            else:
                btn.configure(bg=self.colors["inactive_tab"], fg=self.colors["subtext"])

        # 프레임 전환
        for frame in (self.calc_frame, self.unit_frame, self.exchange_frame, self.history_frame):
            frame.pack_forget()

        if tab_id == "calc":
            self.calc_frame.pack(fill="both", expand=True)
        elif tab_id == "unit":
            self.unit_frame.pack(fill="both", expand=True)
            self.update_unit_conversion()
        elif tab_id == "exchange":
            self.exchange_frame.pack(fill="both", expand=True)
            self.update_exchange_conversion()
        elif tab_id == "history":
            self.history_frame.pack(fill="both", expand=True)
            self.refresh_history_table()

    # ==========================================================
    # 1. 계산기 탭 (CALCULATOR TAB)
    # ==========================================================
    def build_calc_tab(self):
        # 디스플레이 패널
        disp_card = tk.Frame(self.calc_frame, bg=self.colors["card_bg"],
                             highlightbackground=self.colors["border"], highlightthickness=1)
        disp_card.pack(fill="x", pady=(0, 10))

        # 지난 수식 / 상단 서브 라벨
        self.calc_expr_lbl = tk.Label(
            disp_card,
            text="",
            font=("Malgun Gothic", 12),
            fg=self.colors["subtext"],
            bg=self.colors["card_bg"],
            anchor="e",
            padx=16,
            pady=4
        )
        self.calc_expr_lbl.pack(fill="x", pady=(12, 0))

        # 현재 입력 / 결과 디스플레이
        self.calc_disp_lbl = tk.Label(
            disp_card,
            text="0",
            font=("Malgun Gothic", 28, "bold"),
            fg=self.colors["text"],
            bg=self.colors["card_bg"],
            anchor="e",
            padx=16,
            pady=4
        )
        self.calc_disp_lbl.pack(fill="x", pady=(0, 12))

        # 버튼 그리드 컨테이너
        btn_container = tk.Frame(self.calc_frame, bg=self.colors["bg"])
        btn_container.pack(fill="both", expand=True)

        for i in range(6):
            btn_container.rowconfigure(i, weight=1)
        for j in range(4):
            btn_container.columnconfigure(j, weight=1)

        # 공학 및 특수 기능 상단 행
        # 행 0: ( ) x² √
        # 행 1: C CE ⌫ ÷
        # 행 2: 7 8 9 ×
        # 행 3: 4 5 6 -
        # 행 4: 1 2 3 +
        # 행 5: ± 0 . =
        btn_layout = [
            [("(", "func"), (")", "func"), ("x²", "func"), ("√", "func")],
            [("C", "danger"), ("CE", "func"), ("⌫", "func"), ("÷", "op")],
            [("7", "num"), ("8", "num"), ("9", "num"), ("×", "op")],
            [("4", "num"), ("5", "num"), ("6", "num"), ("-", "op")],
            [("1", "num"), ("2", "num"), ("3", "num"), ("+", "op")],
            [("±", "func"), ("0", "num"), (".", "num"), ("=", "eq")],
        ]

        for r, row in enumerate(btn_layout):
            for c, (text, btype) in enumerate(row):
                self.create_calc_btn(btn_container, text, btype, r, c)

        # 하단 미니 공학/과학 함수 툴바 (토글식 확장)
        sci_bar = tk.Frame(self.calc_frame, bg=self.colors["bg"])
        sci_bar.pack(fill="x", pady=(6, 0))

        sci_funcs = [("sin", "sin("), ("cos", "cos("), ("tan", "tan("),
                     ("log", "log("), ("ln", "ln("), ("π", "π"), ("e", "e"), ("^", "^")]
        for label, val in sci_funcs:
            b = tk.Button(
                sci_bar,
                text=label,
                font=("Malgun Gothic", 9),
                fg=self.colors["subtext"],
                bg=self.colors["card_bg"],
                activebackground=self.colors["accent"],
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                pady=4,
                cursor="hand2",
                command=lambda v=val: self.append_calc_token(v)
            )
            b.pack(side="left", expand=True, fill="x", padx=1)

    def create_calc_btn(self, parent, text, btype, row, col):
        if btype == "num":
            bg = self.colors["btn_num"]
            active_bg = self.colors["btn_num_hover"]
            fg = self.colors["text"]
            font = ("Malgun Gothic", 15, "bold")
        elif btype == "op":
            bg = self.colors["btn_op"]
            active_bg = self.colors["btn_op_hover"]
            fg = "#ffffff"
            font = ("Malgun Gothic", 16, "bold")
        elif btype == "eq":
            bg = self.colors["btn_eq"]
            active_bg = self.colors["btn_eq_hover"]
            fg = "#ffffff"
            font = ("Malgun Gothic", 17, "bold")
        elif btype == "danger":
            bg = self.colors["btn_danger"]
            active_bg = self.colors["btn_danger_hover"]
            fg = "#ffffff"
            font = ("Malgun Gothic", 14, "bold")
        else:  # func
            bg = self.colors["btn_func"]
            active_bg = self.colors["btn_func_hover"]
            fg = self.colors["text"]
            font = ("Malgun Gothic", 13, "bold")

        btn = tk.Button(
            parent,
            text=text,
            font=font,
            fg=fg,
            bg=bg,
            activebackground=active_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda t=text: self.on_calc_btn_click(t)
        )
        btn.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)

        # 호버 효과
        btn.bind("<Enter>", lambda e, b=btn, c=active_bg: b.configure(bg=c))
        btn.bind("<Leave>", lambda e, b=btn, c=bg: b.configure(bg=c))

    def on_calc_btn_click(self, char):
        if char == "C":
            self.current_expr = ""
            self.calc_expr_lbl.configure(text="")
            self.calc_disp_lbl.configure(text="0")
            self.should_reset_input = False
        elif char == "CE":
            self.calc_disp_lbl.configure(text="0")
            self.current_expr = ""
        elif char == "⌫":
            if self.should_reset_input:
                self.current_expr = ""
                self.calc_disp_lbl.configure(text="0")
                self.should_reset_input = False
            else:
                self.current_expr = self.current_expr[:-1]
                self.calc_disp_lbl.configure(text=self.current_expr if self.current_expr else "0")
        elif char == "=":
            self.calculate_result()
        elif char == "±":
            if self.current_expr:
                if self.current_expr.startswith("-"):
                    self.current_expr = self.current_expr[1:]
                else:
                    self.current_expr = "-" + self.current_expr
                self.calc_disp_lbl.configure(text=self.current_expr)
        elif char == "x²":
            self.append_calc_token("^2")
        elif char == "√":
            self.append_calc_token("sqrt(")
        else:
            self.append_calc_token(char)

    def append_calc_token(self, token):
        if self.should_reset_input:
            if token in ["+", "-", "×", "÷", "^"]:
                # 이전 결과값에 이어서 연산
                self.current_expr = self.last_result + " " + token + " "
            else:
                self.current_expr = token
            self.should_reset_input = False
        else:
            if token in ["+", "-", "×", "÷", "^"]:
                self.current_expr += f" {token} "
            else:
                self.current_expr += token

        disp_text = self.current_expr.strip()
        if not disp_text:
            disp_text = "0"
        self.calc_disp_lbl.configure(text=disp_text)

    def calculate_result(self):
        if not self.current_expr.strip():
            return

        expr = self.current_expr
        success, result = calculator_core.evaluate(expr)

        if success:
            self.calc_expr_lbl.configure(text=f"{expr} =")
            self.calc_disp_lbl.configure(text=result)
            self.last_result = result
            self.current_expr = result
            self.should_reset_input = True
        else:
            self.calc_expr_lbl.configure(text=f"{expr} =")
            self.calc_disp_lbl.configure(text="오류: " + result)
            self.should_reset_input = True

    def handle_keypress(self, event):
        if self.active_tab != "calc":
            return

        char = event.char
        keysym = event.keysym

        if keysym in ("Return", "KP_Enter"):
            self.calculate_result()
        elif keysym == "BackSpace":
            self.on_calc_btn_click("⌫")
        elif keysym == "Escape":
            self.on_calc_btn_click("C")
        elif char in "0123456789.()":
            self.append_calc_token(char)
        elif char == "+":
            self.append_calc_token("+")
        elif char == "-":
            self.append_calc_token("-")
        elif char == "*":
            self.append_calc_token("×")
        elif char == "/":
            self.append_calc_token("÷")
        elif char == "^":
            self.append_calc_token("^")

    # ==========================================================
    # 2. 단위 변환 탭 (UNIT CONVERTER TAB)
    # ==========================================================
    def build_unit_tab(self):
        # 상단 카테고리 선택 영역
        cat_card = tk.Frame(self.unit_frame, bg=self.colors["card_bg"],
                            highlightbackground=self.colors["border"], highlightthickness=1)
        cat_card.pack(fill="x", pady=(0, 10), padx=2, ipady=6)

        cat_lbl = tk.Label(cat_card, text="변환 분류 선택", font=("Malgun Gothic", 10, "bold"),
                           fg=self.colors["subtext"], bg=self.colors["card_bg"])
        cat_lbl.pack(anchor="w", padx=12, pady=(4, 2))

        self.unit_cat_var = tk.StringVar()
        categories = unit_service.get_categories()
        self.unit_cat_cb = ttk.Combobox(
            cat_card,
            textvariable=self.unit_cat_var,
            values=categories,
            state="readonly",
            font=("Malgun Gothic", 11)
        )
        self.unit_cat_cb.pack(fill="x", padx=12, pady=(0, 6))
        self.unit_cat_cb.current(0)
        self.unit_cat_cb.bind("<<ComboboxSelected>>", self.on_unit_category_change)

        # 변환 입력 & 출력 카드
        conv_card = tk.Frame(self.unit_frame, bg=self.colors["card_bg"],
                             highlightbackground=self.colors["border"], highlightthickness=1)
        conv_card.pack(fill="x", pady=(0, 10), padx=2, ipady=8)

        # 입력 영역
        row1 = tk.Frame(conv_card, bg=self.colors["card_bg"])
        row1.pack(fill="x", padx=12, pady=(6, 4))

        tk.Label(row1, text="입력값", font=("Malgun Gothic", 10),
                 fg=self.colors["subtext"], bg=self.colors["card_bg"]).pack(side="left")

        self.unit_input_var = tk.StringVar(value="1")
        self.unit_input_entry = tk.Entry(
            row1,
            textvariable=self.unit_input_var,
            font=("Malgun Gothic", 13, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            justify="right"
        )
        self.unit_input_entry.pack(side="right", fill="x", expand=True, padx=(10, 0), ipady=3)
        self.unit_input_var.trace_add("write", lambda *args: self.update_unit_conversion())

        # 단위 선택 영역 (From ⇄ To)
        row2 = tk.Frame(conv_card, bg=self.colors["card_bg"])
        row2.pack(fill="x", padx=12, pady=6)

        self.unit_from_var = tk.StringVar()
        self.unit_to_var = tk.StringVar()

        self.unit_from_cb = ttk.Combobox(row2, textvariable=self.unit_from_var, state="readonly", font=("Malgun Gothic", 10), width=16)
        self.unit_from_cb.pack(side="left", fill="x", expand=True)
        self.unit_from_cb.bind("<<ComboboxSelected>>", lambda e: self.update_unit_conversion())

        swap_btn = tk.Button(
            row2,
            text="⇄",
            font=("Malgun Gothic", 13, "bold"),
            fg="#ffffff",
            bg=self.colors["border"],
            activebackground=self.colors["accent"],
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.swap_units
        )
        swap_btn.pack(side="left", padx=6)

        self.unit_to_cb = ttk.Combobox(row2, textvariable=self.unit_to_var, state="readonly", font=("Malgun Gothic", 10), width=16)
        self.unit_to_cb.pack(side="left", fill="x", expand=True)
        self.unit_to_cb.bind("<<ComboboxSelected>>", lambda e: self.update_unit_conversion())

        # 변환 결과 강조 표시
        self.unit_result_lbl = tk.Label(
            conv_card,
            text="= 0",
            font=("Malgun Gothic", 17, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["card_bg"],
            anchor="e",
            padx=12
        )
        self.unit_result_lbl.pack(fill="x", pady=(6, 2))

        # 하단: 해당 카테고리의 모든 단위 일괄 변환 표 (Treeview)
        list_lbl = tk.Label(self.unit_frame, text="모든 단위 일괄 변환 목록", font=("Malgun Gothic", 10, "bold"),
                            fg=self.colors["subtext"], bg=self.colors["bg"])
        list_lbl.pack(anchor="w", padx=4, pady=(2, 4))

        tree_container = tk.Frame(self.unit_frame, bg=self.colors["card_bg"],
                                  highlightbackground=self.colors["border"], highlightthickness=1)
        tree_container.pack(fill="both", expand=True, padx=2)

        self.unit_tree = ttk.Treeview(tree_container, columns=("unit", "value"), show="headings", height=8)
        self.unit_tree.heading("unit", text="단위")
        self.unit_tree.heading("value", text="환산값")
        self.unit_tree.column("unit", width=180, anchor="w")
        self.unit_tree.column("value", width=240, anchor="e")

        unit_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.unit_tree.yview)
        self.unit_tree.configure(yscrollcommand=unit_scroll.set)

        self.unit_tree.pack(side="left", fill="both", expand=True)
        unit_scroll.pack(side="right", fill="y")

        # 초기 단위 목록 로드
        self.on_unit_category_change()

    def on_unit_category_change(self, event=None):
        cat = self.unit_cat_var.get()
        units = unit_service.get_units(cat)
        self.unit_from_cb["values"] = units
        self.unit_to_cb["values"] = units

        if units:
            self.unit_from_cb.current(0)
            if len(units) > 1:
                self.unit_to_cb.current(1)
            else:
                self.unit_to_cb.current(0)

        self.update_unit_conversion()

    def swap_units(self):
        f = self.unit_from_var.get()
        t = self.unit_to_var.get()
        self.unit_from_var.set(t)
        self.unit_to_var.set(f)
        self.update_unit_conversion()

    def update_unit_conversion(self):
        cat = self.unit_cat_var.get()
        raw_val = self.unit_input_var.get().strip()
        from_u = self.unit_from_var.get()
        to_u = self.unit_to_var.get()

        if not raw_val or not from_u or not to_u:
            self.unit_result_lbl.configure(text="")
            return

        try:
            val = float(raw_val.replace(",", ""))
        except ValueError:
            self.unit_result_lbl.configure(text="숫자를 입력해주세요")
            return

        result = unit_service.convert(cat, val, from_u, to_u)

        # 결과 깔끔한 포맷
        formatted = self.format_number(result)
        self.unit_result_lbl.configure(text=f"= {formatted} {to_u.split()[0]}")

        # 전체 일괄 변환 표 갱신
        for item in self.unit_tree.get_children():
            self.unit_tree.delete(item)

        all_results = unit_service.convert_all(cat, val, from_u)
        for u, v in all_results.items():
            f_val = self.format_number(v)
            self.unit_tree.insert("", "end", values=(u, f_val))

    def format_number(self, num: float) -> str:
        """숫자를 가독성 있게 콤마 및 소수점 포맷"""
        if abs(num) >= 1e12 or (abs(num) < 1e-4 and num != 0):
            return f"{num:.6e}"
        if num == int(num):
            return f"{int(num):,}"
        formatted = f"{num:.6f}".rstrip("0").rstrip(".")
        parts = formatted.split(".")
        parts[0] = f"{int(parts[0]):,}"
        return ".".join(parts)

    # ==========================================================
    # 3. 실시간 환율 탭 (EXCHANGE RATE TAB)
    # ==========================================================
    def build_exchange_tab(self):
        # 상단 환율 계산 카드
        calc_card = tk.Frame(self.exchange_frame, bg=self.colors["card_bg"],
                             highlightbackground=self.colors["border"], highlightthickness=1)
        calc_card.pack(fill="x", pady=(0, 8), padx=2, ipady=8)

        # 금액 입력 행
        amt_row = tk.Frame(calc_card, bg=self.colors["card_bg"])
        amt_row.pack(fill="x", padx=12, pady=(6, 4))

        tk.Label(amt_row, text="금액", font=("Malgun Gothic", 10),
                 fg=self.colors["subtext"], bg=self.colors["card_bg"]).pack(side="left")

        self.exch_amt_var = tk.StringVar(value="1")
        self.exch_amt_entry = tk.Entry(
            amt_row,
            textvariable=self.exch_amt_var,
            font=("Malgun Gothic", 13, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            justify="right"
        )
        self.exch_amt_entry.pack(side="right", fill="x", expand=True, padx=(10, 0), ipady=3)
        self.exch_amt_var.trace_add("write", lambda *args: self.update_exchange_conversion())

        # 통화 선택 행 (From ⇄ To)
        curr_row = tk.Frame(calc_card, bg=self.colors["card_bg"])
        curr_row.pack(fill="x", padx=12, pady=6)

        curr_options = [f"{info['flag']} {code} ({info['name']})" for code, info in CURRENCIES.items()]

        self.exch_from_var = tk.StringVar()
        self.exch_to_var = tk.StringVar()

        self.exch_from_cb = ttk.Combobox(curr_row, textvariable=self.exch_from_var, values=curr_options,
                                         state="readonly", font=("Malgun Gothic", 10), width=18)
        self.exch_from_cb.pack(side="left", fill="x", expand=True)
        self.exch_from_cb.bind("<<ComboboxSelected>>", lambda e: self.update_exchange_conversion())

        swap_btn = tk.Button(
            curr_row,
            text="⇄",
            font=("Malgun Gothic", 13, "bold"),
            fg="#ffffff",
            bg=self.colors["border"],
            activebackground=self.colors["accent"],
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.swap_currencies
        )
        swap_btn.pack(side="left", padx=6)

        self.exch_to_cb = ttk.Combobox(curr_row, textvariable=self.exch_to_var, values=curr_options,
                                       state="readonly", font=("Malgun Gothic", 10), width=18)
        self.exch_to_cb.pack(side="left", fill="x", expand=True)
        self.exch_to_cb.bind("<<ComboboxSelected>>", lambda e: self.update_exchange_conversion())

        # 기본 선택: USD -> KRW
        usd_idx = [i for i, opt in enumerate(curr_options) if "USD" in opt][0]
        krw_idx = [i for i, opt in enumerate(curr_options) if "KRW" in opt][0]
        self.exch_from_cb.current(usd_idx)
        self.exch_to_cb.current(krw_idx)

        # 환율 결과 표시
        self.exch_result_lbl = tk.Label(
            calc_card,
            text="= 0 원",
            font=("Malgun Gothic", 17, "bold"),
            fg=self.colors["btn_eq"],
            bg=self.colors["card_bg"],
            anchor="e",
            padx=12
        )
        self.exch_result_lbl.pack(fill="x", pady=(6, 2))

        self.exch_rate_info_lbl = tk.Label(
            calc_card,
            text="",
            font=("Malgun Gothic", 9),
            fg=self.colors["subtext"],
            bg=self.colors["card_bg"],
            anchor="e",
            padx=12
        )
        self.exch_rate_info_lbl.pack(fill="x", pady=(0, 4))

        # 환율 상태 및 새로고침 바
        status_bar = tk.Frame(self.exchange_frame, bg=self.colors["bg"])
        status_bar.pack(fill="x", pady=(0, 6), padx=2)

        self.exch_status_lbl = tk.Label(
            status_bar,
            text="환율 상태 확인 중...",
            font=("Malgun Gothic", 9),
            fg=self.colors["subtext"],
            bg=self.colors["bg"]
        )
        self.exch_status_lbl.pack(side="left", padx=4)

        self.refresh_btn = tk.Button(
            status_bar,
            text="🔄 환율 새로고침",
            font=("Malgun Gothic", 9, "bold"),
            fg="#ffffff",
            bg=self.colors["accent"],
            activebackground=self.colors["accent_hover"],
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.refresh_rates_threaded
        )
        self.refresh_btn.pack(side="right")

        # 하단: 원화(KRW) 기준 주요국 환율표
        table_lbl = tk.Label(self.exchange_frame, text="주요국 원화(KRW) 기준 환율표 (더블클릭 시 변환기로 선택)",
                             font=("Malgun Gothic", 10, "bold"), fg=self.colors["subtext"], bg=self.colors["bg"])
        table_lbl.pack(anchor="w", padx=4, pady=(2, 4))

        tree_box = tk.Frame(self.exchange_frame, bg=self.colors["card_bg"],
                            highlightbackground=self.colors["border"], highlightthickness=1)
        tree_box.pack(fill="both", expand=True, padx=2)

        self.rate_tree = ttk.Treeview(tree_box, columns=("currency", "name", "rate"), show="headings", height=8)
        self.rate_tree.heading("currency", text="통화")
        self.rate_tree.heading("name", text="통화명")
        self.rate_tree.heading("rate", text="매매기준율 (KRW)")
        self.rate_tree.column("currency", width=100, anchor="w")
        self.rate_tree.column("name", width=180, anchor="w")
        self.rate_tree.column("rate", width=140, anchor="e")

        tree_scroll = ttk.Scrollbar(tree_box, orient="vertical", command=self.rate_tree.yview)
        self.rate_tree.configure(yscrollcommand=tree_scroll.set)

        self.rate_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        self.rate_tree.bind("<Double-1>", self.on_rate_table_double_click)

    def extract_currency_code(self, opt_str: str) -> str:
        # "🇺🇸 USD (미국 달러)" 형태에서 'USD' 추출
        parts = opt_str.split()
        if len(parts) >= 2:
            return parts[1]
        return "USD"

    def swap_currencies(self):
        f = self.exch_from_var.get()
        t = self.exch_to_var.get()
        self.exch_from_var.set(t)
        self.exch_to_var.set(f)
        self.update_exchange_conversion()

    def update_exchange_conversion(self):
        raw_amt = self.exch_amt_var.get().strip()
        from_str = self.exch_from_var.get()
        to_str = self.exch_to_var.get()

        if not raw_amt or not from_str or not to_str:
            self.exch_result_lbl.configure(text="")
            self.exch_rate_info_lbl.configure(text="")
            return

        try:
            amt = float(raw_amt.replace(",", ""))
        except ValueError:
            self.exch_result_lbl.configure(text="금액을 숫자로 입력해주세요")
            return

        from_code = self.extract_currency_code(from_str)
        to_code = self.extract_currency_code(to_str)

        converted = currency_service.convert(amt, from_code, to_code)
        one_unit_rate = currency_service.convert(1.0, from_code, to_code)

        # 표시
        to_sym = CURRENCIES.get(to_code, {}).get("symbol", "")
        formatted_res = f"{converted:,.2f}" if to_code not in ["KRW", "JPY", "VND"] else f"{converted:,.0f}"
        self.exch_result_lbl.configure(text=f"= {to_sym} {formatted_res} {to_code}")

        rate_fmt = f"{one_unit_rate:,.4f}" if one_unit_rate < 100 else f"{one_unit_rate:,.2f}"
        self.exch_rate_info_lbl.configure(text=f"기준환율: 1 {from_code} = {rate_fmt} {to_code}")

    def refresh_rates_threaded(self):
        self.exch_status_lbl.configure(text="⏳ 최신 환율 동기화 중...", fg=self.colors["accent"])
        self.refresh_btn.configure(state="disabled")

        def worker():
            ok, msg = currency_service.fetch_latest_rates()
            self.after(0, lambda: self.on_rates_refreshed(ok, msg))

        threading.Thread(target=worker, daemon=True).start()

    def on_rates_refreshed(self, ok, msg):
        self.refresh_btn.configure(state="normal")
        status_time = currency_service.last_update_time or "정보 없음"
        if ok:
            self.exch_status_lbl.configure(text=f"🟢 실시간 연동됨 ({status_time})", fg="#10b981")
        else:
            self.exch_status_lbl.configure(text=f"🟡 오프라인 캐시 모드 ({status_time})", fg="#f59e0b")

        # 환율표 갱신
        self.populate_rate_table()
        # 변환 결과 갱신
        self.update_exchange_conversion()

    def populate_rate_table(self):
        for item in self.rate_tree.get_children():
            self.rate_tree.delete(item)

        table_data = currency_service.get_krw_rate_table()
        for item in table_data:
            curr_col = f"{item['flag']} {item['unit_text']}"
            name_col = item["name"]
            rate_val = item["krw_value"]
            rate_fmt = f"{rate_val:,.2f} 원"
            self.rate_tree.insert("", "end", values=(curr_col, name_col, rate_fmt), tags=(item["code"],))

    def on_rate_table_double_click(self, event):
        selected = self.rate_tree.selection()
        if not selected:
            return
        item_vals = self.rate_tree.item(selected[0], "values")
        if item_vals:
            # 첫 컬럼에서 통화 코드 추출
            raw_text = item_vals[0]
            words = raw_text.split()
            code = words[1] if len(words) > 1 else words[0]
            # 출발 통화로 설정
            for opt in self.exch_from_cb["values"]:
                if f" {code} " in opt:
                    self.exch_from_var.set(opt)
                    self.update_exchange_conversion()
                    break

    # ==========================================================
    # 4. 계산 기록 탭 (HISTORY TAB)
    # ==========================================================
    def build_history_tab(self):
        btn_bar = tk.Frame(self.history_frame, bg=self.colors["bg"])
        btn_bar.pack(fill="x", pady=(0, 6))

        tk.Label(btn_bar, text="최근 계산 기록", font=("Malgun Gothic", 11, "bold"),
                 fg=self.colors["text"], bg=self.colors["bg"]).pack(side="left")

        clear_btn = tk.Button(
            btn_bar,
            text="🗑️ 기록 모두 지우기",
            font=("Malgun Gothic", 9),
            fg="#ffffff",
            bg=self.colors["btn_danger"],
            activebackground=self.colors["btn_danger_hover"],
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.clear_history
        )
        clear_btn.pack(side="right")

        tree_box = tk.Frame(self.history_frame, bg=self.colors["card_bg"],
                            highlightbackground=self.colors["border"], highlightthickness=1)
        tree_box.pack(fill="both", expand=True)

        self.hist_tree = ttk.Treeview(tree_box, columns=("expr", "result"), show="headings")
        self.hist_tree.heading("expr", text="수식")
        self.hist_tree.heading("result", text="계산 결과")
        self.hist_tree.column("expr", width=250, anchor="w")
        self.hist_tree.column("result", width=170, anchor="e")

        hist_scroll = ttk.Scrollbar(tree_box, orient="vertical", command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=hist_scroll.set)

        self.hist_tree.pack(side="left", fill="both", expand=True)
        hist_scroll.pack(side="right", fill="y")

        self.hist_tree.bind("<Double-1>", self.on_history_double_click)

        tip_lbl = tk.Label(self.history_frame, text="💡 팁: 기록 항목을 더블클릭하면 계산기로 불러옵니다.",
                           font=("Malgun Gothic", 9), fg=self.colors["subtext"], bg=self.colors["bg"])
        tip_lbl.pack(anchor="w", pady=(6, 0))

    def refresh_history_table(self):
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        for record in calculator_core.get_history():
            self.hist_tree.insert("", "end", values=(record["expr"], record["result"]))

    def clear_history(self):
        calculator_core.clear_history()
        self.refresh_history_table()

    def on_history_double_click(self, event):
        sel = self.hist_tree.selection()
        if not sel:
            return
        vals = self.hist_tree.item(sel[0], "values")
        if vals:
            res = vals[1]
            self.current_expr = res
            self.calc_disp_lbl.configure(text=res)
            self.calc_expr_lbl.configure(text=f"불러옴: {vals[0]}")
            self.switch_tab("calc")


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()
