import json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

# -----------------------------
# UIキー生成（衝突しない命名規約）
# -----------------------------
def ui_key(path: str) -> str:
    # 例: "robot.items.0.name" -> "ui.robot.items.0.name"
    return f"ui.{path}"

# -----------------------------
# デフォルトパラメータ（必要に応じて拡張）
# -----------------------------
def default_params() -> dict:
    return {
        "robot": {
            "num_types": 2,
            "items": [
                {"name": "ロボホン", "price": 230_000,
                 "commission_rate": 0.10, "purchase_rate": 0.03,
                 "release_month": 0,
                },
                {"name": "ポケとも", "price": 39_000,
                 "commission_rate": 0.10, "purchase_rate": 0.09,
                 "release_month": 10,
                }
            ]
        },
        "app": {
            "monthly_fee": 300,
            "free_months": 3,
            "churn_rate": 0.03,
        },
        # --- 追加：cloud（クラウド閾値） ---
        "cloud": {
            "initial_cost": 350,
            "bugfix_cost": 100,
            "num_thresholds": 4,
            "thresholds": [300, 1000, 3000, 10000],
            "scale_costs": [100, 150, 200, 300],  # 万円で保持
            "aws_cost_per_user_month": 50,
        },
        # 販売会社（増加数）
        "dealer":{
            "initial_companies": 1,
            "max_companies": 50,
            "fixed_months_before_growth": 6,
            "company_growth_per_month": 2,
        },
        # アプリ開発・ロボットI/F開発・不具合修正支出
        "develop":{
            "android_dev_initial": 450,
            "ios_dev_initial": 650,
            "ios_dev_month": 12,
            "robot_if_dev":250,
            "android_bugfix_cost": 100,
            "ios_bugfix_cost": 100,
            "bugfix_cycle_months": 6,
        } ,
        # 販売店向けロボット・販売ツール
        "tool":{
            "robot_unit_cost": 230_000 + 39_000,
            "sales_tool_cost_per_shop": 20,
            "robots_per_shop": 3,
        },
        # カスタマーサポート
        "sport":{
            "cs_cost_per_user_month": 10,
        },
        # 事業体人件費
        "labor":{
            "base_fte": 1,
            "fte_cost_per_month": 120,
            "base_users": 2000,
            "fte_increment_users": 4000,
            "fte_increment": 0.5,
        }
    }

# -----------------------------
# session_state 初期化（setdefault: 既存値を壊さない）
# ※ウィジェット生成前に呼ぶ
# -----------------------------
def init_state_from_params(params: dict) -> None:
    # robot
    st.session_state.setdefault(ui_key("robot.num_types"), int(params["robot"]["num_types"]))
    for i, r in enumerate(params["robot"]["items"]):
        st.session_state.setdefault(ui_key(f"robot.items.{i}.name"), r["name"])
        st.session_state.setdefault(ui_key(f"robot.items.{i}.price"), int(r["price"]))
        st.session_state.setdefault(ui_key(f"robot.items.{i}.commission_rate_pct"), float(r["commission_rate"]) * 100.0)
        st.session_state.setdefault(ui_key(f"robot.items.{i}.purchase_rate_pct"), float(r["purchase_rate"]) * 100.0)
        st.session_state.setdefault(ui_key(f"robot.items.{i}.release_month"), int(r["release_month"]))

    # app
    st.session_state.setdefault(ui_key("app.monthly_fee"), int(params["app"]["monthly_fee"]))
    st.session_state.setdefault(ui_key("app.free_months"), int(params["app"]["free_months"]))
    st.session_state.setdefault(ui_key("app.churn_rate_pct"), float(params["app"]["churn_rate"]) * 100.0)

    # --- 追加：cloud ---
    cloud = params.get("cloud", {})
    st.session_state.setdefault(ui_key("cloud.initial_cost"), int(cloud.get("initial_cost", 0)))
    st.session_state.setdefault(ui_key("cloud.bugfix_cost"), int(cloud.get("bugfix_cost", 0)))
    st.session_state.setdefault(ui_key("cloud.num_thresholds"), int(cloud.get("num_thresholds", 0)))
    st.session_state.setdefault(ui_key("cloud.aws_cost_per_user_month"), int(cloud.get("aws_cost_per_user_month", 0)))

    ths = cloud.get("thresholds", [])
    costs = cloud.get("scale_costs", [])

    n = int(st.session_state[ui_key("cloud.num_thresholds")])
    for i in range(n):
        st.session_state.setdefault(ui_key(f"cloud.thresholds.{i}"), int(ths[i] if i < len(ths) else 0))
        st.session_state.setdefault(ui_key(f"cloud.scale_costs.{i}"), int(costs[i] if i < len(costs) else 0))

    # -----------------------------
    # dealer
    # -----------------------------
    dealer = params.get("dealer", {})
    st.session_state.setdefault(ui_key("dealer.initial_companies"), int(dealer.get("initial_companies", 1)))
    st.session_state.setdefault(ui_key("dealer.max_companies"), int(dealer.get("max_companies", 1)))
    st.session_state.setdefault(ui_key("dealer.fixed_months_before_growth"), int(dealer.get("fixed_months_before_growth", 0)))
    st.session_state.setdefault(ui_key("dealer.company_growth_per_month"), int(dealer.get("company_growth_per_month", 0)))

    # -----------------------------
    # develop  （単位：万円で保持している想定）
    # -----------------------------
    develop = params.get("develop", {})
    st.session_state.setdefault(ui_key("develop.android_dev_initial"), int(develop.get("android_dev_initial", 0)))
    st.session_state.setdefault(ui_key("develop.ios_dev_initial"), int(develop.get("ios_dev_initial", 0)))
    st.session_state.setdefault(ui_key("develop.ios_dev_month"), int(develop.get("ios_dev_month", 0)))
    st.session_state.setdefault(ui_key("develop.robot_if_dev"), int(develop.get("robot_if_dev", 0)))
    st.session_state.setdefault(ui_key("develop.android_bugfix_cost"), int(develop.get("android_bugfix_cost", 0)))
    st.session_state.setdefault(ui_key("develop.ios_bugfix_cost"), int(develop.get("ios_bugfix_cost", 0)))
    st.session_state.setdefault(ui_key("develop.bugfix_cycle_months"), int(develop.get("bugfix_cycle_months", 1)))

    # -----------------------------
    # tool  （単位：万円で保持している想定。ただし robot_unit_cost は円で持っている）
    # -----------------------------
    tool = params.get("tool", {})
    st.session_state.setdefault(ui_key("tool.robot_unit_cost"), int(tool.get("robot_unit_cost", 0)))  # 円
    st.session_state.setdefault(ui_key("tool.sales_tool_cost_per_shop"), int(tool.get("sales_tool_cost_per_shop", 0)))  # 万円
    st.session_state.setdefault(ui_key("tool.robots_per_shop"), int(tool.get("robots_per_shop", 0)))

    # -----------------------------
    # sport（= support の typo のまま踏襲） 単位：円/月
    # -----------------------------
    sport = params.get("sport", {})
    st.session_state.setdefault(ui_key("sport.cs_cost_per_user_month"), int(sport.get("cs_cost_per_user_month", 0)))

    # -----------------------------
    # labor  （単位：fte_cost_per_month は万円で保持している想定）
    # -----------------------------
    labor = params.get("labor", {})
    st.session_state.setdefault(ui_key("labor.base_fte"), float(labor.get("base_fte", 0)))
    st.session_state.setdefault(ui_key("labor.fte_cost_per_month"), int(labor.get("fte_cost_per_month", 0)))
    st.session_state.setdefault(ui_key("labor.base_users"), int(labor.get("base_users", 0)))
    st.session_state.setdefault(ui_key("labor.fte_increment_users"), int(labor.get("fte_increment_users", 1)))
    st.session_state.setdefault(ui_key("labor.fte_increment"), float(labor.get("fte_increment", 0.0)))

