import os
import pandas as pd
import sqlite3


# ======================================
# 0. 工具函数
# ======================================
def normalize_text(text):
    if pd.isna(text):
        return ""
    return str(text).replace("\n", "").replace(" ", "").strip().lower()


def find_header_row(file_path, max_rows=10):
    """
    扫描前几行，找到最像表头的一行
    """
    preview = pd.read_excel(file_path, sheet_name=0, header=None, nrows=max_rows)

    header_keywords = [
        "分类名称", "分类", "品类",
        "产品名称", "菜品名称", "商品名称", "名称",
        "商品描述", "菜品内容", "内容", "描述",
        "原价", "门市价", "吊牌价",
        "美外饿了么京东小程序活动价", "活动价", "售价", "售价格", "卖价",
        "餐盒费", "打包费", "包装费",
        "备注", "说明",
        "sku", "SKU", "商品编码", "单品编码", "编码"
    ]

    best_row = 0
    best_score = -1

    for i in range(len(preview)):
        row_values = [normalize_text(x) for x in preview.iloc[i].tolist()]
        score = 0
        for cell in row_values:
            for kw in header_keywords:
                if normalize_text(kw) in cell:
                    score += 1
        if score > best_score:
            best_score = score
            best_row = i

    return best_row


def find_column(columns, keywords):
    """
    按同义词匹配列名
    """
    normalized_map = {col: normalize_text(col) for col in columns}

    for keyword in keywords:
        keyword_norm = normalize_text(keyword)
        for col, col_norm in normalized_map.items():
            if keyword_norm == col_norm or keyword_norm in col_norm:
                return col

    return None


# ======================================
# 1. demo 固定输入
# ======================================
file_path = "sample_data/demo_plan.xlsx"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"找不到 demo 文件：{file_path}")

campaign_name = "Demo Campaign"
launch_date = "2026-04-14"
source_file = os.path.basename(file_path)

print("正在读取 demo 文件：", file_path)

# ======================================
# 2. 自动识别表头行
# ======================================
header_row = find_header_row(file_path)
print(f"\n识别到表头行：第 {header_row + 1} 行")

# ======================================
# 3. 读取 Excel
# ======================================
df = pd.read_excel(file_path, sheet_name=0, header=header_row)

print("\n原始列名：")
print(df.columns.tolist())

# ======================================
# 4. 自动识别列
# ======================================
category_col = find_column(df.columns, ["分类名称", "分类", "品类"])
product_col = find_column(df.columns, ["产品名称", "菜品名称", "商品名称", "名称"])
desc_col = find_column(df.columns, ["商品描述", "菜品内容", "内容", "描述"])
original_price_col = find_column(df.columns, ["原价", "门市价", "吊牌价"])
promo_col = find_column(df.columns, ["美外饿了么京东小程序活动价", "活动价", "售价", "售价格", "卖价"])
box_fee_col = find_column(df.columns, ["餐盒费", "打包费", "包装费"])
remark_col = find_column(df.columns, ["备注", "说明"])
sku_col = find_column(df.columns, ["sku", "SKU", "商品编码", "单品编码", "编码"])

print("\n识别到的关键列：")
print("分类列：", category_col)
print("商品名称列：", product_col)
print("描述列：", desc_col)
print("原价列：", original_price_col)
print("价格列：", promo_col)
print("餐盒费列：", box_fee_col)
print("备注列：", remark_col)
print("SKU列：", sku_col)

# 必须字段检查（SKU 不再强制）
if product_col is None:
    raise Exception("找不到商品名称列，请检查表头")
if original_price_col is None:
    raise Exception("找不到原价列，请检查表头")
if promo_col is None:
    raise Exception("找不到活动价/售价列，请检查表头")

# 非必须字段兜底
if category_col is None:
    df["临时分类列"] = None
    category_col = "临时分类列"

if desc_col is None:
    df["临时描述列"] = None
    desc_col = "临时描述列"

if box_fee_col is None:
    df["临时餐盒费列"] = None
    box_fee_col = "临时餐盒费列"

if remark_col is None:
    df["临时备注列"] = None
    remark_col = "临时备注列"

if sku_col is None:
    df["临时SKU列"] = None
    sku_col = "临时SKU列"
    print("\n⚠️ 未找到 SKU 列，本次将按商品名称保留数据，后续比对时需支持名称匹配。")

# ======================================
# 5. 只保留需要的列
# ======================================
df = df[
    [
        category_col,
        product_col,
        desc_col,
        original_price_col,
        promo_col,
        box_fee_col,
        remark_col,
        sku_col,
    ]
].copy()

# 统一列名
df.columns = [
    "分类名称",
    "产品名称",
    "商品描述",
    "原价",
    "活动价原始列",
    "餐盒费",
    "备注",
    "sku",
]

# ======================================
# 6. 清洗数据
# ======================================
# 如果有 SKU 列，就清洗；如果没有，保持为空
df["sku"] = df["sku"].where(df["sku"].notna(), None)

