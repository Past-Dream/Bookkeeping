import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum


class RecordType(Enum):
    INCOME = "收入"
    EXPENSE = "支出"


class PaymentMethod(Enum):
    CASH = "现金"
    WECHAT = "微信"
    ALIPAY = "支付宝"
    BANK_CARD = "银行卡"


class Category:
    def __init__(self, category_id: int, name: str, icon: str, color: str = "#666666"):
        self.category_id = category_id
        self.name = name
        self.icon = icon
        self.color = color


class Record:
    def __init__(self, record_id: int, amount: float, record_type: RecordType,
                 category: Category, payment_method: PaymentMethod,
                 note: str = "", record_date: Optional[datetime] = None):
        self.record_id = record_id
        self.amount = amount
        self.record_type = record_type
        self.category = category
        self.payment_method = payment_method
        self.note = note
        self.record_date = record_date or datetime.now()

    def get_formatted_date(self) -> str:
        return self.record_date.strftime("%m/%d %H:%M")

    def get_formatted_time(self) -> str:
        now = datetime.now()
        if self.record_date.date() == now.date():
            return "今天 " + self.record_date.strftime("%H:%M")
        elif self.record_date.date() == now.replace(day=now.day - 1).date():
            return "昨天 " + self.record_date.strftime("%H:%M")
        else:
            return self.record_date.strftime("%m/%d %H:%M")