# -----------------------------
# session_state -> params（内部表現に正規化）
# -----------------------------
def build_params_from_state() -> dict:
    num = int(st.session_state[ui_key("robot.num_types")])
    items = []
    for i in range(num):
        items.append({
            "name": st.session_state.get(ui_key(f"robot.items.{i}.name"), f"No{i+1}"),
            "price": int(st.session_state.get(ui_key(f"robot.items.{i}.price"), 230_000)),
            "commission_rate": float(st.session_state.get(ui_key(f"robot.items.{i}.commission_rate_pct"), 10.0)) / 100.0,
            "purchase_rate": float(st.session_state.get(ui_key(f"robot.items.{i}.purchase_rate_pct"), 3.0)) / 100.0,
            "release_month": int(st.session_state.get(ui_key(f"robot.items.{i}.release_month"), 0)),
        })

    # --- 追加：cloud ---
    n = int(st.session_state.get(ui_key("cloud.num_thresholds"), 0))
    thresholds = []
    scale_costs = []
    for i in range(n):
        thresholds.append(int(st.session_state.get(ui_key(f"cloud.thresholds.{i}"), 0)))
        scale_costs.append(int(st.session_state.get(ui_key(f"cloud.scale_costs.{i}"), 0)))

    params = {
        "robot": {"num_types": num, "items": items},
        "app": {
            "monthly_fee": int(st.session_state[ui_key("app.monthly_fee")]),
            "free_months": int(st.session_state[ui_key("app.free_months")]),
            "churn_rate": float(st.session_state[ui_key("app.churn_rate_pct")]) / 100.0,
        },
        # --- 追加：cloud ---
        "cloud": {
            "initial_cost": int(st.session_state[ui_key("cloud.initial_cost")]),
            "bugfix_cost": int(st.session_state[ui_key("cloud.bugfix_cost")]),
            "num_thresholds": n,
            "thresholds": thresholds,
            "scale_costs": scale_costs,
            "aws_cost_per_user_month": int(st.session_state[ui_key("cloud.aws_cost_per_user_month")]),
        },
        # 販売会社（増加数）
        "dealer": {
            "initial_companies": int(st.session_state.get(ui_key("dealer.initial_companies"), 1)),
            "max_companies": int(st.session_state.get(ui_key("dealer.max_companies"), 1)),
            "fixed_months_before_growth": int(st.session_state.get(ui_key("dealer.fixed_months_before_growth"), 0)),
            "company_growth_per_month": int(st.session_state.get(ui_key("dealer.company_growth_per_month"), 0)),
        },
        # アプリ開発・不具合修正支出
        "develop": {
            "android_dev_initial": int(st.session_state.get(ui_key("develop.android_dev_initial"), 0)),
            "ios_dev_initial": int(st.session_state.get(ui_key("develop.ios_dev_initial"), 0)),
            "ios_dev_month": int(st.session_state.get(ui_key("develop.ios_dev_month"), 0)),
            "robot_if_dev": int(st.session_state.get(ui_key("develop.robot_if_dev"), 0)),
            "android_bugfix_cost": int(st.session_state.get(ui_key("develop.android_bugfix_cost"), 0)),
            "ios_bugfix_cost": int(st.session_state.get(ui_key("develop.ios_bugfix_cost"), 0)),
            "bugfix_cycle_months": int(st.session_state.get(ui_key("develop.bugfix_cycle_months"), 1)),
        },
        # 販売店向けロボット・販売ツール
        "tool": {
            "robot_unit_cost": int(st.session_state.get(ui_key("tool.robot_unit_cost"), 0)),  # 円
            "sales_tool_cost_per_shop": int(
                st.session_state.get(ui_key("tool.sales_tool_cost_per_shop"), 0)),  # 円
            "robots_per_shop": int(st.session_state.get(ui_key("tool.robots_per_shop"), 0)),
        },
        # カスタマーサポート
        "sport": {
            "cs_cost_per_user_month": int(st.session_state.get(ui_key("sport.cs_cost_per_user_month"), 0)),
        },
        # 事業体人件費
        "labor": {
            "base_fte": float(st.session_state.get(ui_key("labor.base_fte"), 0.0)),
            "fte_cost_per_month": int(st.session_state.get(ui_key("labor.fte_cost_per_month"), 0)),  # 円
            "base_users": int(st.session_state.get(ui_key("labor.base_users"), 0)),
            "fte_increment_users": int(st.session_state.get(ui_key("labor.fte_increment_users"), 1)),
            "fte_increment": float(st.session_state.get(ui_key("labor.fte_increment"), 0.0)),
        }
    }
    return params

