import random
import json
import os
from sklearn.ensemble import RandomForestClassifier
from tqdm import tqdm
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MultiLabelBinarizer
import constants

# ========================================================
# 全局变量
# ========================================================

PAST_MATCHES = []  # 保存所有比赛数据（包括手动文件 + 生成的数据）
HERO_APPEARANCE_HISTORY = {}  # 记录英雄的出场次数
KNOWN_HEROES = set()  # 记录已经出现过的英雄
MODEL, MLB = None, None  # LogisticRegression 模型 & MultiLabelBinarizer

NUM_ITERATIONS = 1200  # 迭代次数
MATCHES_PER_ITERATION = 10  # 每次迭代生成的虚拟比赛数量

RETENTION = 100000000  # 保留最近的 10000 条比赛数据，超过的部分会被删除


# ========================================================
def load_manual_matches_from_files(folder_path="BaseData"):
    """
    用于读取基础真实数据
    从指定文件夹读取所有手动创建的比赛数据，并返回一个列表。
    将里面的 "maps" 信息提取并返回一个列表。
    """
    all_maps = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "maps" in data and isinstance(data["maps"], list):
                        all_maps.extend(data["maps"])
    return all_maps


def random_switch(my_team, enemy_team, hero_out, role_out):
    """在同职业里找一个没在当前队伍或敌队的英雄，随机换上。"""
    pool = (
        constants.TANK_HEROES
        if role_out == "Tank"
        else constants.DPS_HEROES if role_out == "DPS" else constants.SUPPORT_HEROES
    )
    available_heroes = [h for h in pool if (h not in my_team) and (h not in enemy_team)]
    if available_heroes:
        return random.choice(available_heroes)
    return None


def get_role(hero):
    """根据英雄名称判断其职业类别。"""
    if hero in constants.TANK_HEROES:
        return "Tank"
    elif hero in constants.DPS_HEROES:
        return "DPS"
    elif hero in constants.SUPPORT_HEROES:
        return "Support"
    return None


def generate_team(is_weaker=False, used_heroes=None):
    """
    如果有历史数据，优先选胜率高/低英雄；如果没有历史数据，随机选。
    weaker队伍选胜率相对低的英雄。
    """
    if used_heroes is None:
        used_heroes = set()
    
    # 如果无历史数据，就直接随机
    if not PAST_MATCHES:
        tank = random.choice([h for h in constants.TANK_HEROES if h not in used_heroes])
        dps = random.sample([h for h in constants.DPS_HEROES if h not in used_heroes], 2)
        support = random.sample([h for h in constants.SUPPORT_HEROES if h not in used_heroes], 2)
        return [tank] + dps + support
    
    # 统计历史中英雄的胜场数
    hero_win_freq = {}
    for match in PAST_MATCHES:
        winner = "team_1" if match["map_result"] == "team_1_win" else "team_2"
        for hero in match[winner]:
            hero_win_freq[hero] = hero_win_freq.get(hero, 0) + 1
    
    sorted_heroes = sorted(hero_win_freq.items(), key=lambda x: x[1], reverse=True)
    
    known_tanks = [h for h, _ in sorted_heroes if h in constants.TANK_HEROES and h in KNOWN_HEROES] or \
                  [h for h in constants.TANK_HEROES if h in KNOWN_HEROES]
    known_dps = [h for h, _ in sorted_heroes if h in constants.DPS_HEROES and h in KNOWN_HEROES] or \
                [h for h in constants.DPS_HEROES if h in KNOWN_HEROES]
    known_supports = [h for h, _ in sorted_heroes if h in constants.SUPPORT_HEROES and h in KNOWN_HEROES] or \
                     [h for h in constants.SUPPORT_HEROES if h in KNOWN_HEROES]
    
    # 若是弱队，就更倾向于选择胜场数较低的英雄
    # 若是强队，就倾向选择胜场数较高的英雄
    if is_weaker:
        available_tanks = [h for h in known_tanks[-3:] if h not in used_heroes] or \
                          [h for h in constants.TANK_HEROES if h not in used_heroes]
        available_dps = [h for h in known_dps[-5:] if h not in used_heroes] or \
                        [h for h in constants.DPS_HEROES if h not in used_heroes]
        available_supports = [h for h in known_supports[-5:] if h not in used_heroes] or \
                             [h for h in constants.SUPPORT_HEROES if h not in used_heroes]
    else:
        available_tanks = [h for h in known_tanks[:3] if h not in used_heroes] or \
                          [h for h in constants.TANK_HEROES if h not in used_heroes]
        available_dps = [h for h in known_dps[:5] if h not in used_heroes] or \
                        [h for h in constants.DPS_HEROES if h not in used_heroes]
        available_supports = [h for h in known_supports[:5] if h not in used_heroes] or \
                             [h for h in constants.SUPPORT_HEROES if h not in used_heroes]
    
    tank = random.choice(available_tanks)
    dps_team = random.sample(available_dps, 2) if len(available_dps) >= 2 else \
               random.sample([h for h in constants.DPS_HEROES if h not in used_heroes], 2)
    support_team = random.sample(available_supports, 2) if len(available_supports) >= 2 else \
                   random.sample([h for h in constants.SUPPORT_HEROES if h not in used_heroes], 2)
    
    return [tank] + dps_team + support_team



