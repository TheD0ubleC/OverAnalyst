import predict_model


if __name__ == "__main__":
    model_name = "RandomForest" 

    team_1 = ['莱因哈特', '死神', '猎空', '天使', '禅雅塔']
    team_2 = ['莱因哈特', '死神', '猎空', '天使', '禅雅塔']
    test_map = "好莱坞"

    print("=== 1) 原始无偏见胜率 ===")
    p_no_bias = predict_model.predict_no_bias(model_name, team_1, team_2, test_map)
    if p_no_bias is not None:
        print(f"Team1={team_1}\nTeam2={team_2}\n地图={test_map}")
        print(f"队伍1胜率: {p_no_bias:.3f}, 队伍2胜率: {1 - p_no_bias:.3f}")
    else:
        print("无法计算胜率")

    print("\n=== 队伍1自动换人 ===")
    orig_sp, out_h, in_h, new_p, delta = predict_model.auto_team_swap(model_name, team_1, team_2, test_map, team="team_1")
    if out_h is not None:
        print(f"换下 [{out_h}], 换上 [{in_h}] => 新胜率 {new_p:.3f} (提升 {delta:.3f})")
    else:
        print("队伍1没有找到更好的换人方案")

    print("\n=== 队伍2自动换人 ===")
    orig_sp2, out_h2, in_h2, new_p2, delta2 = predict_model.auto_team_swap(model_name, team_1, team_2, test_map, team="team_2")
    if out_h2 is not None:
        print(f"换下 [{out_h2}], 换上 [{in_h2}] => 新胜率 {new_p2:.3f} (提升 {delta2:.3f})")
    else:
        print("队伍2没有找到更好的换人方案")


    team_1_out = "源氏"
    print(f"\n=== 队伍1强制换下 [{team_1_out}] ===")
    orig_sp4, best_swap_info = predict_model.replacement(model_name, team_1, team_2, test_map, team_1_out, team="team_1")
    if best_swap_info:
        hero_in, new_prob, dlt = best_swap_info
        print(f"换下 [源氏], 换上 [{hero_in}] => 新胜率={new_prob:.3f}, 提升={dlt:.3f}")
    else:
        print(f"没有找到更优的英雄来替换 [{team_1_out}]")

    team_2_out = "安娜"
    print(f"\n===  队伍2强制换下 [{team_2_out}] ===")
    orig_sp5, best_swap_info2 = predict_model.replacement(model_name, team_1, team_2, test_map, team_2_out, team="team_2")
    if best_swap_info2:
        hero_in2, new_prob2, dlt2 = best_swap_info2
        print(f"换下 [安娜], 换上 [{hero_in2}] => 新胜率={new_prob2:.3f}, 提升={dlt2:.3f}")
    else:
        print(f"没有找到更优的英雄来替换 [{team_2_out}]")