class RecordManager:
    def __init__(self, db_path: str = "finance.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    category_id INTEGER,
                    payment_method TEXT NOT NULL,
                    note TEXT,
                    record_date TEXT NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    icon TEXT,
                    color TEXT
                )
            ''')

            self._insert_default_data(cursor)
            conn.commit()
            conn.close()
            print("数据库初始化成功")
        except Exception as e:
            print(f"数据库初始化错误: {e}")

    def _insert_default_data(self, cursor):
        categories = [
            (1, "美食饮品", "🍔", "#FF6B6B"),
            (2, "购物消费", "🎒", "#4ECDC4"),
            (3, "交通出行", "🚗", "#45B7D1"),
            (4, "娱乐休闲", "🎮", "#96CEB4"),
            (5, "数码家电", "📱", "#F7DC6F"),
            (6, "医疗健康", "🏥", "#BB8FCE"),
            (7, "教育培训", "📚", "#F1948A"),
            (8, "工资收入", "💰", "#52BE80"),
            (9, "投资理财", "📈", "#5499C7"),
            (10, "其他", "📦", "#95A5A6")
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO categories (id, name, icon, color) VALUES (?, ?, ?, ?)
        ''', categories)

    def add_record(self, record: Record) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO records (amount, type, category_id, payment_method, note, record_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                record.amount,
                record.record_type.value,
                record.category.category_id,
                record.payment_method.value,
                record.note,
                record.record_date.isoformat()
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加记录错误: {e}")
            return False

    def get_all_records(self, limit: int = None) -> List[Record]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = '''
                SELECT r.id, r.amount, r.type, r.category_id, r.payment_method, r.note, r.record_date,
                       c.name as category_name, c.icon, c.color
                FROM records r
                LEFT JOIN categories c ON r.category_id = c.id
                ORDER BY r.record_date DESC
            '''

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)

            records = []
            for row in cursor.fetchall():
                category = Category(row[3], row[7], row[8], row[9])
                try:
                    record_date = datetime.fromisoformat(row[6])
                except ValueError:
                    record_date = datetime.now()

                record = Record(
                    row[0], row[1], RecordType(row[2]), category,
                    PaymentMethod(row[4]), row[5], record_date
                )
                records.append(record)

            conn.close()
            return records
        except Exception as e:
            print(f"获取记录错误: {e}")
            return []

    def get_records_by_date_range(self, start_date: datetime, end_date: datetime, record_type: str = None) -> List[
        Record]:
        """根据日期范围和类型获取记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = '''
                SELECT r.id, r.amount, r.type, r.category_id, r.payment_method, r.note, r.record_date,
                       c.name as category_name, c.icon, c.color
                FROM records r
                LEFT JOIN categories c ON r.category_id = c.id
                WHERE r.record_date BETWEEN ? AND ?
            '''

            params = [start_date.isoformat(), end_date.isoformat()]

            if record_type and record_type != "全部":
                query += " AND r.type = ?"
                params.append(record_type)

            query += " ORDER BY r.record_date DESC"

            cursor.execute(query, params)

            records = []
            for row in cursor.fetchall():
                category = Category(row[3], row[7], row[8], row[9])
                try:
                    record_date = datetime.fromisoformat(row[6])
                except ValueError:
                    record_date = datetime.now()

                record = Record(
                    row[0], row[1], RecordType(row[2]), category,
                    PaymentMethod(row[4]), row[5], record_date
                )
                records.append(record)

            conn.close()
            return records
        except Exception as e:
            print(f"按日期范围获取记录错误: {e}")
            return []

    def get_summary_by_date_range(self, start_date: datetime, end_date: datetime, record_type: str = None) -> Dict[
        str, float]:
        """根据日期范围和类型获取统计摘要"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = '''
                SELECT type, SUM(amount) 
                FROM records 
                WHERE record_date BETWEEN ? AND ?
            '''

            params = [start_date.isoformat(), end_date.isoformat()]

            if record_type and record_type != "全部":
                query += " AND type = ?"
                params.append(record_type)

            query += " GROUP BY type"

            cursor.execute(query, params)

            result = {"收入": 0.0, "支出": 0.0}
            for row in cursor.fetchall():
                result[row[0]] = row[1] or 0.0

            conn.close()

            # 如果指定了类型，只返回该类型的数据
            if record_type and record_type != "全部":
                return {record_type: result.get(record_type, 0.0)}

            return result
        except Exception as e:
            print(f"获取日期范围统计错误: {e}")
            return {"收入": 0.0, "支出": 0.0}

    def get_category_summary(self, start_date: datetime, end_date: datetime, record_type: str = None) -> Dict[
        str, Dict[str, float]]:
        """获取分类统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = '''
                SELECT c.name, r.type, SUM(r.amount)
                FROM records r
                LEFT JOIN categories c ON r.category_id = c.id
                WHERE r.record_date BETWEEN ? AND ?
            '''

            params = [start_date.isoformat(), end_date.isoformat()]

            if record_type and record_type != "全部":
                query += " AND r.type = ?"
                params.append(record_type)

            query += " GROUP BY c.name, r.type"

            cursor.execute(query, params)

            result = {}
            for row in cursor.fetchall():
                category_name, record_type_val, amount = row
                if category_name not in result:
                    result[category_name] = {"收入": 0.0, "支出": 0.0}
                result[category_name][record_type_val] = amount or 0.0

            conn.close()
            return result
        except Exception as e:
            print(f"获取分类统计错误: {e}")
            return {}

    def get_monthly_summary(self) -> Dict[str, float]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            current_month = datetime.now().strftime("%Y-%m")
            cursor.execute('''
                SELECT type, SUM(amount) 
                FROM records 
                WHERE strftime('%Y-%m', record_date) = ?
                GROUP BY type
            ''', (current_month,))

            result = {"收入": 0.0, "支出": 0.0}
            for row in cursor.fetchall():
                result[row[0]] = row[1] or 0.0

            conn.close()
            return result
        except Exception as e:
            print(f"获取月度统计错误: {e}")
            return {"收入": 0.0, "支出": 0.0}


class CompactRecordDialog(tk.Toplevel):
    """紧凑型记录对话框"""

    def __init__(self, parent, record_manager: RecordManager, categories: List[Category]):
        super().__init__(parent)
        self.record_manager = record_manager
        self.categories = categories
        self.amount = 0.0
        self.selected_category = None

        self.title("记录收支")
        self.geometry("380x600")
        self.configure(bg="white")
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._setup_bindings()

    def _create_widgets(self):
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.title_label = tk.Label(main_frame, text="记录收支", font=("Arial", 14, "bold"),
                                    bg="white", fg="#333333")
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        amount_frame = tk.Frame(main_frame, bg="white")
        amount_frame.grid(row=1, column=0, columnspan=2, pady=(0, 8), sticky="ew")

        tk.Label(amount_frame, text="金额", font=("Arial", 10),
                 bg="white", fg="#666666").pack(anchor="w")

        self.amount_entry = tk.Entry(amount_frame, font=("Arial", 16, "bold"),
                                     relief="flat", bg="#f5f5f5", justify="right")
        self.amount_entry.pack(fill="x", pady=3)
        self.amount_entry.insert(0, "0.00")
        self.amount_entry.bind("<KeyRelease>", self._on_amount_change)

        self.type_var = tk.StringVar(value="支出")
        type_frame = tk.Frame(main_frame, bg="white")
        type_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        tk.Radiobutton(type_frame, text="支出", variable=self.type_var,
                       value="支出", font=("Arial", 10), bg="white",
                       command=self._update_amount_color).pack(side="left", padx=15)
        tk.Radiobutton(type_frame, text="收入", variable=self.type_var,
                       value="收入", font=("Arial", 10), bg="white",
                       command=self._update_amount_color).pack(side="left", padx=15)

        self._create_category_selector(main_frame)

        payment_frame = tk.Frame(main_frame, bg="white")
        payment_frame.grid(row=4, column=0, columnspan=2, pady=(0, 8), sticky="ew")

        tk.Label(payment_frame, text="支付方式", font=("Arial", 10),
                 bg="white", fg="#666666").pack(anchor="w")

        self.payment_var = tk.StringVar(value="支付宝")
        payment_combo = ttk.Combobox(payment_frame, textvariable=self.payment_var,
                                     values=["支付宝", "微信", "现金", "银行卡"],
                                     state="readonly", height=4, font=("Arial", 10))
        payment_combo.pack(fill="x", pady=3)

        note_frame = tk.Frame(main_frame, bg="white")
        note_frame.grid(row=5, column=0, columnspan=2, pady=(0, 10), sticky="ew")

        tk.Label(note_frame, text="备注", font=("Arial", 10),
                 bg="white", fg="#666666").pack(anchor="w")

        self.note_entry = tk.Entry(note_frame, font=("Arial", 10), relief="flat",
                                   bg="#f5f5f5")
        self.note_entry.pack(fill="x", pady=3)
        self.note_entry.insert(0, "添加备注（可选）")
        self.note_entry.bind("<FocusIn>", self._clear_placeholder)

        button_frame = tk.Frame(main_frame, bg="white")
        button_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0), sticky="ew")

        tk.Button(button_frame, text="取消", font=("Arial", 10),
                  bg="#f0f0f0", fg="#666666", relief="flat",
                  command=self.destroy).pack(side="left", padx=5)

        tk.Button(button_frame, text="保存记录", font=("Arial", 10),
                  bg="#1890ff", fg="white", relief="flat",
                  command=self._save_record).pack(side="right", padx=5)

        for i in range(7):
            main_frame.rowconfigure(i, weight=0)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def _create_category_selector(self, parent):
        category_frame = tk.Frame(parent, bg="white")
        category_frame.grid(row=3, column=0, columnspan=2, pady=(0, 8), sticky="ew")

        tk.Label(category_frame, text="分类", font=("Arial", 10),
                 bg="white", fg="#666666").pack(anchor="w")

        self.category_buttons = []
        categories_subframe = tk.Frame(category_frame, bg="white")
        categories_subframe.pack(fill="x", pady=5)

        for i, category in enumerate(self.categories[:8]):
            row = i // 4
            col = i % 4

            btn_frame = tk.Frame(categories_subframe, bg="white")
            btn_frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

            btn = tk.Button(btn_frame, text=category.icon, font=("Arial", 14),
                            bg="#f5f5f5", fg=category.color, relief="flat",
                            width=2, height=1, command=lambda c=category: self._select_category(c))
            btn.pack()

            tk.Label(btn_frame, text=category.name, font=("Arial", 8),
                     bg="white", fg="#666666").pack()

            self.category_buttons.append(btn)

            categories_subframe.columnconfigure(col, weight=1)
            categories_subframe.rowconfigure(row, weight=1)

    def _setup_bindings(self):
        if self.categories:
            self._select_category(self.categories[0])
        self.bind("<Return>", lambda e: self._save_record())
        self.amount_entry.focus_set()

    def _on_amount_change(self, event):
        current_text = self.amount_entry.get()
        filtered_text = ''.join(c for c in current_text if c.isdigit() or c == '.')

        if filtered_text.count('.') > 1:
            parts = filtered_text.split('.')
            filtered_text = parts[0] + '.' + ''.join(parts[1:])

        if '.' in filtered_text:
            integer_part, decimal_part = filtered_text.split('.')
            if len(decimal_part) > 2:
                filtered_text = integer_part + '.' + decimal_part[:2]

        if filtered_text != current_text:
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, filtered_text)

        try:
            if filtered_text and filtered_text != '.':
                self.amount = float(filtered_text) if filtered_text not in ['', '.'] else 0.0
            else:
                self.amount = 0.0
        except ValueError:
            self.amount = 0.0

        self._update_amount_color()

    def _clear_placeholder(self, event):
        if self.note_entry.get() == "添加备注（可选）":
            self.note_entry.delete(0, tk.END)

    def _select_category(self, category):
        self.selected_category = category
        for i, btn in enumerate(self.category_buttons):
            if i < len(self.categories) and self.categories[i].category_id == category.category_id:
                btn.configure(bg="#e6f7ff")
            else:
                btn.configure(bg="#f5f5f5")

    def _update_amount_color(self):
        color = "#ff4d4f" if self.type_var.get() == "支出" else "#52c41a"
        self.amount_entry.configure(fg=color)

    def _save_record(self):
        if not self.selected_category:
            messagebox.showerror("错误", "请选择分类")
            return

        if self.amount <= 0:
            messagebox.showerror("错误", "金额必须大于0")
            return

        try:
            record = Record(
                record_id=0,
                amount=self.amount,
                record_type=RecordType.INCOME if self.type_var.get() == "收入" else RecordType.EXPENSE,
                category=self.selected_category,
                payment_method=PaymentMethod(self.payment_var.get()),
                note=self.note_entry.get() if self.note_entry.get() != "添加备注（可选）" else ""
            )

            if self.record_manager.add_record(record):
                messagebox.showinfo("成功", "记录保存成功")
                self.destroy()
            else:
                messagebox.showerror("错误", "保存记录失败")
        except Exception as e:
            messagebox.showerror("错误", f"保存记录时发生错误: {e}")


class StatisticsDialog(tk.Toplevel):
    """统计对话框"""

    def __init__(self, parent, record_manager: RecordManager):
        super().__init__(parent)
        self.record_manager = record_manager
        self.title("收支统计")
        self.geometry("600x700")
        self.configure(bg="white")
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._load_data()

    def _create_widgets(self):
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        title_label = tk.Label(main_frame, text="收支统计", font=("Arial", 16, "bold"),
                               bg="white", fg="#333333")
        title_label.pack(pady=(0, 15))

        time_frame = tk.Frame(main_frame, bg="white")
        time_frame.pack(fill="x", pady=(0, 15))

        tk.Label(time_frame, text="开始日期:", font=("Arial", 10),
                 bg="white").pack(side="left", padx=(0, 10))

        self.start_date = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        start_entry = tk.Entry(time_frame, textvariable=self.start_date, font=("Arial", 10), width=12)
        start_entry.pack(side="left", padx=(0, 20))

        tk.Label(time_frame, text="结束日期:", font=("Arial", 10),
                 bg="white").pack(side="left", padx=(0, 10))

        self.end_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        end_entry = tk.Entry(time_frame, textvariable=self.end_date, font=("Arial", 10), width=12)
        end_entry.pack(side="left", padx=(0, 20))

        tk.Label(time_frame, text="类型:", font=("Arial", 10),
                 bg="white").pack(side="left", padx=(0, 10))

        self.type_var = tk.StringVar(value="全部")
        type_combo = ttk.Combobox(time_frame, textvariable=self.type_var,
                                  values=["全部", "收入", "支出"], state="readonly",
                                  width=8, font=("Arial", 10))
        type_combo.pack(side="left", padx=(0, 20))

        tk.Button(time_frame, text="查询", font=("Arial", 10),
                  command=self._load_data, bg="#1890ff", fg="white").pack(side="left")

        summary_frame = tk.LabelFrame(main_frame, text="统计摘要", font=("Arial", 12, "bold"),
                                      bg="white", fg="#333333")
        summary_frame.pack(fill="x", pady=(0, 15))

        self.income_var = tk.StringVar(value="收入: ￥0.00")
        self.expense_var = tk.StringVar(value="支出: ￥0.00")
        self.balance_var = tk.StringVar(value="结余: ￥0.00")

        tk.Label(summary_frame, textvariable=self.income_var, font=("Arial", 12),
                 bg="white", fg="#52c41a").pack(side="left", padx=20, pady=10)
        tk.Label(summary_frame, textvariable=self.expense_var, font=("Arial", 12),
                 bg="white", fg="#ff4d4f").pack(side="left", padx=20, pady=10)
        tk.Label(summary_frame, textvariable=self.balance_var, font=("Arial", 12, "bold"),
                 bg="white", fg="#333333").pack(side="left", padx=20, pady=10)

        category_frame = tk.LabelFrame(main_frame, text="分类统计", font=("Arial", 12, "bold"),
                                       bg="white", fg="#333333")
        category_frame.pack(fill="both", expand=True, pady=(0, 15))

        columns = ("分类", "收入", "支出", "占比")
        self.tree = ttk.Treeview(category_frame, columns=columns, show="tree headings", height=10)

        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("分类", width=150, anchor="w")
        self.tree.column("收入", width=100, anchor="e")
        self.tree.column("支出", width=100, anchor="e")
        self.tree.column("占比", width=100, anchor="e")

        for col in columns:
            self.tree.heading(col, text=col)

        scrollbar = ttk.Scrollbar(category_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _load_data(self):
        try:
            start_dt = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
            end_dt = datetime.strptime(self.end_date.get(), "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        except ValueError:
            messagebox.showerror("错误", "日期格式不正确，请使用YYYY-MM-DD格式")
            return

        record_type = self.type_var.get()

        summary = self.record_manager.get_summary_by_date_range(start_dt, end_dt, record_type)

        if record_type == "全部":
            income = summary.get("收入", 0)
            expense = summary.get("支出", 0)
            balance = income - expense

            self.income_var.set(f"收入: ￥{income:.2f}")
            self.expense_var.set(f"支出: ￥{expense:.2f}")
            self.balance_var.set(f"结余: ￥{balance:.2f}")
        else:
            amount = summary.get(record_type, 0)
            if record_type == "收入":
                self.income_var.set(f"收入: ￥{amount:.2f}")
                self.expense_var.set("支出: ￥0.00")
                self.balance_var.set(f"结余: ￥{amount:.2f}")
            else:
                self.income_var.set("收入: ￥0.00")
                self.expense_var.set(f"支出: ￥{amount:.2f}")
                self.balance_var.set(f"结余: ￥{-amount:.2f}")

        category_summary = self.record_manager.get_category_summary(start_dt, end_dt, record_type)

        for item in self.tree.get_children():
            self.tree.delete(item)

        if record_type == "全部":
            total_income = summary.get("收入", 0)
            total_expense = summary.get("支出", 0)
            total_amount = total_income + total_expense
        else:
            total_income = 0
            total_expense = 0
            total_amount = summary.get(record_type, 0)

        for category_name, data in category_summary.items():
            cat_income = data.get("收入", 0)
            cat_expense = data.get("支出", 0)

            if record_type == "全部":
                total = total_income + total_expense
                percentage = ((cat_income + cat_expense) / total * 100) if total > 0 else 0
                self.tree.insert("", "end", values=(
                    category_name,
                    f"￥{cat_income:.2f}" if cat_income > 0 else "-",
                    f"￥{cat_expense:.2f}" if cat_expense > 0 else "-",
                    f"{percentage:.1f}%" if (cat_income + cat_expense) > 0 else "-"
                ))
            elif record_type == "收入":
                percentage = (cat_income / total_amount * 100) if total_amount > 0 else 0
                self.tree.insert("", "end", values=(
                    category_name,
                    f"￥{cat_income:.2f}" if cat_income > 0 else "-",
                    "-",
                    f"{percentage:.1f}%" if cat_income > 0 else "-"
                ))
            else:
                percentage = (cat_expense / total_amount * 100) if total_amount > 0 else 0
                self.tree.insert("", "end", values=(
                    category_name,
                    "-",
                    f"￥{cat_expense:.2f}" if cat_expense > 0 else "-",
                    f"{percentage:.1f}%" if cat_expense > 0 else "-"
                ))


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("智能记账本")
        self.geometry("400x640")
        self.configure(bg="white")

        self.record_manager = RecordManager()
        self.categories = self._load_categories()

        self._create_widgets()
        self._create_sample_data()
        self.update_balance()
        self.refresh_transactions()

    def _load_categories(self) -> List[Category]:
        try:
            conn = sqlite3.connect(self.record_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, icon, color FROM categories")
            categories = [Category(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()]
            conn.close()
            return categories
        except:
            return []

    def _create_widgets(self):
        header_frame = tk.Frame(self, bg="white", height=50)
        header_frame.pack(fill="x", padx=15, pady=8)
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="智能记账本", font=("Arial", 16, "bold"),
                 bg="white", fg="#333333").pack(side="left")

        icon_frame = tk.Frame(header_frame, bg="white")
        icon_frame.pack(side="right")
        tk.Label(icon_frame, text="🔍", font=("Arial", 14), bg="white").pack(side="left", padx=4)
        tk.Label(icon_frame, text="⏰", font=("Arial", 14), bg="white").pack(side="left", padx=4)

        balance_frame = tk.Frame(self, bg="#667eea", height=100)
        balance_frame.pack(fill="x", padx=15, pady=8)
        balance_frame.pack_propagate(False)

        tk.Label(balance_frame, text="当前余额", font=("Arial", 10),
                 bg="#667eea", fg="white").place(relx=0.1, rely=0.2)

        self.amount_label = tk.Label(balance_frame, text="￥0.00", font=("Arial", 20, "bold"),
                                     bg="#667eea", fg="white")
        self.amount_label.place(relx=0.1, rely=0.4)

        stats_frame = tk.Frame(balance_frame, bg="#667eea")
        stats_frame.place(relx=0.1, rely=0.7, relwidth=0.8)

        self.income_label = tk.Label(stats_frame, text="本月收入 ￥0.00", font=("Arial", 9),
                                     bg="#667eea", fg="#90EE90")
        self.income_label.pack(side="left", padx=8)

        self.expense_label = tk.Label(stats_frame, text="本月支出 ￥0.00", font=("Arial", 9),
                                      bg="#667eea", fg="#FFB6C1")
        self.expense_label.pack(side="right", padx=8)

        func_frame = tk.Frame(self, bg="white")
        func_frame.pack(fill="x", padx=15, pady=10)

        functions = [("📊", "统计", self.show_statistics),
                     ("➕", "记录", self.show_record_dialog),
                     ("💰", "预算", self.show_budget),
                     ("⚙️", "设置", self.show_settings)]

        for icon, text, command in functions:
            btn_frame = tk.Frame(func_frame, bg="white", cursor="hand2")
            btn_frame.pack(side="left", expand=True)
            btn_frame.bind("<Button-1>", lambda e, cmd=command: cmd())

            icon_label = tk.Label(btn_frame, text=icon, font=("Arial", 18), bg="white", cursor="hand2")
            icon_label.pack()
            icon_label.bind("<Button-1>", lambda e, cmd=command: cmd())

            text_label = tk.Label(btn_frame, text=text, font=("Arial", 9), bg="white", fg="#666666", cursor="hand2")
            text_label.pack()
            text_label.bind("<Button-1>", lambda e, cmd=command: cmd())

        trans_header = tk.Frame(self, bg="white")
        trans_header.pack(fill="x", padx=15, pady=8)

        tk.Label(trans_header, text="最近交易", font=("Arial", 12, "bold"),
                 bg="white", fg="#333333").pack(side="left")

        view_all_label = tk.Label(trans_header, text="查看全部", font=("Arial", 10),
                                  bg="white", fg="#1890ff", cursor="hand2")
        view_all_label.pack(side="right")
        view_all_label.bind("<Button-1>", lambda e: self.show_all_records())

        self.transactions_frame = tk.Frame(self, bg="white")
        self.transactions_frame.pack(fill="both", expand=True, padx=15, pady=5)

        nav_frame = tk.Frame(self, bg="#fafafa", height=50)
        nav_frame.pack(fill="x", side="bottom")
        nav_frame.pack_propagate(False)

        # 修复底部标签栏点击响应问题
        nav_items = [("🏠", "首页", lambda: messagebox.showinfo("提示", "首页功能开发中...")),
                     ("📈", "图表", lambda: messagebox.showinfo("提示", "图表功能开发中...")),
                     ("👤", "我的", lambda: messagebox.showinfo("提示", "个人中心功能开发中..."))]

        for icon, text, command in nav_items:
            nav_btn_frame = tk.Frame(nav_frame, bg="#fafafa", cursor="hand2")
            nav_btn_frame.pack(side="left", expand=True)
            nav_btn_frame.bind("<Button-1>", lambda e, cmd=command: cmd())

            icon_label = tk.Label(nav_btn_frame, text=icon, font=("Arial", 14), bg="#fafafa", cursor="hand2")
            icon_label.pack(pady=3)
            icon_label.bind("<Button-1>", lambda e, cmd=command: cmd())

            text_label = tk.Label(nav_btn_frame, text=text, font=("Arial", 9), bg="#fafafa", fg="#1890ff",
                                  cursor="hand2")
            text_label.pack()
            text_label.bind("<Button-1>", lambda e, cmd=command: cmd())

    def _create_sample_data(self):
        records = self.record_manager.get_all_records()
        if not records:
            sample_records = [
                (256.80, RecordType.EXPENSE, self.categories[1], PaymentMethod.ALIPAY, "超市购物"),
                (6600.00, RecordType.INCOME, self.categories[7], PaymentMethod.WECHAT, "工资"),
                (128.00, RecordType.EXPENSE, self.categories[0], PaymentMethod.WECHAT, "晚餐"),
                (39.00, RecordType.EXPENSE, self.categories[3], PaymentMethod.CASH, "电影票")
            ]

            for amount, rtype, category, payment, note in sample_records:
                record = Record(0, amount, rtype, category, payment, note)
                self.record_manager.add_record(record)

        self.refresh_transactions()

    def show_record_dialog(self):
        dialog = CompactRecordDialog(self, self.record_manager, self.categories)
        self.wait_window(dialog)
        self.refresh_transactions()
        self.update_balance()

    def show_statistics(self):
        dialog = StatisticsDialog(self, self.record_manager)
        self.wait_window(dialog)

    def show_budget(self):
        messagebox.showinfo("预算", "预算功能开发中...")

    def show_settings(self):
        messagebox.showinfo("设置", "设置功能开发中...")

    def show_all_records(self):
        records = self.record_manager.get_all_records()
        if not records:
            messagebox.showinfo("所有记录", "暂无交易记录")
            return

        all_records_window = tk.Toplevel(self)
        all_records_window.title("所有交易记录")
        all_records_window.geometry("600x500")

        table_frame = tk.Frame(all_records_window, bg="white")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("日期", "类型", "分类", "金额", "支付方式", "备注")
        tree = ttk.Treeview(table_frame, columns=columns, show="tree headings", height=20)

        tree.column("#0", width=0, stretch=tk.NO)
        tree.column("日期", width=120, anchor="center")
        tree.column("类型", width=60, anchor="center")
        tree.column("分类", width=80, anchor="center")
        tree.column("金额", width=100, anchor="e")
        tree.column("支付方式", width=80, anchor="center")
        tree.column("备注", width=120, anchor="w")

        for col in columns:
            tree.heading(col, text=col)

        for record in records:
            amount_color = "#52c41a" if record.record_type == RecordType.INCOME else "#ff4d4f"
            amount_sign = "+" if record.record_type == RecordType.INCOME else "-"
            amount_text = f"{amount_sign}￥{record.amount:.2f}"

            item_id = tree.insert("", "end", values=(
                record.get_formatted_time(),
                record.record_type.value,
                record.category.name,
                amount_text,
                record.payment_method.value,
                record.note
            ))

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def update_balance(self):
        summary = self.record_manager.get_monthly_summary()
        income = summary.get("收入", 0)
        expense = summary.get("支出", 0)
        balance = income - expense

        self.amount_label.configure(text=f"￥{balance:.2f}")
        self.income_label.configure(text=f"本月收入 ￥{income:.2f}")
        self.expense_label.configure(text=f"本月支出 ￥{expense:.2f}")

    def refresh_transactions(self):
        for widget in self.transactions_frame.winfo_children():
            widget.destroy()

        records = self.record_manager.get_all_records()[:10]

        if not records:
            empty_label = tk.Label(self.transactions_frame, text="暂无交易记录",
                                   font=("Arial", 12), bg="white", fg="#999999")
            empty_label.pack(pady=20)
            return

        for record in records:
            self._create_transaction_item(record)

    def _create_transaction_item(self, record: Record):
        item_frame = tk.Frame(self.transactions_frame, bg="white", height=60)
        item_frame.pack(fill="x", pady=2)
        item_frame.pack_propagate(False)

        icon_frame = tk.Frame(item_frame, bg="#f5f5f5", width=40, height=40)
        icon_frame.pack(side="left", padx=10, pady=10)
        icon_frame.pack_propagate(False)

        icon_label = tk.Label(icon_frame, text=record.category.icon, font=("Arial", 16),
                              bg="#f5f5f5")
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        info_frame = tk.Frame(item_frame, bg="white")
        info_frame.pack(side="left", fill="both", expand=True, pady=10)

        name_frame = tk.Frame(info_frame, bg="white")
        name_frame.pack(fill="x", pady=2)

        tk.Label(name_frame, text=record.category.name, font=("Arial", 10, "bold"),
                 bg="white", fg="#333333").pack(side="left")

        if record.note:
            tk.Label(name_frame, text=f"·{record.note}", font=("Arial", 9),
                     bg="white", fg="#999999").pack(side="left", padx=5)

        tk.Label(info_frame, text=record.get_formatted_time(), font=("Arial", 9),
                 bg="white", fg="#999999").pack(anchor="w")

        amount_color = "#52c41a" if record.record_type == RecordType.INCOME else "#ff4d4f"
        amount_sign = "+" if record.record_type == RecordType.INCOME else "-"
        amount_label = tk.Label(item_frame, text=f"{amount_sign}￥{record.amount:.2f}",
                                font=("Arial", 11, "bold"), bg="white", fg=amount_color)
        amount_label.pack(side="right", padx=15, pady=10)

        sep = tk.Frame(self.transactions_frame, bg="#f0f0f0", height=1)
        sep.pack(fill="x")


def main():
    try:
        app = MainApp()
        app.mainloop()
    except Exception as e:
        print(f"应用程序错误: {e}")


if __name__ == "__main__":
    main()