def is_countered_by_enemy(hero, used_heroes):
    """
    判断该英雄是否被已选队伍克制
    - 这里可以结合 `hero_counters()` 来判断
    """
    for enemy in used_heroes:
        if hero_counters(enemy, hero):
            return True
    return False


def hero_counters(heroA, heroB):
    """
    检查 heroA 是否克制 heroB。
    现在 COUNTER_PAIRS 的结构是：
    [
        ["莱因哈特", ["路霸", "堡垒", "法老之鹰"]],
        ["温斯顿", ["死神", "布丽吉塔"]]
    ]
    """
    for pair in constants.COUNTER_PAIRS:
        if pair[0] == heroA and heroB in pair[1]:
            return True
    return False


def find_heroes_that_counter(enemy_hero):
    """
    查找所有克制 enemy_hero 的英雄。
    """
    result = []
    for pair in constants.COUNTER_PAIRS:
        if enemy_hero in pair[1]:  # 如果 enemy_hero 在克制列表里
            result.append(pair[0])  # 取出克制它的英雄
    return result


def apply_counter_synergy(team_1, team_2, base_prob):
    """
    如果 team_1 有 A, team_2 有 B, 且 [A, B] 在 COUNTER_PAIRS 中，
    team_1 克制 team_2：
      -> 75% 概率 +0.05 胜率
      -> 25% 中 2/3 不变, 1/3 -0.2
    可能出现多个克制对，会多次叠加。
    """
    synergy_count = 0

    # 检查 team_1克制team_2 的组合
    for a in team_1:
        for b in team_2:
            if hero_counters(a, b):
                synergy_count += 1

    # 对每一个克制对，施加一次概率影响
    for _ in range(synergy_count):
        r = random.random()
        if r < 0.75:
            base_prob += 0.05  # 75% 概率 -> 增加一点
        else:
            # 25% -> 2/3不变, 1/3 -0.2
            r2 = random.random()
            if r2 < 0.6667:
                pass
            else:
                base_prob -= 0.2
        # 限制范围
        base_prob = max(0.05, min(0.95, base_prob))

    return base_prob


def apply_reverse_pick_penalty(
    team_1_changes, team_2_changes, team_1, team_2, base_prob
):
    """
    如果队伍在这一次事件里换上的英雄，正好被对面克制，
    就有一个小概率事件会触发“发神经”：
      - 70% 大幅降低胜率 ( -0.2 )
      - 24% 不变
      - 6% 反而 +0.05
    （你可以调节这些概率和数值）

    注意：
    1. 只有当本次 actually 出现了换人（team_1_changes/team_2_changes不空）时才执行。
    2. 先判断 是否“正好被克制”，再判定 是否触发“发神经”随机事件。
    """
    # 发神经事件触发的总概率，比如 10%
    # 你可根据需求改小/改大
    RANDOM_TRIGGER_PROB = 0.10

    def check_and_apply(new_heroes, enemy_team):
        nonlocal base_prob
        # 对每个 newly_in hero，看看是否被对面某个人克制
        for hero_in in new_heroes:
            # 小概率才判定“发神经”
            if random.random() < RANDOM_TRIGGER_PROB:
                # 检查对面有没有克制 hero_in 的人
                # 如果 (enemy_hero, hero_in) 在 COUNTER_PAIRS
                # 表示 enemy_hero 克制 hero_in
                is_countered = False
                for ehero in enemy_team:
                    if hero_counters(ehero, hero_in):
                        is_countered = True
                        break
                # 如果确实被克制，就执行多分支效果
                if is_countered:
                    r = random.random()
                    if r < 0.70:
                        # 70% -> -0.2
                        base_prob -= 0.2
                    elif r < 0.94:
                        # 24% -> 不变
                        pass
                    else:
                        # 6% -> +0.05
                        base_prob += 0.05

                    base_prob = max(0.05, min(0.95, base_prob))

    # team_1 换上的英雄
    if team_1_changes:
        new_heroes_1 = list(team_1_changes.values())
        check_and_apply(new_heroes_1, team_2)

    # team_2 换上的英雄
    if team_2_changes:
        new_heroes_2 = list(team_2_changes.values())
        check_and_apply(new_heroes_2, team_1)

    return base_prob


