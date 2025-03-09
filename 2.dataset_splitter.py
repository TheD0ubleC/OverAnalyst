import os
import json
import random
from tqdm import tqdm

# 数据存储路径
DATA_FOLDER = "FinalMatches"
TRAIN_FILE = "Data/train_data.json"
TEST_FILE = "Data/test_data.json"
TEST_RATIO = 0.2  # 20% 作为测试集

def load_all_matches(data_folder=DATA_FOLDER):
    """
    从 `FinalMatches/` 读取所有比赛数据，返回一个列表。
    """
    all_matches = []

    if not os.path.exists(data_folder):
        print(f"目录 '{data_folder}' 不存在！")
        return []

    files = [f for f in os.listdir(data_folder) if f.endswith(".json")]
    if not files:
        print(f"'{data_folder}' 中没有 JSON 文件！")
        return []

    for filename in tqdm(files, desc="读取比赛数据"):
        file_path = os.path.join(data_folder, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "maps" in data and isinstance(data["maps"], list):
                    all_matches.extend(data["maps"])
        except Exception as e:
            print(f"读取 {filename} 失败: {e}")

    print(f"读取完成，共加载 {len(all_matches)} 场比赛")
    return all_matches

def split_dataset(matches, test_ratio=TEST_RATIO):
    """
    将数据集划分为训练集和测试集，返回 (train_set, test_set)
    """
    random.shuffle(matches)  # 打乱顺序
    split_idx = int(len(matches) * (1 - test_ratio))  # 计算 80% 训练集
    train_set = matches[:split_idx]
    test_set = matches[split_idx:]
    print(f"数据集已划分: 训练集 {len(train_set)} 场，测试集 {len(test_set)} 场")
    return train_set, test_set

def save_dataset(train_set, test_set, train_file=TRAIN_FILE, test_file=TEST_FILE):
    """
    将训练集 & 测试集分别保存为 JSON 文件
    """
    with open(train_file, "w", encoding="utf-8") as f:
        json.dump({"maps": train_set}, f, indent=4, ensure_ascii=False)
    
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump({"maps": test_set}, f, indent=4, ensure_ascii=False)

    print(f"训练集已保存到 {train_file}")
    print(f"测试集已保存到 {test_file}")

if __name__ == "__main__":
    # 读取比赛数据
    matches = load_all_matches()
    if not matches:
        print("数据为空，无法划分数据集！")
        exit()

    # 分割训练集 & 测试集
    train_set, test_set = split_dataset(matches)

    # 保存数据
    save_dataset(train_set, test_set)
