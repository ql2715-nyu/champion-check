import subprocess
import sys


def run_script(script_name):
    print(f"\n正在运行：{script_name}")
    print("-" * 50)

    result = subprocess.run([sys.executable, script_name])

    if result.returncode == 0:
        print(f"\n✅ {script_name} 运行完成")
    else:
        print(f"\n❌ {script_name} 运行失败，请检查上面的错误信息")


def main():
    while True:
        print("\n========== Champion Check System ==========")
        print("1. 初始化 SQLite 数据库 (Initialize Database)")
        print("2. 导入活动方案数据 (Import Plan Data)")
        print("3. 导入门店数据 (Import Store Data)")
        print("4. 生成实际价格填写模板 (Generate Actual Price Template)")
        print("5. 导入实际价格数据 (Import Actual Price Data)")
        print("6. 生成差异报告 (Generate Discrepancy Report)")
        print("7. 退出 (Exit)")
        print("==========================================")

        choice = input("请输入选项 / Enter option: ").strip()

        if choice == "1":
            run_script("init_sqlite_db.py")
        elif choice == "2":
            run_script("import_plan_sqlite.py")
        elif choice == "3":
            run_script("import_store_sqlite.py")
        elif choice == "4":
            run_script("generate_actual_price_template_sqlite.py")
        elif choice == "5":
            run_script("import_actual_price_sqlite.py")
        elif choice == "6":
            run_script("export_discrepancy_report_sqlite.py")
        elif choice == "7":
            print("已退出 / Exited Champion Check System")
            break
        else:
            print("无效选项，请输入 1-7 / Invalid option, please enter 1-7")


if __name__ == "__main__":
    main()