def predict_win_probability(team_1, team_2, team_1_changes, team_2_changes):
    """根据模型或随机逻辑，预测 team_1 的胜率，并在最后阶段应用发神经反向克制。"""
    combined_team = team_1 + team_2
    unknown_heroes = [h for h in combined_team if h not in KNOWN_HEROES]

    # 1) 基础胜率
    if unknown_heroes:
        # 对未知英雄采用“奇招”机制
        if random.random() < 0.2:  # 20% 概率奇招 -> 胜率0.75~0.95
            base_prob = random.uniform(0.75, 0.95)
        else:  # 否则0.3~0.55
            base_prob = random.uniform(0.3, 0.55)
    else:
        if MODEL is not None and MLB is not None:
            X = MLB.transform([combined_team])
            base_prob = MODEL.predict_proba(X)[0][1]
        else:
            base_prob = 0.5

    # 2) 加强随机波动
    base_prob += random.uniform(-0.15, 0.15)
    base_prob = max(0.05, min(0.95, base_prob))

    # 3) 应用常规克制链
    base_prob = apply_counter_synergy(team_1, team_2, base_prob)

    # 4) 最后再应用“发神经反向克制”：
    #    - 小概率出现选了个被对面克制的英雄
    #    - 70% 大降胜率, 24% 不变, 6% 小幅增胜率
    base_prob = apply_reverse_pick_penalty(
        team_1_changes, team_2_changes, team_1, team_2, base_prob
    )

    # 最终保底限制
    base_prob = max(0.05, min(0.95, base_prob))
    return base_prob


def get_new_status(win_prob):
    """
    当 win_prob > 0.6 时 -> "team_1_advantage"
    当 win_prob < 0.4 时 -> "team_2_advantage"
    否则(0.4 ~ 0.6) -> 在 20% 概率下 "balanced"，80% 随机给一方优势。
    """
    if win_prob > 0.6:
        return "team_1_advantage"
    elif win_prob < 0.4:
        return "team_2_advantage"
    else:
        return random.choices(
            ["balanced", "team_1_advantage", "team_2_advantage"], weights=[20, 40, 40]
        )[0]


