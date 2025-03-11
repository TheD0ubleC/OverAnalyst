import os
import joblib
import numpy as np
import constants

MODEL_DIR = "models"

# =========================
# 低优先级英雄 (二维数组)
# =========================
# 例如 [["狂鼠", 0.05]] 表示: 如果队伍1带了“狂鼠”，队伍1胜率要 -0.05
LOW_PRIORITY_HEROES_PENALTY = [
    ["狂鼠", 0.05],
    ["莱因哈特", 0.04],
    ["黑百合", 0.01],
    ["生命之梭", 0], # 我讨厌你 生命之梭 玩生命之梭的都是nt！！！
    ["莫伊拉", 0.05],
]

# =========================
# 负向克制链 (降低胜率)
# =========================

HERO_FLOATS = {
    "莱因哈特": 0.08,
    "温斯顿": 0.12,
    "D.Va": 0.08,
    "路霸": 0.09,
    "查莉娅": 0.05,
    "末日铁拳": 0.09,
    "奥丽莎": 0.07,
    "破坏球": 0.12,
    "毛加": 0.09,
    "西格玛": 0.07,
    "渣客女王": 0.08,
    "拉玛刹": 0.09,
    "骇灾": 0.08,

    # =====================================
    # 输出（DPS）
    # =====================================
    "死神": 0.09,
    "猎空": 0.10,
    "半藏": 0.07,
    "托比昂": 0.06,
    "法老之鹰": 0.10,
    "黑百合": 0.08,
    "堡垒": 0.10,
    "秩序之光": 0.07,
    "源氏": 0.08,
    "卡西迪": 0.05,
    "狂鼠": 0.12,
    "士兵：76": 0.06,
    "美": 0.07,
    "黑影": 0.08,
    "索杰恩": 0.05,
    "艾什": 0.07,
    "回声": 0.08,
    "探奇": 0.00,

    # =====================================
    # 辅助英雄（Support）
    # =====================================
    "天使": 0.09,
    "禅雅塔": 0.12,
    "卢西奥": 0.06,
    "安娜": 0.13,
    "巴蒂斯特": 0.07,
    "莫伊拉": 0.08,
    "雾子": 0.06,
    "生命之梭": 0.09,
    "伊拉锐": 0.10,
    "朱诺": 0.06,
}

# 合并 COUNTER_PAIRS 和浮动值 HERO_FLOATS
COUNTER_PAIRS_NEG = [
    [hero[0], hero[1], HERO_FLOATS.get(hero[0], 0)]  # 使用字典的浮动值，如果找不到该英雄，默认值为0
    for hero in constants.COUNTER_PAIRS
]


# =========================
# 🔄 加载模型 & 编码器
# =========================
def load_model(model_name):
    model_path = os.path.join(MODEL_DIR, f"{model_name}.joblib")
    if not os.path.exists(model_path):
        print(f"❌ 模型 '{model_name}' 不存在！")
        return None
    return joblib.load(model_path)

def load_encoders():
    try:
        mlb_heroes = joblib.load(os.path.join(MODEL_DIR, "MLB_HEROES.joblib"))
        lb_maps = joblib.load(os.path.join(MODEL_DIR, "LB_MAPS.joblib"))
        return mlb_heroes, lb_maps
    except Exception as e:
        print(f"⚠️ 编码器加载失败: {e}")
        return None, None

# =========================
# 🔧 特征构造
# =========================
def build_feature_matrix(team_1_heroes, team_2_heroes, map_name, mlb_heroes, lb_maps):
    team1_encoded = mlb_heroes.transform([team_1_heroes])
    team2_encoded = mlb_heroes.transform([team_2_heroes])

    if map_name not in lb_maps.classes_:
        print(f"⚠️ 地图 '{map_name}' 不在训练数据中，将视为未知地图 (全零向量)。")
        map_encoded = np.zeros((1, len(lb_maps.classes_)))
    else:
        map_encoded = lb_maps.transform([map_name])

    X_matrix = np.hstack([team1_encoded, team2_encoded, map_encoded])
    return X_matrix

# =========================
# 🔎 获取英雄角色
# =========================
def get_role(hero):
    if hero in constants.TANK_HEROES:
        return "Tank"
    elif hero in constants.DPS_HEROES:
        return "DPS"
    elif hero in constants.SUPPORT_HEROES:
        return "Support"
    return None

# =========================
# 🛠️ 负向效果: 低优先级 & 被克制
# =========================
def apply_negative_effect(team_1, team_2):
    """
    计算队伍1的所有负向效果，包括：
    1. 低优先级英雄的惩罚
    2. 被对方英雄克制的惩罚（同一英雄被多个克制时叠加）
    3. 如果同一英雄在 COUNTER_PAIRS_NEG 中有多个条目，则取平均权重
    """
    penalty = 0.0



    # 2) 计算克制链的惩罚
    counter_penalties = {}  # 用于存储 {被克制英雄: [多个权重值]}
    
    for hero1, hero2_list, val in COUNTER_PAIRS_NEG:
        if hero1 in team_1:
            for hero2 in hero2_list:
                if hero2 in team_2:
                    if hero1 not in counter_penalties:
                        counter_penalties[hero1] = []
                    counter_penalties[hero1].append(val)

    # 计算克制的平均权重，并累加总 penalty
    for hero, values in counter_penalties.items():
        avg_penalty = sum(values) / len(values)  # 取平均值
        penalty += avg_penalty


    for hero, val in LOW_PRIORITY_HEROES_PENALTY:
        if hero in team_1:
            penalty += val

    # 3) 确保 penalty 不会过高，导致胜率变成负数
    penalty = min(penalty, 0.65)  # 限制最大削减值（可调整）

    return penalty

