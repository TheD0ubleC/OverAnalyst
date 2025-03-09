import os
import json
import pickle
import random
import numpy as np
from tqdm import tqdm
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer, LabelBinarizer
from sklearn.metrics import accuracy_score, log_loss

# ======================
# 📌 数据路径
# ======================
TRAIN_FILE = "Data/train_data.json"  # 训练集
TEST_FILE = "Data/test_data.json"    # 测试集
MODEL_DIR = "Models"                 # 存储模型的文件夹

# ======================
# 📌 全局变量
# ======================
MLB_HEROES = None   # 多标签编码器（英雄）
LB_MAPS = None      # 地图 One-hot 编码器

# ======================
# 📌 读取数据并生成 (X,y)
# ======================
def load_data(file_path):
    """
    解析比赛数据，生成 (X_samples, y_samples)
    X_sample: (team1英雄列表, team2英雄列表, map_name)
    y_sample: 1 表示 team1 胜利, 0 表示 team2 胜利

    其中还会捕捉“换人事件”后的阵容变化，每次换人都算一条新 (X,y)。
    """
    X_samples = []
    y_samples = []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for match in data["maps"]:
        # 基本字段
        map_name = match["map_name"]
        team_1 = match["team_1"][:]
        team_2 = match["team_2"][:]
        final_result = 1 if match["map_result"] == "team_1_win" else 0

        # 先随机交换一次 (team_1, team_2)；让模型不死记“team1=必胜队”
        if random.random() < 0.5:
            team_1, team_2 = team_2, team_1
            final_result = 1 - final_result

        # 加入初始阵容
        X_samples.append((team_1[:], team_2[:], map_name))
        y_samples.append(final_result)

        # 处理换人事件
        if "events" in match and isinstance(match["events"], list):
            for ev in match["events"]:
                # team_1_changes: {旧英雄: 新英雄}
                for out_hero, in_hero in ev.get("team_1_changes", {}).items():
                    if out_hero in team_1:
                        idx = team_1.index(out_hero)
                        team_1[idx] = in_hero

                # team_2_changes
                for out_hero, in_hero in ev.get("team_2_changes", {}).items():
                    if out_hero in team_2:
                        idx = team_2.index(out_hero)
                        team_2[idx] = in_hero

                # 再次随机交换
                if random.random() < 0.5:
                    team_1, team_2 = team_2, team_1
                    final_result = 1 - final_result

                # 每换一次人，就再记录一条新 (X,y)
                X_samples.append((team_1[:], team_2[:], map_name))
                y_samples.append(final_result)

    return X_samples, y_samples

# ======================
# 📌 生成特征矩阵
# ======================
def build_feature_matrix(X_samples, is_training=True):
    """
    将 (team_1, team_2, map_name) 转换为 One-hot 特征:
      - MLB_HEROES: MultiLabelBinarizer，用于把每个队伍的英雄列表编码
      - LB_MAPS:    LabelBinarizer，用于把 map_name 编码
    最终特征: [队伍1英雄One-hot] + [队伍2英雄One-hot] + [地图One-hot]
    """
    global MLB_HEROES, LB_MAPS

    team1_list, team2_list, maps_list = [], [], []

    for (t1, t2, map_name) in X_samples:
        team1_list.append(t1)
        team2_list.append(t2)
        maps_list.append(map_name)

    # (a) 编码 team_1 & team_2
    if is_training or MLB_HEROES is None:
        MLB_HEROES = MultiLabelBinarizer()
        MLB_HEROES.fit(team1_list + team2_list)

    team1_encoded = MLB_HEROES.transform(team1_list)
    team2_encoded = MLB_HEROES.transform(team2_list)

    # (b) 编码地图
    if is_training or LB_MAPS is None:
        LB_MAPS = LabelBinarizer()
        LB_MAPS.fit(maps_list)

    map_encoded = LB_MAPS.transform(maps_list)

    # 合并特征: team1 + team2 + map
    X_matrix = np.hstack([team1_encoded, team2_encoded, map_encoded])
    return X_matrix