def generate_match():
    map_name = random.choice(constants.MAPS)  # 随机选择地图
    weaker_team = random.choice(["team_1", "team_2"])  # 随机选择弱队
    starting_status = random.choice(constants.STATUS)  # 随机选择初始状态

    used_heroes = set()  # 记录已经使用过的英雄
    # 生成队伍
    initial_team_1 = generate_team(
        is_weaker=(weaker_team == "team_1"), used_heroes=used_heroes
    )
    used_heroes.update(initial_team_1)
    initial_team_2 = generate_team(
        is_weaker=(weaker_team == "team_2"), used_heroes=used_heroes
    )

    current_team_1 = initial_team_1[:]
    current_team_2 = initial_team_2[:]

    events = []
    current_status = starting_status

    # 随机换人次数 (2 ~ 6 次)
    for _ in range(random.randint(2, 6)):
        team_1_changes = {}
        team_2_changes = {}

        # ============ team_1 换人逻辑 ============
        if (random.random() < 0.5) or (
            weaker_team == "team_1" and current_status != "team_1_advantage"
        ):

            hero_out = random.choice(current_team_1)
            role_out = get_role(hero_out)
            if role_out is not None:
                # 先检查对面是否克制hero_out
                is_countered = None
                for enemy_hero in current_team_2:
                    if hero_counters(enemy_hero, hero_out):
                        is_countered = enemy_hero
                        break

                if is_countered:
                    # 找到能克制 is_countered 的英雄
                    possible_counter_heroes = find_heroes_that_counter(is_countered)
                    # 过滤同职业可用英雄
                    pool = (
                        constants.TANK_HEROES
                        if role_out == "Tank"
                        else (
                            constants.DPS_HEROES
                            if role_out == "DPS"
                            else constants.SUPPORT_HEROES
                        )
                    )
                    possible_counter_heroes = [
                        x
                        for x in possible_counter_heroes
                        if x in pool
                        and x not in current_team_1
                        and x not in current_team_2
                    ]

                    # 60% 概率换这个反克制英雄
                    if possible_counter_heroes and (random.random() < 0.6):
                        hero_in = random.choice(possible_counter_heroes)
                        team_1_changes[hero_out] = hero_in
                        idx = current_team_1.index(hero_out)
                        current_team_1[idx] = hero_in
                    else:
                        # 否则就普通随机换人
                        hero_in = random_switch(
                            current_team_1, current_team_2, hero_out, role_out
                        )
                        if hero_in:
                            team_1_changes[hero_out] = hero_in
                            idx = current_team_1.index(hero_out)
                            current_team_1[idx] = hero_in
                else:
                    # 不被对面克制 -> 普通换人
                    hero_in = random_switch(
                        current_team_1, current_team_2, hero_out, role_out
                    )
                    if hero_in:
                        team_1_changes[hero_out] = hero_in
                        idx = current_team_1.index(hero_out)
                        current_team_1[idx] = hero_in

        # ============ team_2 换人逻辑 ============
        if (random.random() < 0.5) or (
            weaker_team == "team_2" and current_status != "team_2_advantage"
        ):
            hero_out_2 = random.choice(current_team_2)
            role_out_2 = get_role(hero_out_2)
            if role_out_2 is not None:
                is_countered = None
                for enemy_hero in current_team_1:
                    if hero_counters(enemy_hero, hero_out_2):
                        is_countered = enemy_hero
                        break

                if is_countered:
                    possible_counter_heroes = find_heroes_that_counter(is_countered)
                    pool = (
                        constants.TANK_HEROES
                        if role_out_2 == "Tank"
                        else (
                            constants.DPS_HEROES
                            if role_out_2 == "DPS"
                            else constants.SUPPORT_HEROES
                        )
                    )
                    possible_counter_heroes = [
                        x
                        for x in possible_counter_heroes
                        if x in pool
                        and x not in current_team_2
                        and x not in current_team_1
                    ]

                    if possible_counter_heroes and (random.random() < 0.6):
                        hero_in = random.choice(possible_counter_heroes)
                        team_2_changes[hero_out_2] = hero_in
                        idx = current_team_2.index(hero_out_2)
                        current_team_2[idx] = hero_in
                    else:
                        hero_in = random_switch(
                            current_team_2, current_team_1, hero_out_2, role_out_2
                        )
                        if hero_in:
                            team_2_changes[hero_out_2] = hero_in
                            idx = current_team_2.index(hero_out_2)
                            current_team_2[idx] = hero_in
                else:
                    hero_in = random_switch(
                        current_team_2, current_team_1, hero_out_2, role_out_2
                    )
                    if hero_in:
                        team_2_changes[hero_out_2] = hero_in
                        idx = current_team_2.index(hero_out_2)
                        current_team_2[idx] = hero_in

        # 如果没有任何换人，就跳过不记录事件
        if not team_1_changes and not team_2_changes:
            continue

        # 如果确实发生了换人，则计算胜率 & 更新状态
        # 注意这里将本次换人传给 predict_win_probability，让其做“发神经”逻辑
        win_prob = predict_win_probability(
            current_team_1, current_team_2, team_1_changes, team_2_changes
        )
        current_status = get_new_status(win_prob)

        events.append(
            {
                "team_1_changes": team_1_changes,
                "team_2_changes": team_2_changes,
                "new_status": current_status,
            }
        )

    # 最终根据状态判定谁赢
    map_result = "team_1_win" if current_status == "team_1_advantage" else "team_2_win"
    return {
        "map_name": map_name,
        "weaker": weaker_team,
        "starting_status": starting_status,
        "team_1": initial_team_1,
        "team_2": initial_team_2,
        "events": events,
        "map_result": map_result,
    }