# -----------------------------
# JSON読込を session_state に反映（ウィジェット生成前に呼ぶ）
# -----------------------------
def apply_loaded_params_to_state(loaded: dict) -> None:
    # 形式チェック（最低限）
    if "robot" not in loaded or "app" not in loaded:
        raise ValueError("JSONの形式が想定と異なります（robot/appがありません）。")

    st.session_state[ui_key("robot.num_types")] = int(loaded["robot"]["num_types"])

    # ロボット種別
    for i, r in enumerate(loaded["robot"]["items"]):
        st.session_state[ui_key(f"robot.items.{i}.name")] = r["name"]
        st.session_state[ui_key(f"robot.items.{i}.price")] = int(r["price"])

        # JSONは内部表現（0-1）想定。もし%で入っていても破綻しないよう補正
        cr = float(r["commission_rate"])
        pr = float(r["purchase_rate"])
        if cr > 1.0:  # %として入っている可能性
            cr = cr / 100.0
        if pr > 1.0:
            pr = pr / 100.0

        st.session_state[ui_key(f"robot.items.{i}.commission_rate_pct")] = cr * 100.0
        st.session_state[ui_key(f"robot.items.{i}.purchase_rate_pct")] = pr * 100.0
        st.session_state[ui_key(f"robot.items.{i}.release_month")] = int(r["release_month"])


    # アプリ
    st.session_state[ui_key("app.monthly_fee")] = int(loaded["app"]["monthly_fee"])
    st.session_state[ui_key("app.free_months")] = int(loaded["app"]["free_months"])

    churn = float(loaded["app"]["churn_rate"])
    if churn > 1.0:
        churn = churn / 100.0
    st.session_state[ui_key("app.churn_rate_pct")] = churn * 100.0

    # --- 追加：cloud ---
    if "cloud" in loaded:
        c = loaded["cloud"]
        st.session_state[ui_key("cloud.initial_cost")] = int(c.get("initial_cost", 0))
        st.session_state[ui_key("cloud.bugfix_cost")] = int(c.get("bugfix_cost", 0))
        st.session_state[ui_key("cloud.num_thresholds")] = int(c.get("num_thresholds", 0))
        st.session_state[ui_key("cloud.aws_cost_per_user_month")] = int(c.get("aws_cost_per_user_month", 0))

        ths = c.get("thresholds", [])
        costs = c.get("scale_costs", [])

        n = int(st.session_state[ui_key("cloud.num_thresholds")])
        for i in range(n):
            st.session_state[ui_key(f"cloud.thresholds.{i}")] = int(ths[i] if i < len(ths) else 0)
            st.session_state[ui_key(f"cloud.scale_costs.{i}")] = int(costs[i] if i < len(costs) else 0)

    # -----------------------------
    # dealer
    # -----------------------------
    dealer = loaded.get("dealer", {})
    st.session_state[ui_key("dealer.initial_companies")] = int(dealer.get("initial_companies", 1))
    st.session_state[ui_key("dealer.max_companies")] = int(dealer.get("max_companies", 1))
    st.session_state[ui_key("dealer.fixed_months_before_growth")] = int(dealer.get("fixed_months_before_growth", 0))
    st.session_state[ui_key("dealer.company_growth_per_month")] = int(dealer.get("company_growth_per_month", 0))

    # -----------------------------
    # develop（params は円、UI は万円）
    # -----------------------------
    develop = loaded.get("develop", {})
    st.session_state[ui_key("develop.android_dev_initial")] = int(develop.get("android_dev_initial", 0))
    st.session_state[ui_key("develop.ios_dev_initial")] = int(develop.get("ios_dev_initial", 0))
    st.session_state[ui_key("develop.ios_dev_month")] = int(develop.get("ios_dev_month", 0))
    st.session_state[ui_key("develop.robot_if_dev")] = int(develop.get("robot_if_dev", 0))
    st.session_state[ui_key("develop.android_bugfix_cost")] = int(develop.get("android_bugfix_cost", 0))
    st.session_state[ui_key("develop.ios_bugfix_cost")] = int(develop.get("ios_bugfix_cost", 0))
    st.session_state[ui_key("develop.bugfix_cycle_months")] = int(develop.get("bugfix_cycle_months", 1))

    # -----------------------------
    # tool（robot_unit_cost: 円、sales_tool_cost_per_shop: 円→UI万円）
    # -----------------------------
    tool = loaded.get("tool", {})
    st.session_state[ui_key("tool.robot_unit_cost")] = int(tool.get("robot_unit_cost", 0))
    st.session_state[ui_key("tool.sales_tool_cost_per_shop")] = int(tool.get("sales_tool_cost_per_shop", 0))
    st.session_state[ui_key("tool.robots_per_shop")] = int(tool.get("robots_per_shop", 0))

    # -----------------------------
    # sport
    # -----------------------------
    sport = loaded.get("sport", {})
    st.session_state[ui_key("sport.cs_cost_per_user_month")] = int(sport.get("cs_cost_per_user_month", 0))

    # -----------------------------
    # labor（params は円、UI は万円）
    # -----------------------------
    labor = loaded.get("labor", {})
    st.session_state[ui_key("labor.base_fte")] = float(labor.get("base_fte", 0.0))
    st.session_state[ui_key("labor.fte_cost_per_month")] = int(labor.get("fte_cost_per_month", 0))
    st.session_state[ui_key("labor.base_users")] = int(labor.get("base_users", 0))
    st.session_state[ui_key("labor.fte_increment_users")] = int(labor.get("fte_increment_users", 1))
    st.session_state[ui_key("labor.fte_increment")] = float(labor.get("fte_increment", 0.0))