# ======================
# 📌 标注翻转（可选）
# ======================
def partial_flip_labels(y, flip_ratio=0.3):
    """
    随机翻转标签：把 y 中的部分 1->0, 0->1
    旨在模拟数据噪音或标签不确定性。
    如果你不想翻转，可以把 flip_ratio=0.
    """
    y = np.array(y)
    n = len(y)
    flip_count = int(n * flip_ratio)
    flip_indices = np.random.choice(n, flip_count, replace=False)
    y_flipped = y.copy()
    y_flipped[flip_indices] = 1 - y_flipped[flip_indices]
    return y_flipped.tolist()

# ======================
# 📌 训练 & 保存随机森林
# ======================
def train_and_save_random_forest():
    # 1) 加载数据
    X_train, y_train = load_data(TRAIN_FILE)
    X_test, y_test = load_data(TEST_FILE)

    # 2) 可选：翻转标签，模拟噪音
    flip_ratio = 0.1  # 如果不想翻转，就设 0.0
    y_train = partial_flip_labels(y_train, flip_ratio)
    y_test = partial_flip_labels(y_test, flip_ratio)

    # 3) 构造特征矩阵
    X_train_matrix = build_feature_matrix(X_train, is_training=True)
    X_test_matrix = build_feature_matrix(X_test, is_training=False)

    # 4) 创建 & 训练 随机森林
    rf_model = RandomForestClassifier(
        n_estimators=512,  # 树数量
        max_depth=None,
        random_state=42,
        n_jobs=-1  # 使用全部CPU
    )
    print("\n🚀 正在训练随机森林...")
    rf_model.fit(X_train_matrix, np.array(y_train))

    # 5) 评估
    train_acc = rf_model.score(X_train_matrix, y_train)
    test_preds = rf_model.predict(X_test_matrix)
    test_acc = accuracy_score(y_test, test_preds)
    test_logloss = log_loss(y_test, rf_model.predict_proba(X_test_matrix))

    print(f"✅ 训练完成！")
    print(f"📊 训练集准确率: {train_acc:.3f}")
    print(f"📊 测试集准确率: {test_acc:.3f}")
    print(f"📊 测试集 Log Loss: {test_logloss:.3f}")

    # 6) 保存模型 & 编码器
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    # 用 pickle 存模型
    model_path = os.path.join(MODEL_DIR, "RandomForest.joblib")
    joblib.dump(rf_model, model_path)
    print(f"✅ 随机森林模型已保存到: {model_path}")

    # 保存编码器
    joblib.dump(MLB_HEROES, os.path.join(MODEL_DIR, "MLB_HEROES.joblib"))
    joblib.dump(LB_MAPS, os.path.join(MODEL_DIR, "LB_MAPS.joblib"))
    print("✅ 编码器已保存")

# ======================
# 📌 加载模型 & 预测示例
# ======================
def load_rf_model():
    """加载随机森林模型 & 编码器"""
    model_path = os.path.join(MODEL_DIR, "RandomForest.joblib")
    if not os.path.exists(model_path):
        print(f"❌ 模型不存在: {model_path}")
        return None, None, None

    rf_model = joblib.load(model_path)
    mlb_heroes = joblib.load(os.path.join(MODEL_DIR, "MLB_HEROES.joblib"))
    lb_maps = joblib.load(os.path.join(MODEL_DIR, "LB_MAPS.joblib"))
    return rf_model, mlb_heroes, lb_maps

def predict_match(team1_heroes, team2_heroes, map_name):
    """
    使用训练好的随机森林模型预测 team1 的胜率
    """
    rf_model, mlb_heroes, lb_maps = load_rf_model()
    if rf_model is None:
        return 0.5

    # 构造特征
    X = build_feature_matrix([(team1_heroes, team2_heroes, map_name)], is_training=False)
    # 预测
    win_prob = rf_model.predict_proba(X)[0][1]
    return win_prob

# ======================
# 📌 主函数
# ======================
if __name__ == "__main__":
    train_and_save_random_forest()