def generate_matches(num_matches=10, desc="Generating matches"):
    """批量生成指定数量的比赛。"""
    matches = []
    for _ in tqdm(range(num_matches), desc=desc, unit="match"):
        match = generate_match()
        matches.append(match)
    return matches


def train_win_predictor(past_matches, model_type="random_forest"):
    """
    训练胜率预测模型（支持多线程）
    - model_type 可选 "random_forest" 或 "logistic_regression"
    - 训练数据来源：past_matches（真实数据 + 生成数据）

    返回：
    - 训练好的模型
    - MultiLabelBinarizer（用于处理英雄数据）
    """
    if len(past_matches) < 2:
        return None, None  # 数据不足时，不训练模型

    mlb = MultiLabelBinarizer()
    X = mlb.fit_transform(
        [m["team_1"] + m["team_2"] for m in past_matches]
    )  # 英雄特征编码
    y = [
        1 if m["map_result"] == "team_1_win" else 0 for m in past_matches
    ]  # 结果转换成 0/1

    # 选择模型（默认随机森林）
    if model_type == "random_forest":
        model = RandomForestClassifier(
            n_estimators=128, random_state=42, max_depth=10, n_jobs=24
        )  # 多线程加速
    elif model_type == "logistic_regression":
        model = LogisticRegression(max_iter=1000, n_jobs=25)  # 逻辑回归也支持多线程
    else:
        raise ValueError(
            "Unsupported model type. Choose 'random_forest' or 'logistic_regression'."
        )

    # 训练模型
    model.fit(X, y)
    return model, mlb


def main():
    # 读取真实的基础数据
    manual_maps = load_manual_matches_from_files(folder_path="BaseData")
    print(f"从本地 JSON 文件加载 {len(manual_maps)} 条比赛数据。")
    # 将手动创建的比赛数据添加到 PAST_MATCHES 中
    PAST_MATCHES.extend(manual_maps)
    for m in manual_maps:
        KNOWN_HEROES.update(m["team_1"])
        KNOWN_HEROES.update(m["team_2"])
    print(
        f"总英雄数量：{len(constants.ALL_HEROES)} | 已知英雄数量：{len(KNOWN_HEROES)} | 未知英雄数量：{len(constants.ALL_HEROES) - len(KNOWN_HEROES)}"
    )

    # 生成比赛数据
    # iteration 代表迭代次数
    for iteration in range(NUM_ITERATIONS):
        print(
            f"\n[迭代 {iteration+1}/{NUM_ITERATIONS}] 生成 {MATCHES_PER_ITERATION} 条比赛数据..."
        )
        new_matches = generate_matches(
            num_matches=MATCHES_PER_ITERATION, desc=f"生成次数 {iteration+1}"
        )
        # 加入全局
        PAST_MATCHES.extend(new_matches)
        PAST_MATCHES[:] = PAST_MATCHES[-RETENTION:]
        # 更新英雄
        for nm in new_matches:
            KNOWN_HEROES.update(nm["team_1"])
            KNOWN_HEROES.update(nm["team_2"])

        # 训练/重训模型
        print("生成后的训练模型...")
        MODEL, MLB = train_win_predictor(PAST_MATCHES)
        if MODEL is None:
            print("还没有足够的数据进行训练。")
        else:
            print(f"模型已更新。迄今为止的比赛总数 {len(PAST_MATCHES)}")

    # ============ 生成最终可行的比赛数据 ============
    final_num = 1000
    print(f"\n>>> 使用训练后的模型生成最终 {final_num} 比赛数据(可行数据)...")
    final_data = generate_matches(num_matches=final_num, desc="Final Generation")

    # 将这些数据写入文件夹
    final_folder = "FinalMatches"
    if not os.path.exists(final_folder):
        os.makedirs(final_folder)

    for i, match in enumerate(final_data):
        file_path = os.path.join(final_folder, f"final_match_{i:04d}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"maps": [match]}, f, indent=4, ensure_ascii=False)

    print(f"完成！最终匹配结果已保存到文件夹中： {final_folder}")


if __name__ == "__main__":
    main()