# ----------------------------------------------------
# Streamlit 基本設定
# ----------------------------------------------------
st.set_page_config(page_title="ビジネスモデル 収益・支出試算", layout="wide")
st.title("ビジネスモデル シミュレーション")

# ---- 大規模パラメータ管理：初期化 ----
params0 = default_params()
init_state_from_params(params0)

st.sidebar.header("パラメータ")

with st.sidebar.expander("設定の保存 / 読み込み"):
    uploaded = st.file_uploader("設定JSONを読み込む", type=["json"], key="uploader_params_json")
    if uploaded is not None and not st.session_state.get("flag_params_loaded", False):
        try:
            text = uploaded.getvalue().decode("utf-8-sig")  # BOM対策
            loaded_params = json.loads(text)

            apply_loaded_params_to_state(loaded_params)

            st.session_state["flag_params_loaded"] = True
            st.sidebar.success("読み込み完了")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"読み込み失敗: {e}")

    # 保存
    params_for_save = build_params_from_state()
    json_bytes = json.dumps(params_for_save, ensure_ascii=False, indent=2).encode("utf-8")

    st.download_button(
        "設定を保存（JSON）",
        data=json_bytes,
        file_name="params.json",
        mime="application/json",
        key="download_params_json",
    )

# ----------------------------------------------------
# 期間パラメータ（★シミュレーション年数）
# ----------------------------------------------------
years = st.sidebar.slider("シミュレーション年数（年）", min_value=1, max_value=10, value=7, step=1)
MONTHS = years * 12

# ----------------------------------------------------
# ロボット販売・手数料関連
# ----------------------------------------------------
#units_per_event = st.sidebar.number_input("イベントあたり販売台数（台）", min_value=0, value=2, step=1)
attendees_per_event = st.sidebar.number_input("イベントあたり集客数（人）", min_value=0, value=50, step=1)

# ----------------------------------------------------
# 販売会社イベント
# ----------------------------------------------------
events_per_company_per_month = st.sidebar.number_input("1社あたり月間イベント数（回）", min_value=0, value=2, step=1)

# ----------------------------------------------------
# 既存ユーザー向けアプリ課金
# ----------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("ロボット購入率設定")
num_types_sb = int(st.session_state.get(ui_key("robot.num_types"), 1))
for i in range(num_types_sb):
    r_name = st.session_state.get(ui_key(f"robot.items.{i}.name"), f"No{i+1}")
    st.sidebar.number_input(f"{r_name} 購入率（%）", min_value=0.0, max_value=10.0, step=0.1, key=ui_key(f"robot.items.{i}.purchase_rate_pct"))

st.sidebar.markdown("---")
st.sidebar.caption(f"ロボット保有顧客の月当たり新規課金登録者")
robot_uio_users_per_month = st.sidebar.number_input("新規課金登録者数（人）", min_value=0, value=0, step=1)



# ----------------------------------------------------
# タブ定義
# ----------------------------------------------------
tab_summary, tab_graphs, tab_settings  = st.tabs(["📋サマリー", "📊 グラフ", "⚙ 設定"])







