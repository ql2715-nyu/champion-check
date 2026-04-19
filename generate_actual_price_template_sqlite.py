import sqlite3
import pandas as pd
import os

# ======================================
# 1. 连接数据库
# ======================================
conn = sqlite3.connect("champion_check.db")

# ======================================
# 2. 读取最新 campaign
# ======================================
query_campaign = """
SELECT campaign_id, campaign_name
FROM campaign
ORDER BY campaign_id DESC
LIMIT 1
"""

campaign_df = pd.read_sql(query_campaign, conn)

if campaign_df.empty:
    raise Exception("没有找到 campaign，请先导入方案")

campaign_id = campaign_df.iloc[0]["campaign_id"]
campaign_name = campaign_df.iloc[0]["campaign_name"]

print("当前活动：", campaign_name)

# ======================================
# 3. 读取 plan 数据
# ======================================
query_plan = f"""
SELECT sku, product_name
FROM planned_product_price
WHERE campaign_id = {campaign_id}
"""

plan_df = pd.read_sql(query_plan, conn)

# ======================================
# 4. 读取 store
# ======================================
store_df = pd.read_sql("SELECT store_name FROM store", conn)

# ======================================
# 5. 读取 platform
# ======================================
platform_df = pd.read_sql("SELECT platform_name FROM platform", conn)

# ======================================
# 6. 生成模板（笛卡尔积）
# ======================================
template = store_df.assign(key=1)\
    .merge(platform_df.assign(key=1), on="key")\
    .merge(plan_df.assign(key=1), on="key")\
    .drop("key", axis=1)

# ======================================
# 7. 添加需要填写的列
# ======================================
template["actual_price"] = ""
template["actual_trial_price"] = ""

# 调整列顺序
template = template[
    [
        "store_name",
        "platform_name",
        "sku",
        "product_name",
        "actual_price",
        "actual_trial_price"
    ]
]

# ======================================
# 8. 输出文件
# ======================================
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

file_name = f"actual_price_template_{campaign_name}.xlsx"
output_path = os.path.join(output_dir, file_name)

template.to_excel(output_path, index=False)

print("\n✅ 模板生成成功：")
print(output_path)

conn.close()