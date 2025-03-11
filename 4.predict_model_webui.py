import flask
import predict_model

app = flask.Flask(__name__, template_folder='WebUI/templates', static_folder='WebUI/static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True      
app.config['UPLOAD_FOLDER'] = 'WebUI'
model_name = "RandomForest"

@app.route("/")
def index():
    return flask.render_template("index.html")

@app.route("/over_analyst/predict", methods=["POST"])
def predict():
    team_1 = flask.request.form.getlist("team_1[]")
    team_2 = flask.request.form.getlist("team_2[]")
    test_map = flask.request.form.get("map")

    # 计算胜率
    p_no_bias = predict_model.predict_no_bias(model_name, team_1, team_2, test_map)
    if p_no_bias is not None:
        team1_winrate = round(p_no_bias * 100, 1)
        team2_winrate = round((1 - p_no_bias) * 100, 1)
    else:
        return "无法计算胜率，请检查输入！", 400

    # 直接渲染 `predict.html`，传入计算结果
    return flask.render_template("predict.html",
                           team1=team_1,
                           team2=team_2,
                           map_name=test_map,
                           team1_winrate=team1_winrate,
                           team2_winrate=team2_winrate)


@app.route("/over_analyst/auto_team_swap", methods=["POST"])
def auto_team_swap():
    team_1 = flask.request.form.getlist("team_1[]")
    team_2 = flask.request.form.getlist("team_2[]")
    map = flask.request.form.get("map")
    team = flask.request.form.get("team")

    orig_sp, out_h, in_h, new_p, delta = predict_model.auto_team_swap(model_name, team_1, team_2, map, team=team)
    if out_h is not None:
        result = f"换下 [{out_h}], 换上 [{in_h}] => 新胜率 {new_p:.3f} (提升 {delta:.3f})"
    else:
        result = "队伍1没有找到更好的换人方案"
    return result

@app.route("/over_analyst/replacement", methods=["POST"])
def replacement():
    team_1 = flask.request.form.getlist("team_1[]")
    team_2 = flask.request.form.getlist("team_2[]")
    map = flask.request.form.get("map")
    team = flask.request.form.get("team")
    out_hero = flask.request.form.get("out_hero")

    orig_sp, best_swap_info = predict_model.replacement(model_name, team_1, team_2, map, out_hero, team=team)
    if best_swap_info:
        hero_in, new_prob, dlt = best_swap_info
        result = f"换下 [{out_hero}], 换上 [{hero_in}] => 新胜率={new_prob:.3f}, 提升={dlt:.3f}"
    else:
        result = f"没有找到更优的英雄来替换 [{out_hero}]"
    return result

@app.route("/over_analyst/build_page", methods=["POST"])
def build_page():
    team_1 = flask.request.form.getlist("team_1[]")
    team_2 = flask.request.form.getlist("team_2[]")
    test_map = flask.request.form.get("map")
    team1_winrate = flask.request.form.get("team1_winrate")
    team2_winrate = flask.request.form.get("team2_winrate")

    return flask.render_template("predict.html",
                           team1=team_1,
                           team2=team_2,
                           map_name=test_map,
                           team1_winrate=team1_winrate,
                           team2_winrate=team2_winrate)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)