with tab_settings:

    # ----------------------------------------------------
    # 収入パラメータ（メイン領域）
    # ----------------------------------------------------


    st.header("収入パラメータ設定")
    st.subheader("アプリ課金")
    st.caption(f"プラットフォーマー手数料＝15%")

    col = st.columns(2)
    with col[0]:
        st.number_input("アプリ月額料金（円）", min_value=0, step=10, key=ui_key("app.monthly_fee"))
        st.number_input("無料期間（月）", min_value=0, max_value=24, step=1, key=ui_key("app.free_months"))
    with col[1]:
        st.number_input("月間解約率（%）", min_value=0.0, max_value=50.0, step=0.5, key=ui_key("app.churn_rate_pct"))


    st.subheader("ロボット販売収益")

    st.number_input(
        "ロボット種類数",
        min_value=1,
        max_value=10,
        step=1,
        key=ui_key("robot.num_types"),
    )

    num_robot_types = int(st.session_state[ui_key("robot.num_types")])

    # ロボット情報を「items配列」として正規化
    for i in range(num_robot_types):
        with st.expander(f"ロボットNo{i + 1} の設定", expanded=(i == 0)):
            col = st.columns(2)
            with col[0]:
                st.text_input("ロボット名", key=ui_key(f"robot.items.{i}.name"))
                st.number_input("小売価格（円）", min_value=0, step=1_000, key=ui_key(f"robot.items.{i}.price"))
                st.number_input("販売開始月", min_value=0, step=1, key=ui_key(f"robot.items.{i}.release_month"))
            with col[1]:
                st.number_input("販売手数料率（%）", min_value=0.0, max_value=25.0, step=1.0, key=ui_key(f"robot.items.{i}.commission_rate_pct"))

    # ---- 計算用 params を組み立て（内部表現に正規化）----
    params = build_params_from_state()

    # app
    monthly_fee = params["app"]["monthly_fee"]
    free_months = params["app"]["free_months"]
    churn_rate = params["app"]["churn_rate"]

    # robot（配列に展開：既存計算を壊さないため）
    num_robot_types = params["robot"]["num_types"]
    robot_names = [r["name"] for r in params["robot"]["items"]]
    robot_prices = [r["price"] for r in params["robot"]["items"]]
    release_month = [r["release_month"] for r in params["robot"]["items"]]
    commission_rates = [r["commission_rate"] for r in params["robot"]["items"]]
    purchase_rates = [r["purchase_rate"] for r in params["robot"]["items"]]


    # ----------------------------------------------------
    # 販売会社（★毎月の増加数をパラメータ化）
    # ----------------------------------------------------
    st.subheader("販売会社（増加数）")
    col = st.columns(2)
    with col[0]:
        initial_companies = st.number_input("開始販売会社数", min_value=1, step=1,
                                            key=ui_key("dealer.initial_companies"))
        max_companies = st.number_input("販売会社数の上限（社）", min_value=1, step=1,
                                        key=ui_key("dealer.max_companies"))
    with col[1]:
        fixed_months_before_growth = st.number_input("初期実証期間", min_value=1, step=1,
                                                     key=ui_key("dealer.fixed_months_before_growth"))
        company_growth_per_month = st.number_input(
        "販売会社数の毎月の増加数（社／月）", min_value=0, step=1,
            key=ui_key("dealer.company_growth_per_month"))

    st.caption(f"販売会社数：1社（{fixed_months_before_growth}ヶ月）→ 以降は毎月の増加数だけ増加 → 上限に達したら停止")

    st.markdown("---")


    # ----------------------------------------------------
    # 支出パラメータ（メイン領域）
    # ----------------------------------------------------
    st.header("支出パラメータ設定")
    st.subheader("アプリ開発・不具合修正")
    col = st.columns(2)
    with col[0]:
        android_dev_initial = st.number_input("Android 初期開発費（万円）", min_value=0, step=10,
                                              key=ui_key("develop.android_dev_initial")) * 10000
        ios_dev_initial = st.number_input("iPhone 初期開発費（万円）", min_value=0, step=10,
                                          key=ui_key("develop.ios_dev_initial")) * 10000
        ios_dev_month = st.number_input("iPhone開発時期", min_value=0, step=1,
                                        key=ui_key("develop.ios_dev_month"))
        robot_if_dev = st.number_input("ロボットI/F開発費（万円）", min_value=0, step=10,
                                          key=ui_key("develop.robot_if_dev")) * 10000
    with col[1]:
        android_bugfix_cost = st.number_input("Android 不具合修正費用（万円）", min_value=0,  step=10,
                                              key=ui_key("develop.android_bugfix_cost")) * 10000
        ios_bugfix_cost = st.number_input("iPhone 不具合修正費用（万円）", min_value=0, step=10,
                                          key=ui_key("develop.ios_bugfix_cost")) * 10000
        bugfix_cycle_months = st.number_input("不具合修正リリース周期（ヶ月）", min_value=1, step=1,
                                              key=ui_key("develop.bugfix_cycle_months"))

    st.subheader("クラウドシステム")
    col = st.columns(2)
    with col[0]:
        cloud_initial = st.number_input("クラウド初期構築費用（万円）",
                                        min_value=0, step=10,
                                        key=ui_key("cloud.initial_cost")) * 10000
        cloud_bugfix_cost = st.number_input("クラウド不具合修正費用（万円）",
                                            min_value=0, step=10,
                                            key=ui_key("cloud.bugfix_cost")) * 10000
        # --- 置換：クラウド増強回数（保存/読込対象） ---
        st.number_input(
            "クラウド増強回数",
            min_value=0,
            step=1,
            key=ui_key("cloud.num_thresholds"),
        )

    with col[1]:
        aws_cost_per_user_month = st.number_input("AWS費用（有料会員あたり月額・円）",
                                                  min_value=0, step=5,
                                                  key=ui_key("cloud.aws_cost_per_user_month"))

    num_thresholds = int(st.session_state[ui_key("cloud.num_thresholds")])

    # 結果格納用の配列
    cloud_scale_thresholds = []
    cloud_scale_costs = []

    col = st.columns(2)
    with col[0]:
        for i in range(num_thresholds):
            threshold = st.number_input(
                f"クラウド増強閾値 No{i+1}（有料会員数）",
                min_value=0,
                step=100,
                key=ui_key(f"cloud.thresholds.{i}"),
            )
            cloud_scale_thresholds.append(int(threshold))
    with col[1]:
        for i in range(num_thresholds):
            cost = st.number_input(
                f"クラウド増強費用 No{i+1}（万円）",
                min_value=0,
                step=10,
                key=ui_key(f"cloud.scale_costs.{i}"),
            ) * 10000  # 円換算
            cloud_scale_costs.append(int(cost))

    st.markdown("---")
    st.subheader("販売店向けロボット・販売ツール")
    col11, col12 = st.columns(2)
    with col11:
        robot_unit_cost = st.number_input("ロボット1式費用（円）", min_value=0, step=1000,
                                          key=ui_key("tool.robot_unit_cost"))
        sales_tool_cost_per_shop = st.number_input("販売ツール一式費用／社（万円）", min_value=0, step=1,
                                                   key=ui_key("tool.sales_tool_cost_per_shop")) * 10000
    with col12:
        robots_per_shop = st.number_input("販売店あたりロボット台数（台）", min_value=0, step=1,
                                          key=ui_key("tool.robots_per_shop"))

    st.subheader("カスタマーサポート")
    colmk5, colmk6 = st.columns(2)
    with colmk5:
        cs_cost_per_user_month = st.number_input("CS費用（有料会員あたり月額・円）", min_value=0, step=10,
                                                 key=ui_key("sport.cs_cost_per_user_month"))

    st.subheader("事業体人件費")
    col13, col14 = st.columns(2)
    with col13:
        base_fte = st.number_input("初期事業体要員（人）", min_value=0.0, step=0.1,
                                   key=ui_key("labor.base_fte"))
        fte_cost_per_month = st.number_input("人月当たり人件費（万円）", min_value=0, step=10,
                                             key=ui_key("labor.fte_cost_per_month")) * 10000
    with col14:
        base_users = st.number_input("増員なしの上限（有料会員数）", min_value=0, step=100,
                                     key=ui_key("labor.base_users"))
        fte_increment_users = st.number_input("増員基準（有料会員数）", min_value=1, step=100,
                                              key=ui_key("labor.fte_increment_users"))
        fte_increment = st.number_input("追加人員（人）", min_value=0.0, step=0.1,
                                        key=ui_key("labor.fte_increment"))


