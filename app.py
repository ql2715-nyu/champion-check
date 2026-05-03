import streamlit as st
import subprocess
import sys

# ===============================
# 页面标题
# ===============================
st.title("Champion Check System")
st.subheader("价格校验系统 / Price Validation System")

# ===============================
# 运行脚本函数
# ===============================
def run_script(script_name):
    st.write(f"正在运行 / Running: {script_name}")

    result = subprocess.run([sys.executable, script_name])

    if result.returncode == 0:
        st.success(f"{script_name} 运行成功 / Finished successfully")
    else:
        st.error(f"{script_name} 运行失败 / Failed")

# ===============================
# 操作区
# ===============================
st.header("系统操作 / System Operations")

if st.button("1️⃣ 初始化数据库 (Initialize Database)"):
    run_script("init_sqlite_db.py")

if st.button("2️⃣ 导入活动方案 (Import Plan Data)"):
    run_script("import_plan_sqlite.py")

if st.button("3️⃣ 导入门店数据 (Import Store Data)"):
    run_script("import_store_sqlite.py")

if st.button("4️⃣ 生成实际价格模板 (Generate Template)"):
    run_script("generate_actual_price_template_sqlite.py")

if st.button("5️⃣ 导入实际价格 (Import Actual Data)"):
    run_script("import_actual_price_sqlite.py")

if st.button("6️⃣ 生成差异报告 (Generate Report)"):
    run_script("export_discrepancy_report_sqlite.py")

# ===============================
# 说明
# ===============================
st.markdown("---")
st.caption("Demo System - Champion Check | Capstone Project")