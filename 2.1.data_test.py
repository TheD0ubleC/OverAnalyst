import json
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib

# 解决中文显示问题
plt.rcParams["font.sans-serif"] = ["SimHei"]  # Windows 下的黑体
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 读取 JSON 文件
with open("Data/train_data_balanced.json", "r", encoding="utf-8") as f:
    data = json.load(f)

maps_data = data["maps"]
total_matches = len(maps_data)
print(f"共有 {total_matches} 场比赛数据。")

# 1) 计算 Team1 / Team2 的胜率
team1_wins = sum(1 for match in maps_data if match["map_result"] == "team_1_win")
team2_wins = total_matches - team1_wins

print(f"Team 1 胜率: {team1_wins / total_matches:.3f}")
print(f"Team 2 胜率: {team2_wins / total_matches:.3f}")

# 2) 统计每个英雄被选择的次数（初始 + 换人上场）
hero_pick_count = defaultdict(int)

for match in maps_data:
    # (a) 初始阵容
    for hero in match["team_1"]:
        hero_pick_count[hero] += 1
    for hero in match["team_2"]:
        hero_pick_count[hero] += 1

    # (b) 处理换人事件
    events = match.get("events", [])
    for ev in events:
        # team_1_changes: { out_hero: in_hero }
        for out_hero, in_hero in ev["team_1_changes"].items():
            hero_pick_count[in_hero] += 1
        # team_2_changes
        for out_hero, in_hero in ev["team_2_changes"].items():
            hero_pick_count[in_hero] += 1

# 3) 根据被选择次数做降序排序
sorted_picks = sorted(hero_pick_count.items(), key=lambda x: x[1], reverse=True)

# 4) 打印一下结果（可选）
print("\n=== 英雄被选择次数（从高到低） ===")
for hero, count in sorted_picks:
    print(f"{hero}: {count}")

# 5) 可视化（Bar Chart）
heroes = [item[0] for item in sorted_picks]
counts = [item[1] for item in sorted_picks]

plt.figure(figsize=(12, 6))
plt.bar(heroes, counts, color='steelblue')
plt.xticks(rotation=90)  # 英雄名字比较多，旋转以防遮挡
plt.xlabel("英雄")
plt.ylabel("被选择次数")
plt.title("各英雄被选择频次")
plt.tight_layout()  # 调整布局防止遮挡
plt.show()