# ----------------------------------------------------
# 配列の準備（★MONTHS に応じて動的生成）
# ----------------------------------------------------
contract_companies = [0] * MONTHS
events_per_month = [0] * MONTHS
new_users = [0] * MONTHS
trial_starts = [0] * MONTHS
paying_users = [0.0] * MONTHS
app_revenue = [0.0] * MONTHS
commission_revenue = [0.0] * MONTHS
total_revenue = [0.0] * MONTHS

# ----------------------------------------------------
# 月次シミュレーション（収益）
# ----------------------------------------------------
# ループの前で、ロボット種別ごとの販売台数配列を用意しておく
robot_sales_by_type = [[0] * MONTHS for _ in range(num_robot_types)]

for m in range(MONTHS):

    # 契約販売会社数の推移
    if m < fixed_months_before_growth:
        companies = initial_companies
    else:
        months_since_growth = m - fixed_months_before_growth + 1
        companies = initial_companies + company_growth_per_month * months_since_growth
        companies = min(companies, max_companies)

    contract_companies[m] = companies

    # イベント数
    events = companies * events_per_company_per_month
    events_per_month[m] = events



    # --- 複数種類のロボットに対応した計算 ---

    total_robots_sold = 0
    total_commission = 0.0

    for i in range(num_robot_types):
        # 種類ごとの販売台数（イベント数 × 集客数　×　種別ごとの購入率）
        if m > release_month[i]:
            robots_sold_i = int(events *  attendees_per_event * purchase_rates[i])
        else:
            robots_sold_i = 0
        robot_sales_by_type[i][m] = robots_sold_i

        # 全種類の販売台数を合計（= 新規ユーザー数）
        total_robots_sold += robots_sold_i

        # 種類ごとの販売手数料
        commission_i = robots_sold_i * robot_prices[i] * commission_rates[i]
        total_commission += commission_i

    # 新規ユーザー（全ロボット種別の合計販売台数）
    new_users[m] = total_robots_sold
    trial_starts[m] = total_robots_sold + robot_uio_users_per_month

    # 販売手数料収入（全ロボット種別の合計）
    commission_revenue[m] = total_commission

    # 有料会員数
    prev = paying_users[m - 1] if m > 0 else 0
    churn = prev * churn_rate
    remaining = prev - churn

    # 無料期間後に課金開始
    conversions = trial_starts[m - free_months] if m >= free_months else 0
    paying_users[m] = remaining + conversions

    # アプリ収入
    app_revenue[m] = paying_users[m] * monthly_fee * 0.85

    # 総売上
    total_revenue[m] = app_revenue[m] + commission_revenue[m]

# ----------------------------------------------------
# ★ 支出シミュレーション（有料会員数ベース）
# ----------------------------------------------------

# 「ユーザー数に応じた費用」は有料会員数を使う
users_for_cost = paying_users  # ここがポイント

# 月次支出項目の配列
cost_app_android_initial = [0] * MONTHS
cost_app_ios_initial = [0] * MONTHS
cost_robot_if_dev = [0] * MONTHS
cost_app_android_bugfix = [0] * MONTHS
cost_app_ios_bugfix = [0] * MONTHS

cost_cloud_initial_arr = [0] * MONTHS
cost_cloud_aws = [0] * MONTHS
cost_cloud_bugfix_arr = [0] * MONTHS
cost_cloud_scale = [0] * MONTHS

cost_shop_acquisition = [0] * MONTHS
cost_customer_support = [0] * MONTHS

potstill_fte = [0.0] * MONTHS
cost_potstill_salary = [0.0] * MONTHS

# 初期費用（アプリ・ロボットI/F・クラウド）
if MONTHS > 0:
    cost_app_android_initial[0] = android_dev_initial
    cost_app_ios_initial[ios_dev_month] = ios_dev_initial
    for i in range(num_robot_types):
        cost_robot_if_dev[int(st.session_state.get(ui_key(f"robot.items.{i}.release_month"), 0))] = robot_if_dev
    cost_cloud_initial_arr[0] = cloud_initial

# 不具合修正：bugfix_cycle_months ごと
for m in range(MONTHS):
    if m % bugfix_cycle_months == 0:
        if m < 1:
            cost_app_android_bugfix[m] = 0
            cost_cloud_bugfix_arr[m] = 0
        else:
            cost_app_android_bugfix[m] = android_bugfix_cost
            cost_cloud_bugfix_arr[m] = cloud_bugfix_cost
        if m < ios_dev_month + 1:
            cost_app_ios_bugfix[m] = 0
        else:
            cost_app_ios_bugfix[m] = ios_bugfix_cost


# AWS費用・CS費用（有料会員数に比例）
for m in range(MONTHS):
    users = users_for_cost[m]
    cost_cloud_aws[m] = users * aws_cost_per_user_month
    cost_customer_support[m] = users * cs_cost_per_user_month

# クラウド増強費用（有料会員数が閾値を初めて超えた月に1回だけ）
threshold_flags = [False] * len(cloud_scale_thresholds)
for m in range(MONTHS):
    users_prev = users_for_cost[m - 1] if m > 0 else 0
    users_now = users_for_cost[m]
    for i, th in enumerate(cloud_scale_thresholds):
        if threshold_flags[i]:
            continue
        if users_prev < th <= users_now:
            cost_cloud_scale[m] += cloud_scale_costs[i]
            threshold_flags[i] = True

# 販売店ごとのロボット・ツール費用（新規販売会社数×一式費用）
new_companies = [0] * MONTHS
for m in range(MONTHS):
    if m == 0:
        new_companies[m] = contract_companies[m]
    else:
        diff = contract_companies[m] - contract_companies[m - 1]
        new_companies[m] = diff if diff > 0 else 0

