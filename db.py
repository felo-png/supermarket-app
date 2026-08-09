import sqlite3

DB_NAME = "supermarket.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT UNIQUE NOT NULL,
            Password TEXT NOT NULL,
            Question TEXT NOT NULL,
            Answer TEXT NOT NULL,
            Role TEXT NOT NULL,
            FullName TEXT NOT NULL
        )
    ''')

    # 📦 جدول المنتجات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Barcode TEXT UNIQUE NOT NULL,
            Name TEXT NOT NULL,
            Price REAL NOT NULL,
            Quantity INTEGER NOT NULL,
            Category TEXT DEFAULT 'عام'
        )
    ''')

    # 🧾 جدول الفواتير / المبيعات (جديد)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Total REAL NOT NULL,
            Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    try:
        return sqlite3.connect(DB_NAME)
    except Exception as e:
        print(f"خطأ في الاتصال: {e}")
        return None

# --- دوال المستخدمين ---
def check_login(username, password):
    conn = get_db_connection()
    if not conn: return {"status": False, "message": "فشل الاتصال بـ الداتابيز!"}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Role, FullName FROM Users WHERE Username = ? AND Password = ?", (username, password))
        row = cursor.fetchone()
        if row: return {"status": True, "role": row[0], "name": row[1]}
        else: return {"status": False, "message": "اسم المستخدم أو كلمة المرور غير صحيحة!"}
    finally:
        conn.close()

def register_user(fullname, username, password, question, answer, role="User"):
    conn = get_db_connection()
    if not conn: return False, "فشل الاتصال!"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Users WHERE Username = ?", (username,))
        if cursor.fetchone(): return False, "اسم المستخدم مستخدم بالفعل!"
        cursor.execute('''
            INSERT INTO Users (FullName, Username, Password, Question, Answer, Role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (fullname, username, password, question, answer, role))
        conn.commit()
        return True, "تم إنشاء الحساب بنجاح! 🎉"
    except Exception as e:
        return False, f"خطأ: {str(e)}"
    finally:
        conn.close()

def get_security_question(username):
    conn = get_db_connection()
    if not conn: return False, "فشل الاتصال!"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Question FROM Users WHERE Username = ?", (username,))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False, "اسم المستخدم غير موجود!")
    finally:
        conn.close()

def update_password_with_question(username, answer, new_password):
    conn = get_db_connection()
    if not conn: return False, "فشل الاتصال!"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Answer FROM Users WHERE Username = ?", (username,))
        row = cursor.fetchone()
        if row and row[0].strip().lower() == answer.strip().lower():
            cursor.execute("UPDATE Users SET Password = ? WHERE Username = ?", (new_password, username))
            conn.commit()
            return True, "تم تحديث كلمة المرور بنجاح! 🎉"
        else: return False, "إجابة سؤال الأمان غير صحيحة!"
    finally:
        conn.close()

# --- 📦 دوال إدارة المنتجات ---
def add_product(barcode, name, price, quantity, category="عام"):
    conn = get_db_connection()
    if not conn: return False, "فشل الاتصال!"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Products WHERE Barcode = ?", (barcode,))
        if cursor.fetchone():
            return False, "هذا البار كود مضاف لمنتج آخر بالفعل!"
        
        cursor.execute('''
            INSERT INTO Products (Barcode, Name, Price, Quantity, Category)
            VALUES (?, ?, ?, ?, ?)
        ''', (barcode, name, float(price), int(quantity), category))
        conn.commit()
        return True, "تمت إضافة المنتج للمخزن بنجاح! ✅"
    except Exception as e:
        return False, f"حدث خطأ: {str(e)}"
    finally:
        conn.close()

def get_all_products():
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Barcode, Name, Category, Price, Quantity FROM Products")
        return cursor.fetchall()
    finally:
        conn.close()

def delete_product(barcode):
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Products WHERE Barcode = ?", (barcode,))
        conn.commit()
        return True
    finally:
        conn.close()

# --- 🛒 دوال الكاشير والمبيعات (جديد) ---
def get_product_by_barcode(barcode):
    """البحث عن منتج بالبار كود من أجل الفاتورة"""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Barcode, Name, Price, Quantity FROM Products WHERE Barcode = ?", (barcode,))
        return cursor.fetchone()
    finally:
        conn.close()

def process_sale(cart_items, total_amount):
    """إتمام البيع وخصم الكميات من المخزن"""
    conn = get_db_connection()
    if not conn: return False, "فشل الاتصال!"
    try:
        cursor = conn.cursor()
        # 1. تسجيل العملية في جدول المبيعات
        cursor.execute("INSERT INTO Sales (Total) VALUES (?)", (total_amount,))
        
        # 2. خصم الكمية المبيعة من جدول المنتجات
        for item in cart_items:
            barcode = item['barcode']
            qty_sold = item['qty']
            cursor.execute("UPDATE Products SET Quantity = Quantity - ? WHERE Barcode = ?", (qty_sold, barcode))
            
        conn.commit()
        return True, "تمت عملية البيع وحفظ الفاتورة بنجاح! 🧾🎉"
    except Exception as e:
        return False, f"حدث خطأ أثناء البيع: {str(e)}"
    finally:
        conn.close()