import sqlite3
import os

DB_FILE = "champion_check.db"

# 如果你想每次重新初始化数据库，就先删掉旧文件
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print(f"已删除旧数据库：{DB_FILE}")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 开启外键支持
cursor.execute("PRAGMA foreign_keys = ON;")

# ======================================
# 1. 创建 campaign 表
# ======================================
cursor.execute("""
CREATE TABLE campaign (
    campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name TEXT NOT NULL,
    launch_date TEXT,
    source_file TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")

# ======================================
# 2. 创建 planned_product_price 表
# ======================================
cursor.execute("""
CREATE TABLE planned_product_price (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    category_name TEXT,
    product_name TEXT,
    product_description TEXT,
    original_price REAL,
    promo_price_text TEXT,
    promo_price REAL,
    box_fee REAL,
    remark TEXT,
    sku TEXT,
    trial_price REAL,
    FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id)
);
""")

# ======================================
# 3. 创建 store 表
# ======================================
cursor.execute("""
CREATE TABLE store (
    store_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name TEXT,
    store_short_name TEXT,
    meituan_id TEXT,
    eleme_id TEXT,
    jd_id TEXT,
    city TEXT
);
""")

# ======================================
# 4. 创建 platform 表
# ======================================
cursor.execute("""
CREATE TABLE platform (
    platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT NOT NULL
);
""")

# ======================================
# 5. 创建 actual_price 表
# 这里我先加上 product_name，方便以后支持“无 SKU 按名称比”
# ======================================
cursor.execute("""
CREATE TABLE actual_price (
    actual_price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    sku TEXT,
    product_name TEXT,
    platform_id INTEGER NOT NULL,
    actual_price REAL,
    actual_trial_price REAL,
    check_time TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id),
    FOREIGN KEY (store_id) REFERENCES store(store_id),
    FOREIGN KEY (platform_id) REFERENCES platform(platform_id)
);
""")

# ======================================
# 6. 插入 platform 初始数据
# ======================================
cursor.executemany("""
INSERT INTO platform (platform_name)
VALUES (?)
""", [
    ("美团外卖",),
    ("饿了么",),
    ("京东",)
])

conn.commit()

print("SQLite 数据库初始化完成：champion_check.db")

# 检查表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("已创建的表：")
for t in tables:
    print("-", t[0])

# 检查 platform 数据
cursor.execute("SELECT * FROM platform;")
platforms = cursor.fetchall()
print("\nplatform 初始数据：")
for p in platforms:
    print(p)

cursor.close()
conn.close()
print("\n数据库连接已关闭")