per_shop_acquisition_cost = robots_per_shop * robot_unit_cost + sales_tool_cost_per_shop
for m in range(MONTHS):
    cost_shop_acquisition[m] = new_companies[m] * per_shop_acquisition_cost

# 事業体人件費（有料会員数ベース）
for m in range(MONTHS):
    users = users_for_cost[m]
    users_over_base = max(0, users - base_users)
    increments = math.ceil(users_over_base / fte_increment_users) if users_over_base > 0 else 0
    fte = base_fte + increments * fte_increment
    potstill_fte[m] = fte
    cost_potstill_salary[m] = fte * fte_cost_per_month

# 月次総支出
total_expense = [0.0] * MONTHS
for m in range(MONTHS):
    total_expense[m] = (
        cost_app_android_initial[m]
        + cost_app_ios_initial[m]
        + cost_robot_if_dev[m]
        + cost_app_android_bugfix[m]
        + cost_app_ios_bugfix[m]
        + cost_cloud_initial_arr[m]
        + cost_cloud_aws[m]
        + cost_cloud_bugfix_arr[m]
        + cost_cloud_scale[m]
        + cost_shop_acquisition[m]
        + cost_customer_support[m]
        + cost_potstill_salary[m]
    )

# 月次利益（売上－支出）
profit = [total_revenue[m] - total_expense[m] for m in range(MONTHS)]

# ----------------------------------------------------
# 年次集計（★years に応じて可変）
# ----------------------------------------------------
annual_total = []
annual_app = []
annual_commission = []
annual_robot_sales = []
annual_expense = []
annual_profit = []

for y in range(years):
    start = y * 12
    end = min((y + 1) * 12, MONTHS)

    annual_total.append(sum(total_revenue[start:end]) / 10000)
    annual_app.append(sum(app_revenue[start:end]) / 10000)
    annual_commission.append(sum(commission_revenue[start:end]) / 10000)
    annual_robot_sales.append(sum(new_users[start:end]))
    annual_expense.append(sum(total_expense[start:end]) / 10000)
    annual_profit.append(sum(profit[start:end]) / 10000)

# 年間ロボット販売台数（種類別）
annual_robot_sales_by_type = [
    [0] * years for _ in range(num_robot_types)
]

for i in range(num_robot_types):
    for y in range(years):
        start = y * 12
        end = min((y + 1) * 12, MONTHS)
        annual_robot_sales_by_type[i][y] = sum(robot_sales_by_type[i][start:end])



# ----------------------------------------------------
# 追加：年間 売上・支出・利益・累損 グラフ
# ----------------------------------------------------
# 累損（＝年間利益の累計）を計算
cumulative_loss = []
running = 0
for p in annual_profit:
    running += p
    cumulative_loss.append(running)

years_labels = [f"{y+1}年目" for y in range(years)]
months = list(range(1, MONTHS + 1))

# ----------------------------------------------------
# Plotly: 5段構成のサブプロット（収益部分は元コード準拠）
# ----------------------------------------------------

fig_colors  = ["#1F5DBA", "#2E8B57", "#DAA520", "#ff9da7"]

with tab_graphs:



    fig = make_subplots(
        rows=2,
        cols=1,
        specs=[
            [{"secondary_y": False}],
            [{"secondary_y": False}],
        ],
        vertical_spacing=0.2,
        subplot_titles=[
            "総売上・販売手数料・アプリ収入",
            "販売台数"
        ]
    )


    # ④ 年間売上（総・手数料・アプリ）
    fig.add_trace(go.Bar(x=years_labels, y=annual_total, name="総売上"), row=1, col=1)
    fig.add_trace(go.Bar(x=years_labels, y=annual_commission, name="販売手数料収入"), row=1, col=1)
    fig.add_trace(go.Bar(x=years_labels, y=annual_app, name="アプリ収入"), row=1, col=1)

    # ⑤ 年間ロボット販売台数
    # 種類別 年間販売台数の棒グラフ
    for i in range(num_robot_types):
        fig.add_trace(
            go.Bar(
                x=years_labels,
                y=annual_robot_sales_by_type[i],
                name=f"{robot_names[i]}"
            ),
            row=2,
            col=1
        )

    fig.update_layout(
        height=600,
        barmode="group",
        title="売上げ・販売台数",
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
        colorway=fig_colors
    )
    fig.update_yaxes(tickformat=",")

    st.plotly_chart(fig, use_container_width=True)


    fig = make_subplots(
        rows=3,
        cols=1,
        specs=[
            [{"secondary_y": False}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
        ],
        vertical_spacing=0.06,
        subplot_titles=[
            "販売会社数・イベント数",
            "新規ユーザー数（左軸）",
            "有料会員数（左軸）・アプリ収入（右軸）",
        ]
    )

    # ①
    fig.add_trace(go.Bar(x=months, y=contract_companies, name="販売会社数"), row=1, col=1)
    fig.add_trace(go.Bar(x=months, y=events_per_month, name="イベント数"), row=1, col=1)

    # ②
    fig.add_trace(go.Bar(x=months, y=new_users, name="新規ユーザー数", opacity=0.5),
                  row=2, col=1, secondary_y=False)

    # ③
    fig.add_trace(go.Bar(x=months, y=paying_users, name="有料会員数", opacity=0.5),
                  row=3, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=months, y=[x/10000 for x in app_revenue], name="アプリ収入", mode="lines"),
                  row=3, col=1, secondary_y=True)


    fig.update_layout(
        height=1500,
        barmode="group",
        title="収益計算（ロボット販売 × アプリ課金）",
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
    )
    fig.update_yaxes(tickformat=",", secondary_y=False)
    fig.update_yaxes(tickformat=",", title_text="金額（万円）", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


    # 支出項目別 月次推移グラフ
    st.subheader("支出項目別 月次推移")

    # アプリ開発 月次推移グラフ
    fig3 = go.Figure()

    fig3.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_app_android_initial], name="アプリ開発費（Android初期）"))
    fig3.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_app_ios_initial], name="アプリ開発費（iPhone初期）"))
    fig3.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_robot_if_dev], name="ロボットI/F開発費"))
    fig3.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_app_android_bugfix], name="アプリ不具合修正費（Android）"))
    fig3.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_app_ios_bugfix], name="アプリ不具合修正費（iPhone）"))

    fig3.update_layout(
        title="アプリ開発 月次推移",
        xaxis_title="月",
        yaxis_title="金額（万円）",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=700,
    )
    fig3.update_yaxes(tickformat=",")

    st.plotly_chart(fig3, use_container_width=True)

    # クラウド費用 月次推移グラフ
    fig4 = go.Figure()

    fig4.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_cloud_initial_arr], name="クラウド初期構築費"))
    fig4.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_cloud_aws], name="AWS費用（有料会員数連動）"))
    fig4.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_cloud_bugfix_arr], name="クラウド不具合修正費", ))
    fig4.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_cloud_scale], name="クラウド増強費用", ))

    fig4.update_layout(
        title="クラウド費用 月次推移（全費目）",
        xaxis_title="月",
        yaxis_title="金額（万円）",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=700,
    )
    fig4.update_yaxes(tickformat=",")

    st.plotly_chart(fig4, use_container_width=True)

    # その他 月次推移グラフ
    fig5 = go.Figure()

    fig5.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_shop_acquisition], name="販売店向けロボット・ツール費", ))
    fig5.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_customer_support], name="カスタマーサポート費", ))
    fig5.add_trace(go.Bar(x=months, y=[x/10000 for x in cost_potstill_salary], name="事業体人件費", ))

    fig5.update_layout(
        title="その他 月次推移（全費目）",
        xaxis_title="月",
        yaxis_title="金額（万円）",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=700,
    )
    fig5.update_yaxes(tickformat=",")

    st.plotly_chart(fig5, use_container_width=True)