# =========================
# 🔮 单次预测（带惩罚）
# =========================
def single_predict(model_name, team_1, team_2, map_name):
    """
    计算单次胜率，并应用负面惩罚
    """
    model = load_model(model_name)
    if model is None:
        return None
    mlb_heroes, lb_maps = load_encoders()
    if mlb_heroes is None or lb_maps is None:
        return None

    # 1) 使用模型得到基础胜率
    X = build_feature_matrix(team_1, team_2, map_name, mlb_heroes, lb_maps)
    p = model.predict_proba(X)[0][1]

    # 2) 计算负向影响
    penalty = apply_negative_effect(team_1, team_2)
    p -= penalty

    # 3) 确保 p 在 [0, 1] 范围
    p = max(0.0, min(1.0, p))
    return p


# =========================
# 无偏见预测
# =========================
def predict_no_bias(model_name, team_1, team_2, map_name):
    """
    做两次预测：
        pA = single_predict(team_1 vs team_2)
        pB = single_predict(team_2 vs team_1)
    然后计算 (pA + (1 - pB)) / 2 来消除模型的偏见。
    """
    pA = single_predict(model_name, team_1, team_2, map_name)
    pB = single_predict(model_name, team_2, team_1, map_name)
    if pA is None or pB is None:
        return None
    corrected_prob = (pA + (1 - pB)) / 2
    return corrected_prob

# =========================
# 指定英雄换人 (强制)
# =========================
def replacement(model_name, team_1, team_2, map_name, out_hero, team="team_1"):
    """
    强制换掉 out_hero，换成相同角色的其他英雄，选胜率提升最大的那个。
    返回: (orig_win_prob, (best_in_hero, new_win_prob, delta)) 或 (orig_win_prob, None)
    """
    if team == "team_1":
        target_team, other_team = team_1[:], team_2
    elif team == "team_2":
        target_team, other_team = team_2[:], team_1
    else:
        print("❌ team 参数错误，只能是 'team_1' 或 'team_2'")
        return None, None

    if out_hero not in target_team:
        print(f"无法换人：队伍中没有[{out_hero}]")
        return None, None

    idx = target_team.index(out_hero)
    role = get_role(out_hero)
    if not role:
        print(f" 英雄[{out_hero}]角色未知，跳过")
        return None, None

    if role == "Tank":
        candidate_pool = constants.TANK_HEROES
    elif role == "DPS":
        candidate_pool = constants.DPS_HEROES
    else:
        candidate_pool = constants.SUPPORT_HEROES

    orig_win_prob = predict_no_bias(model_name, team_1, team_2, map_name)
    if orig_win_prob is None:
        return None, None

    best_swap_info = None
    best_delta = 0.0

    # 逐一尝试替换
    for hero_in in candidate_pool:
        if hero_in == out_hero or hero_in in target_team or hero_in in other_team:
            continue

        new_team = target_team[:]
        new_team[idx] = hero_in

        if team == "team_1":
            new_win_prob = predict_no_bias(model_name, new_team, team_2, map_name)
        else:
            new_win_prob = predict_no_bias(model_name, team_1, new_team, map_name)

        if new_win_prob is None:
            continue

        delta = new_win_prob - orig_win_prob
        if delta > best_delta:
            best_delta = delta
            best_swap_info = (hero_in, new_win_prob, delta)

    return orig_win_prob, best_swap_info

# =========================
# AI 自动推荐换人 (指定队伍)
# =========================
def auto_team_swap(model_name, team_1, team_2, map_name, team="team_1"):
    """
    自动分析队伍，遍历每个英雄，用相同角色的其它英雄替换，选出能最大提升胜率的方案
    返回: (orig_win_prob, out_hero, in_hero, new_win_prob, delta)
    """
    if team == "team_1":
        target_team, other_team = team_1[:], team_2
    elif team == "team_2":
        target_team, other_team = team_2[:], team_1
    else:
        print(" team 参数错误，只能是 'team_1' 或 'team_2'")
        return None, None, None, None, 0.0

    orig_win_prob = predict_no_bias(model_name, team_1, team_2, map_name)
    if orig_win_prob is None:
        return None, None, None, None, 0.0

    best_out = None
    best_in = None
    best_new_prob = None
    best_delta = 0.0

    for i, old_hero in enumerate(target_team):
        role = get_role(old_hero)
        if not role:
            continue

        if role == "Tank":
            candidate_pool = constants.TANK_HEROES
        elif role == "DPS":
            candidate_pool = constants.DPS_HEROES
        else:
            candidate_pool = constants.SUPPORT_HEROES

        # 逐一尝试
        for hero_in in candidate_pool:
            if hero_in == old_hero or hero_in in target_team or hero_in in other_team:
                continue

            new_team = target_team[:]
            new_team[i] = hero_in

            if team == "team_1":
                new_win_prob = predict_no_bias(model_name, new_team, team_2, map_name)
            else:
                new_win_prob = predict_no_bias(model_name, team_1, new_team, map_name)

            if new_win_prob is None:
                continue

            delta = new_win_prob - orig_win_prob
            if delta > best_delta:
                best_delta = delta
                best_out = old_hero
                best_in = hero_in
                best_new_prob = new_win_prob

    return orig_win_prob, best_out, best_in, best_new_prob, best_delta