if df["sku"].notna().any():
    df["sku"] = (
        df["sku"]
        .astype(str)
        .str.replace("单品：", "", regex=False)
        .str.replace("单品:", "", regex=False)
        .str.strip()
    )
    df["sku"] = df["sku"].replace({"": None, "nan": None, "None": None})

# 填充分类名称（处理合并单元格）
df["分类名称"] = df["分类名称"].ffill()

# 保留原始价格文本
df["promo_price_text"] = df["活动价原始列"].astype(str).str.strip()

# 提取尝新价
df["trial_price"] = df["promo_price_text"].str.extract(
    r"尝新价[:：]?\s*(\d+(?:\.\d+)?)",
    expand=False
)

# 提取常规价
df["regular_price"] = df["promo_price_text"].str.extract(
    r"常规价[:：]?\s*(\d+(?:\.\d+)?)",
    expand=False
)

# 转数值
df["trial_price"] = pd.to_numeric(df["trial_price"], errors="coerce")
df["regular_price"] = pd.to_numeric(df["regular_price"], errors="coerce")

# 单一活动价（兼容 33.9起 这类格式）
single_price = df["promo_price_text"].str.extract(
    r"(\d+(?:\.\d+)?)",
    expand=False
)
single_price = pd.to_numeric(single_price, errors="coerce")

# promo_price 规则：
# 有常规价 → 用常规价
# 没有常规价 → 用单一活动价
df["promo_price"] = df["regular_price"].fillna(single_price)

# 原价、餐盒费转数值
df["原价"] = pd.to_numeric(df["原价"], errors="coerce")
df["餐盒费"] = pd.to_numeric(df["餐盒费"], errors="coerce")

# 只保留真正主商品：
# 必须同时有 产品名称、原价、promo_price
df = df[
    df["产品名称"].notna() &
    df["原价"].notna() &
    df["promo_price"].notna()
].copy()

# 去掉“仅用于...”的辅助商品
df = df[~df["备注"].astype(str).str.contains("仅用于", na=False)].copy()

# 清理换行
df["分类名称"] = df["分类名称"].astype(str).str.replace("\n", " ", regex=False)
df["商品描述"] = df["商品描述"].astype(str).str.replace("\n", " ", regex=False)

# 重命名为数据库字段
df = df.rename(columns={
    "分类名称": "category_name",
    "产品名称": "product_name",
    "商品描述": "product_description",
    "原价": "original_price",
    "餐盒费": "box_fee",
    "备注": "remark",
    "sku": "sku"
})

# 最终入库表
df_final = df[
    [
        "category_name",
        "product_name",
        "product_description",
        "original_price",
        "promo_price_text",
        "promo_price",
        "trial_price",
        "box_fee",
        "remark",
        "sku",
    ]
].copy()

print("\n清洗后的数据预览：")
print(df_final[["sku", "product_name", "promo_price_text", "promo_price", "trial_price"]].head(20))
print("\n总行数：", len(df_final))

# ======================================
# 7. 连接 SQLite
# ======================================
conn = sqlite3.connect("champion_check.db")
cursor = conn.cursor()

# ======================================
# 8. 插入 campaign
# ======================================
insert_campaign_sql = """
INSERT INTO campaign (campaign_name, launch_date, source_file)
VALUES (?, ?, ?)
"""

cursor.execute(insert_campaign_sql, (campaign_name, launch_date, source_file))
conn.commit()

campaign_id = cursor.lastrowid
print("\ncampaign 创建成功，ID =", campaign_id)

# ======================================
# 9. 插入 planned_product_price
# ======================================
insert_plan_sql = """
INSERT INTO planned_product_price (
    campaign_id,
    category_name,
    product_name,
    product_description,
    original_price,
    promo_price_text,
    promo_price,
    box_fee,
    remark,
    sku,
    trial_price
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

for _, row in df_final.iterrows():
    values = (
        campaign_id,
        None if pd.isna(row["category_name"]) else row["category_name"],
        None if pd.isna(row["product_name"]) else row["product_name"],
        None if pd.isna(row["product_description"]) else row["product_description"],
        None if pd.isna(row["original_price"]) else float(row["original_price"]),
        None if pd.isna(row["promo_price_text"]) else row["promo_price_text"],
        None if pd.isna(row["promo_price"]) else float(row["promo_price"]),
        None if pd.isna(row["box_fee"]) else float(row["box_fee"]),
        None if pd.isna(row["remark"]) else row["remark"],
        None if pd.isna(row["sku"]) else row["sku"],
        None if pd.isna(row["trial_price"]) else float(row["trial_price"]),
    )
    cursor.execute(insert_plan_sql, values)

conn.commit()

print("planned_product_price 插入成功，共", len(df_final), "条")

# ======================================
# 10. 关闭连接
# ======================================
cursor.close()
conn.close()

print("数据库连接已关闭")