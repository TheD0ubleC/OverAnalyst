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
COUNTER_PAIRS_NEG = [
    # =====================================
    # 坦克（Tank）
    # =====================================

    ["莱因哈特", ["路霸", "堡垒", "法老之鹰", "回声", "安娜", "禅雅塔"], 0.08],
    ["温斯顿", ["死神", "布丽吉塔", "D.Va", "托比昂", "堡垒", "路霸", "禅雅塔", "索杰恩","渣客女王"], 0.12],
    ["D.Va", ["查莉娅", "死神", "托比昂", "堡垒", "禅雅塔", "安娜"], 0.08],
    ["路霸", ["安娜", "禅雅塔", "死神", "D.Va", "堡垒"], 0.09],
    ["查莉娅", ["法老之鹰", "回声", "黑百合", "艾什", "半藏", "堡垒", "巴蒂斯特", "美", "禅雅塔", "安娜"], 0.05],
    ["末日铁拳", ["黑影", "奥丽莎", "路霸", "布丽吉塔", "禅雅塔", "安娜"], 0.09],
    ["奥丽莎", ["回声", "堡垒", "禅雅塔", "法老之鹰", "安娜"], 0.07],
    ["破坏球", ["黑影", "布丽吉塔", "托比昂", "美", "安娜", "路霸", "禅雅塔"], 0.12],
    ["莱因哈特", ["路霸", "堡垒", "法老之鹰", "回声", "安娜", "禅雅塔"], 0.08],
    ["毛加", ["毛加","禅雅塔", "安娜", "法老之鹰", "回声"], 0.09],
    ["奥丽莎", ["堡垒", "禅雅塔", "安娜", "法老之鹰", "回声"], 0.07],
    ["西格玛", ["猎空", "源氏", "温斯顿", "破坏球", "禅雅塔", "安娜"], 0.07],
    ["渣客女王", ["安娜", "禅雅塔", "堡垒", "法老之鹰", "回声"], 0.08],
    ["拉玛刹", ["禅雅塔", "安娜", "堡垒", "法老之鹰", "回声", "死神","索杰恩"], 0.09],
    ["毛加", ["禅雅塔", "安娜", "法老之鹰", "回声"], 0.09],
    ["骇灾", ["禅雅塔", "安娜", "堡垒", "法老之鹰", "回声"], 0.08],

    # =====================================
    # 输出（DPS）
    # =====================================
    ["死神", ["法老之鹰", "回声", "黑百合", "半藏", "艾什", "索杰恩"], 0.09],
    ["猎空", ["托比昂", "美", "布丽吉塔", "莫伊拉", "卡西迪", "路霸"], 0.10],
    ["半藏", [ "D.Va", "温斯顿", "破坏球"], 0.07],
    ["托比昂", ["法老之鹰", "回声", "艾什"], 0.06],
    ["法老之鹰", ["艾什", "卡西迪", "士兵：76", "索杰恩", "巴蒂斯特"], 0.10],
    ["黑百合", ["温斯顿", "D.Va", "破坏球", "猎空", "源氏", "黑影", "末日铁拳"], 0.08],
    ["堡垒", ["源氏", "猎空", "法老之鹰", "回声", "D.Va", "破坏球", "安娜"], 0.10],
    ["秩序之光", ["法老之鹰", "回声", "D.Va", "破坏球"], 0.07],
    ["源氏", ["布丽吉塔", "莫伊拉", "托比昂", "美", "温斯顿", "禅雅塔"], 0.08],
    ["卡西迪", ["D.Va", "温斯顿", "猎空", "黑影", "破坏球"], 0.05],
    ["狂鼠", ["法老之鹰", "回声"], 0.12],
    ["士兵：76", ["温斯顿", "D.Va", "猎空", "源氏", "黑影"], 0.06],
    ["美", ["法老之鹰", "回声", "艾什", "禅雅塔"], 0.07],
    ["黑影", ["布丽吉塔", "托比昂", "温斯顿", "禅雅塔"], 0.08],
    ["索杰恩", ["温斯顿", "D.Va", "破坏球","猎空","源氏"], 0.05],
    ["艾什", ["温斯顿", "D.Va", "猎空", "源氏", "黑影"], 0.07],
    ["回声", ["索杰恩", "艾什", "卡西迪", "堡垒", "士兵：76"], 0.08],
    ["探奇", [], 0.00],
    # =====================================
    # 辅助英雄（Support）
    # =====================================
    ["天使", ["黑影", "猎空", "源氏", "温斯顿", "破坏球", "D.Va", "末日铁拳"], 0.09],
    ["禅雅塔", ["猎空", "源氏", "黑影", "温斯顿", "破坏球", "死神", "末日铁拳"], 0.12],
    ["卢西奥", ["猎空", "黑影", "末日铁拳", "温斯顿", "源氏"], 0.06],
    ["安娜", ["源氏", "猎空", "黑影", "温斯顿", "D.Va", "破坏球", "末日铁拳"], 0.13],
    ["巴蒂斯特", ["温斯顿", "猎空", "黑影", "破坏球", "末日铁拳"], 0.07],
    ["莫伊拉", ["温斯顿", "猎空", "源氏", "黑影", "末日铁拳"], 0.08],
    ["雾子", ["猎空", "黑影", "源氏", "末日铁拳", "温斯顿"], 0.06],
    ["生命之梭", ["猎空", "黑影", "源氏", "温斯顿", "末日铁拳"], 0.09],
    ["伊拉锐", ["猎空", "黑影", "温斯顿", "破坏球", "源氏"], 0.1],
    ["朱诺", ["猎空", "黑影", "温斯顿", "末日铁拳", "源氏"], 0.06],
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

# =========================
# 演示
# =========================
if __name__ == "__main__":
    model_name = "RandomForest"

    team_1 = ["末日铁拳", "艾什", "猎空", "天使", "安娜"]
    team_2 = ["D.Va", "艾什", "士兵：76", "天使", "安娜"]
    test_map = "好莱坞"

    print("=== 1) 原始无偏见胜率 ===")
    p_no_bias = predict_no_bias(model_name, team_1, team_2, test_map)
    if p_no_bias is not None:
        print(f"Team1={team_1}\nTeam2={team_2}\n地图={test_map}")
        print(f"队伍1胜率: {p_no_bias:.3f}, 队伍2胜率: {1 - p_no_bias:.3f}")
    else:
        print("无法计算胜率")

    print("\n=== 队伍1自动换人 ===")
    orig_sp, out_h, in_h, new_p, delta = auto_team_swap(model_name, team_1, team_2, test_map, team="team_1")
    if out_h is not None:
        print(f"换下 [{out_h}], 换上 [{in_h}] => 新胜率 {new_p:.3f} (提升 {delta:.3f})")
    else:
        print("队伍1没有找到更好的换人方案")

    print("\n=== 队伍2自动换人 ===")
    orig_sp2, out_h2, in_h2, new_p2, delta2 = auto_team_swap(model_name, team_1, team_2, test_map, team="team_2")
    if out_h2 is not None:
        print(f"换下 [{out_h2}], 换上 [{in_h2}] => 新胜率 {new_p2:.3f} (提升 {delta2:.3f})")
    else:
        print("队伍2没有找到更好的换人方案")


    team_1_out = "源氏"
    print(f"\n=== 队伍1强制换下 [{team_1_out}] ===")
    orig_sp4, best_swap_info = replacement(model_name, team_1, team_2, test_map, team_1_out, team="team_1")
    if best_swap_info:
        hero_in, new_prob, dlt = best_swap_info
        print(f"换下 [源氏], 换上 [{hero_in}] => 新胜率={new_prob:.3f}, 提升={dlt:.3f}")
    else:
        print(f"没有找到更优的英雄来替换 [{team_1_out}]")

    team_2_out = "安娜"
    print(f"\n===  队伍2强制换下 [{team_2_out}] ===")
    orig_sp5, best_swap_info2 = replacement(model_name, team_1, team_2, test_map, team_2_out, team="team_2")
    if best_swap_info2:
        hero_in2, new_prob2, dlt2 = best_swap_info2
        print(f"换下 [安娜], 换上 [{hero_in2}] => 新胜率={new_prob2:.3f}, 提升={dlt2:.3f}")
    else:
        print(f"没有找到更优的英雄来替换 [{team_2_out}]")