with tab_summary:
    st.header("重要指標 (KPI)")

    # 1. 重要数字 (Metrics)
    total_rev_man = sum(total_revenue) / 10000
    total_exp_man = sum(total_expense) / 10000
    total_prof_man = sum(profit) / 10000
    final_users = paying_users[-1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総売上（7年計）", f"{total_rev_man:,.0f} 万円")
    col2.metric("総支出（7年計）", f"{total_exp_man:,.0f} 万円")
    col3.metric("累積利益", f"{total_prof_man:,.0f} 万円", delta="黒字" if total_prof_man >= 0 else "-赤字")
    col4.metric("最終有料会員数", f"{final_users:,.0f} 人")

    st.markdown("---")

    # 年間 売上・支出・利益・累損 グラフ
    fig2_colors = ["#1F5DBA", "#F03531", "#7DBBFF", "#F5A3A3"]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=years_labels, y=annual_total, name="総売上"))
    fig2.add_trace(go.Bar(x=years_labels, y=annual_expense, name="総支出"))
    fig2.add_trace(go.Bar(x=years_labels, y=annual_profit, name="年間利益"))
    fig2.add_trace(go.Scatter(x=years_labels, y=cumulative_loss, name="累損（累計利益）", mode="lines+markers"))

    fig2.update_layout(
        title="売上・支出・利益・累損",
        yaxis_title="金額（万円）",
        barmode="group",
        colorway=fig2_colors
    )
    fig2.update_yaxes(tickformat=",")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # 2. 内訳グラフ (Breakdown)
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("売上構成")
        # 円グラフ用データ
        labels_rev = ["アプリ課金", "販売手数料"]
        values_rev = [sum(app_revenue), sum(commission_revenue)]

        fig_rev = go.Figure(data=[go.Pie(labels=labels_rev, values=values_rev, hole=.3)])
        fig_rev.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_rev, use_container_width=True)

        st.caption(f"{years}年間の売上内訳")
        st.write(f"💸 総アプリ課金：**{sum(app_revenue)/10000:,.0f}万円**")
        st.write(f"💸 総販売手数料：**{sum(commission_revenue)/10000:,.0f}万円**")

    with col_g2:
        st.subheader("支出構成")
        # 支出分類詳細
        # total_apl_expense = ... (下で計算されているが、ここでも使うために計算 or 参照)
        # 変数スコープ的に下のコードがまだ実行されていないので再計算が必要、または順序注意。
        # ここではグラフ用の大分類で。

        val_dev = sum(cost_app_ios_initial) + sum(cost_app_android_initial) + sum(cost_robot_if_dev) + sum(cost_app_ios_bugfix) + sum(cost_app_android_bugfix)
        val_cloud = sum(cost_cloud_initial_arr) + sum(cost_cloud_aws) + sum(cost_cloud_bugfix_arr) + sum(cost_cloud_scale)
        val_labor = sum(potstill_fte) + sum(cost_potstill_salary) # fte sum is not cost, cost_potstill_salary is cost
        # Wait, potstill_fte sum is man-months, cost_potstill_salary is cost. Correct.
        val_labor = sum(cost_potstill_salary)
        val_sales = sum(cost_shop_acquisition)
        val_cs = sum(cost_customer_support)

        labels_exp = ["開発費", "クラウド費", "人件費", "販売ツール費", "CS費"]
        values_exp = [val_dev, val_cloud, val_labor, val_sales, val_cs]

        fig_exp = go.Figure(data=[go.Pie(labels=labels_exp, values=values_exp, hole=.3)])
        fig_exp.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_exp, use_container_width=True)

        st.caption(f"{years}年間の支出内訳")
        st.write(f"💸 総アプリ開発費：**{val_dev/10000:,.0f}万円**")
        st.write(f"💸 総クラウド開発費：**{val_cloud/10000:,.0f}万円**")
        st.write(f"💸 総事業体人件費：**{val_labor/10000:,.0f}万円**")
        st.write(f"💸 総販売ツール費：**{val_sales/10000:,.0f}万円**")
        st.write(f"💸 総カスタマーサポート費：**{val_cs/10000:,.0f}万円**")



