import os
import pandas as pd
import sqlite3

# ======================================
# 1. demo 文件路径
# ======================================
file_path = "output/actual_price_template_Demo Campaign.xlsx"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"找不到 actual price 文件：{file_path}")

print("正在读取 actual price 文件：", file_path)

# ======================================
# 2. 读取 Excel
# ======================================
df = pd.read_excel(file_path)

print("\n原始列名：")
print(df.columns.tolist())

# ======================================
# 3. 只保留真正填写了价格的行
# 只要活动价或尝新价其中一个填写了，就导入
# ======================================
df = df[
    df["actual_price"].notna() | df["actual_trial_price"].notna()
].copy()

print("\n实际填写的行数：", len(df))
print(df.head())

# ======================================
# 4. 连接 SQLite
# ======================================
conn = sqlite3.connect("champion_check.db")
cursor = conn.cursor()

# ======================================
# 5. 获取最新 campaign_id
# ======================================
cursor.execute("""
SELECT campaign_id
FROM campaign
ORDER BY campaign_id DESC
LIMIT 1
""")

result = cursor.fetchone()
if result is None:
    raise Exception("没有找到 campaign，请先导入方案")

campaign_id = result[0]
print("\n当前 campaign_id：", campaign_id)

# ======================================
# 6. 建立 store_name -> store_id 映射
# ======================================
cursor.execute("SELECT store_id, store_name FROM store")
store_map = {row[1]: row[0] for row in cursor.fetchall()}

# ======================================
# 7. 建立 platform_name -> platform_id 映射
# ======================================
cursor.execute("SELECT platform_id, platform_name FROM platform")
platform_map = {row[1]: row[0] for row in cursor.fetchall()}

# ======================================
# 8. 插入 actual_price
# ======================================
insert_sql = """
INSERT INTO actual_price (
    campaign_id,
    store_id,
    sku,
    product_name,
    platform_id,
    actual_price,
    actual_trial_price
)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

success_count = 0

for _, row in df.iterrows():
    store_name = row["store_name"]
    platform_name = row["platform_name"]
    sku = row["sku"] if pd.notna(row["sku"]) else None
    product_name = row["product_name"] if pd.notna(row["product_name"]) else None
    actual_price = float(row["actual_price"]) if pd.notna(row["actual_price"]) else None
    actual_trial_price = float(row["actual_trial_price"]) if pd.notna(row["actual_trial_price"]) else None

    store_id = store_map.get(store_name)
    platform_id = platform_map.get(platform_name)

    if store_id is None:
        print(f"⚠️ 找不到门店：{store_name}")
        continue

    if platform_id is None:
        print(f"⚠️ 找不到平台：{platform_name}")
        continue

    cursor.execute(insert_sql, (
        campaign_id,
        store_id,
        sku,
        product_name,
        platform_id,
        actual_price,
        actual_trial_price
    ))

    success_count += 1

conn.commit()

print(f"\n✅ actual_price 插入成功，共 {success_count} 条")

# ======================================
# 9. 关闭连接
# ======================================
cursor.close()
conn.close()

print("数据库连接已关闭")