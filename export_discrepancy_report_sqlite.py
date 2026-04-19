import sqlite3
import pandas as pd
import os

# ======================================
# 1. 连接数据库
# ======================================
conn = sqlite3.connect("champion_check.db")

# ======================================
# 2. 获取最新 campaign
# ======================================
campaign_df = pd.read_sql("""
SELECT campaign_id, campaign_name
FROM campaign
ORDER BY campaign_id DESC
LIMIT 1
""", conn)

if campaign_df.empty:
    raise Exception("没有找到 campaign，请先导入方案")

campaign_id = campaign_df.iloc[0]["campaign_id"]
campaign_name = campaign_df.iloc[0]["campaign_name"]

print("当前活动：", campaign_name)

# ======================================
# 3. 读取 plan（标准答案）
# ======================================
plan_df = pd.read_sql(f"""
SELECT
    plan_id,
    campaign_id,
    sku,
    product_name,
    category_name,
    promo_price,
    trial_price
FROM planned_product_price
WHERE campaign_id = {campaign_id}
""", conn)

# ======================================
# 4. 读取 actual
# ======================================
actual_df = pd.read_sql(f"""
SELECT
    a.actual_price_id,
    a.campaign_id,
    a.store_id,
    a.sku,
    a.product_name,
    a.platform_id,
    a.actual_price,
    a.actual_trial_price,
    s.store_name,
    p.platform_name
FROM actual_price a
JOIN store s ON a.store_id = s.store_id
JOIN platform p ON a.platform_id = p.platform_id
WHERE a.campaign_id = {campaign_id}
""", conn)

# ======================================
# 5. 先按 SKU 匹配
# ======================================
plan_with_sku = plan_df[plan_df["sku"].notna()].copy()
actual_with_sku = actual_df[actual_df["sku"].notna()].copy()

merged_sku = pd.merge(
    actual_with_sku,
    plan_with_sku,
    on=["campaign_id", "sku"],
    how="right",
    suffixes=("_actual", "_plan")
)

# ======================================
# 6. 再按 product_name 匹配（只处理没有 SKU 的 plan）
# ======================================
plan_no_sku = plan_df[plan_df["sku"].isna()].copy()

merged_name = pd.merge(
    actual_df,
    plan_no_sku,
    on=["campaign_id", "product_name"],
    how="right",
    suffixes=("_actual", "_plan")
)

# ======================================
# 7. 合并两部分结果
# ======================================
merged = pd.concat([merged_sku, merged_name], ignore_index=True)

# ======================================
# 8. 问题判断逻辑（以 plan 为标准）
# ======================================
def check_issue(row):
    issues = []

    # 计划有活动价，但实际没有
    if pd.notna(row["promo_price"]) and pd.isna(row["actual_price"]):
        issues.append("缺少实际活动价")

    # 计划有活动价，实际也有，但不一致
    elif pd.notna(row["promo_price"]) and pd.notna(row["actual_price"]):
        if abs(float(row["actual_price"]) - float(row["promo_price"])) > 0.01:
            issues.append("活动价不一致")

    # 计划有尝新价，但实际没有
    if pd.notna(row["trial_price"]) and pd.isna(row["actual_trial_price"]):
        issues.append("缺少实际尝新价")

    # 计划有尝新价，实际也有，但不一致
    elif pd.notna(row["trial_price"]) and pd.notna(row["actual_trial_price"]):
        if abs(float(row["actual_trial_price"]) - float(row["trial_price"])) > 0.01:
            issues.append("尝新价不一致")

    return "；".join(issues)

merged["issue"] = merged.apply(check_issue, axis=1)

# 只保留有问题的
report = merged[merged["issue"] != ""].copy()

# ======================================
# 9. 整理输出列
# ======================================
report_output = report[
    [
        "store_name",
        "platform_name",
        "sku",
        "product_name",
        "promo_price",
        "actual_price",
        "trial_price",
        "actual_trial_price",
        "issue"
    ]
].copy()

report_output.columns = [
    "门店名称",
    "平台",
    "SKU",
    "商品名称",
    "计划活动价",
    "实际活动价",
    "计划尝新价",
    "实际尝新价",
    "问题类型"
]

print("\n问题记录数：", len(report_output))
print(report_output.head(20))

# ======================================
# 10. 输出 Excel
# ======================================
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

file_name = f"discrepancy_report_{campaign_name}.xlsx"
output_path = os.path.join(output_dir, file_name)

report_output.to_excel(output_path, index=False)

print("\n✅ 差异报告已生成：")
print(output_path)

# ======================================
# 11. 关闭连接
# ======================================
conn.close()
print("数据库连接已关闭")