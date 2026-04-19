import os
import pandas as pd
import sqlite3


# ======================================
# 1. demo 文件路径
# ======================================
file_path = "sample_data/demo_store.xlsx"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"找不到 demo 门店文件：{file_path}")

print("正在读取门店文件：", file_path)

# ======================================
# 2. 读取 Excel
# ======================================
df = pd.read_excel(file_path)

print("\n原始列名：")
print(df.columns.tolist())


# ======================================
# 3. 自动识别列（更稳）
# ======================================
def find_column(columns, keywords):
    for col in columns:
        for kw in keywords:
            if kw in str(col):
                return col
    return None


store_name_col = find_column(df.columns, ["门店名称", "店铺名称", "门店"])
city_col = find_column(df.columns, ["城市"])

short_name_col = find_column(df.columns, ["简称"])
meituan_col = find_column(df.columns, ["美团"])
eleme_col = find_column(df.columns, ["饿了么"])
jd_col = find_column(df.columns, ["京东"])


print("\n识别到的列：")
print("门店名称：", store_name_col)
print("城市：", city_col)

# ======================================
# 4. 必须字段检查
# ======================================
if store_name_col is None:
    raise Exception("❌ 找不到门店名称列，请检查 Excel")

# ======================================
# 5. 构建数据
# ======================================
df_clean = pd.DataFrame()

df_clean["store_name"] = df[store_name_col]
df_clean["city"] = df[city_col] if city_col else None

# 可选字段（没有就设 None）
df_clean["store_short_name"] = df[short_name_col] if short_name_col else None
df_clean["meituan_id"] = df[meituan_col] if meituan_col else None
df_clean["eleme_id"] = df[eleme_col] if eleme_col else None
df_clean["jd_id"] = df[jd_col] if jd_col else None

# 删除空行
df_clean = df_clean[df_clean["store_name"].notna()]

print("\n清洗后的数据：")
print(df_clean.head())
print("\n总门店数：", len(df_clean))


# ======================================
# 6. 连接 SQLite
# ======================================
conn = sqlite3.connect("champion_check.db")
cursor = conn.cursor()


# ======================================
# 7. 插入数据
# ======================================
insert_sql = """
INSERT INTO store (
    store_name,
    store_short_name,
    meituan_id,
    eleme_id,
    jd_id,
    city
)
VALUES (?, ?, ?, ?, ?, ?)
"""

for _, row in df_clean.iterrows():
    cursor.execute(insert_sql, (
        row["store_name"],
        row["store_short_name"],
        row["meituan_id"],
        row["eleme_id"],
        row["jd_id"],
        row["city"]
    ))

conn.commit()

print("\n✅ store 表插入成功，共", len(df_clean), "条")


# ======================================
# 8. 关闭连接
# ======================================
cursor.close()
conn.close()

print("数据库连接已关闭")