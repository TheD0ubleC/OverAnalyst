// ============================
//  1) 英雄池 + 工具函数
// ============================
const dpsHeroes = [
    "死神", "猎空", "半藏", "托比昂", "法老之鹰", "黑百合", "堡垒", "秩序之光",
    "源氏", "卡西迪", "狂鼠", "士兵：76", "美", "黑影", "索杰恩", "艾什", "回声", "探奇"
];
const tankHeroes = [
    "莱因哈特", "温斯顿", "路霸", "查莉娅", "D.Va", "末日铁拳", "奥丽莎", "破坏球",
    "渣客女王", "西格玛", "拉玛刹", "毛加", "骇灾"
];
const supportHeroes = [
    "天使", "禅雅塔", "卢西奥", "安娜", "布丽吉塔", "莫伊拉", "巴蒂斯特", "雾子",
    "生命之梭", "伊拉锐", "朱诺"
];

/** 判断某个英雄的职责 */
function getRole(hero) {
    if (tankHeroes.includes(hero)) return "tank";
    if (dpsHeroes.includes(hero)) return "dps";
    if (supportHeroes.includes(hero)) return "support";
    return "";
}

// ============================
//  2) 全局数据
// ============================
let matchData = {
    // 地图信息
    map_name: "",
    weaker: "team_1",
    starting_status: "team_1_advantage",
    map_result: "team_1_win",

    /** 初始阵容（只在最终 JSON 输出） */
    team_1: [
        tankHeroes[0],
        dpsHeroes[0],
        dpsHeroes[1],
        supportHeroes[0],
        supportHeroes[1]
    ],
    team_2: [
        tankHeroes[1],
        dpsHeroes[2],
        dpsHeroes[3],
        supportHeroes[2],
        supportHeroes[3]
    ],

    /** 已确认事件 */
    events: []
};

/**
 * 当前阵容 (会被事件修改)，以便事件之间继承
 */
let currentTeam1 = [...matchData.team_1];
let currentTeam2 = [...matchData.team_2];

/** 当前待编辑事件 */
let pendingEvent = {
    team_1_changes: {},
    team_2_changes: {},
    new_status: ""
};

// ============================
//  3) 页面加载
// ============================
window.onload = () => {
    fillTeamDropdowns();
    renderInitialPreview();
    setupListeners();
    renderEventList();
    renderPendingChangesView();
    updateHeroChangeDropdowns();
    refreshUI(); // 初次刷新一下
};

// ============================
//  4) 填充“初始阵容”下拉
// ============================
function fillTeamDropdowns() {
    fillDropdown("team1_1", tankHeroes, matchData.team_1[0]);
    fillDropdown("team1_2", dpsHeroes, matchData.team_1[1]);
    fillDropdown("team1_3", dpsHeroes, matchData.team_1[2]);
    fillDropdown("team1_4", supportHeroes, matchData.team_1[3]);
    fillDropdown("team1_5", supportHeroes, matchData.team_1[4]);

    fillDropdown("team2_1", tankHeroes, matchData.team_2[0]);
    fillDropdown("team2_2", dpsHeroes, matchData.team_2[1]);
    fillDropdown("team2_3", dpsHeroes, matchData.team_2[2]);
    fillDropdown("team2_4", supportHeroes, matchData.team_2[3]);
    fillDropdown("team2_5", supportHeroes, matchData.team_2[4]);
}

/** 给 <select> 填充英雄选项，并设置默认值 */
function fillDropdown(selectId, heroArray, defaultValue) {
    const sel = document.getElementById(selectId);
    sel.innerHTML = "";
    heroArray.forEach(h => {
        const opt = document.createElement("option");
        opt.value = h;
        opt.textContent = h;
        sel.appendChild(opt);
    });
    sel.value = defaultValue || heroArray[0];
}

// ============================
//  5) 显示顶部“初始阵容”
// ============================
function renderInitialPreview() {
    document.getElementById("initialTeam1Preview").textContent =
        "队伍 1: " + matchData.team_1.join(" | ");
    document.getElementById("initialTeam2Preview").textContent =
        "队伍 2: " + matchData.team_2.join(" | ");
}

// ============================
//  6) 设置监听器
// ============================
function setupListeners() {
    // 地图信息
    document.getElementById("map_name").addEventListener("input", e => {
        matchData.map_name = e.target.value;
        refreshUI();
    });
    document.getElementById("weaker").addEventListener("change", e => {
        matchData.weaker = e.target.value;
        refreshUI();
    });
    document.getElementById("starting_status").addEventListener("change", e => {
        matchData.starting_status = e.target.value;
        refreshUI();
    });
    document.getElementById("map_result").addEventListener("change", e => {
        matchData.map_result = e.target.value;
        refreshUI();
    });

    // 队伍1 下拉
    ["team1_1", "team1_2", "team1_3", "team1_4", "team1_5"].forEach((id, idx) => {
        document.getElementById(id).addEventListener("change", e => {
            let newHero = e.target.value;
            matchData.team_1[idx] = newHero; // 初始阵容
            currentTeam1[idx] = newHero;     // 当前阵容
            refreshUI();
        });
    });
    // 队伍2 下拉
    ["team2_1", "team2_2", "team2_3", "team2_4", "team2_5"].forEach((id, idx) => {
        document.getElementById(id).addEventListener("change", e => {
            let newHero = e.target.value;
            matchData.team_2[idx] = newHero;
            currentTeam2[idx] = newHero;
            refreshUI();
        });
    });

    // 事件后优势
    document.getElementById("event_new_status").addEventListener("change", e => {
        pendingEvent.new_status = e.target.value;
        refreshUI();
    });

    // 事件换人下拉
    document.getElementById("change_team").addEventListener("change", () => {
        updateHeroChangeDropdowns();
        refreshUI();
    });
    document.getElementById("change_old_hero").addEventListener("change", () => {
        updateHeroChangeDropdowns();
        refreshUI();
    });
}

// ============================
//  7) 更新“事件：换下/换上”下拉
// ============================
function updateHeroChangeDropdowns() {
    const changeTeamSel = document.getElementById("change_team");
    const oldHeroSel = document.getElementById("change_old_hero");
    const newHeroSel = document.getElementById("change_new_hero");

    const savedOld = oldHeroSel.value;
    const savedNew = newHeroSel.value;

    // 如果是队伍1，就用 currentTeam1，否则 currentTeam2
    let curTeam = (changeTeamSel.value === "team_1_changes")
        ? currentTeam1 : currentTeam2;

    // “换下”下拉
    oldHeroSel.innerHTML = '<option value="">原英雄</option>';
    curTeam.forEach(hero => {
        const opt = document.createElement("option");
        opt.value = hero;
        opt.textContent = hero;
        oldHeroSel.appendChild(opt);
    });
    if (curTeam.includes(savedOld)) {
        oldHeroSel.value = savedOld;
    } else {
        oldHeroSel.value = "";
    }

    // “换上”下拉
    newHeroSel.innerHTML = '<option value="">新英雄</option>';
    const role = getRole(oldHeroSel.value);
    let heroPool = [];
    if (role === "tank") heroPool = tankHeroes;
    else if (role === "dps") heroPool = dpsHeroes;
    else if (role === "support") heroPool = supportHeroes;

    heroPool.forEach(h => {
        const opt = document.createElement("option");
        opt.value = h;
        opt.textContent = h;
        newHeroSel.appendChild(opt);
    });
    if (heroPool.includes(savedNew)) {
        newHeroSel.value = savedNew;
    } else {
        newHeroSel.value = "";
    }
}

// ============================
//  8) 添加换人记录
// ============================
function addHeroChange() {
    const changeTeamVal = document.getElementById("change_team").value;
    const oldH = document.getElementById("change_old_hero").value;
    const newH = document.getElementById("change_new_hero").value;

    if (!oldH || !newH) {
        alert("请选择要换下的英雄 和 换上的英雄！");
        return;
    }
    if (oldH === newH) {
        alert("不能换成相同英雄！");
        return;
    }

    // 写入 pendingEvent
    if (changeTeamVal === "team_1_changes") {
        pendingEvent.team_1_changes[oldH] = newH;
    } else {
        pendingEvent.team_2_changes[oldH] = newH;
    }

    // 重置
    document.getElementById("change_team").value = "team_1_changes";
    document.getElementById("change_old_hero").value = "";
    document.getElementById("change_new_hero").value = "";

    refreshUI();
    alert("换人记录已添加到当前事件！");
}

// ============================
//  9) 显示当前事件(未确认)
// ============================
function renderPendingChangesView() {
    const view = document.getElementById("pendingChangesView");
    const t1 = pendingEvent.team_1_changes;
    const t2 = pendingEvent.team_2_changes;

    if (!Object.keys(t1).length && !Object.keys(t2).length) {
        view.innerHTML = "<p>暂无换人记录</p>";
        return;
    }

    let html = "<p><strong>队伍 1 换人:</strong></p>";
    if (!Object.keys(t1).length) {
        html += "<p>无</p>";
    } else {
        for (let oldH in t1) {
            html += `<p>${oldH} -> ${t1[oldH]}</p>`;
        }
    }

    html += "<p><strong>队伍 2 换人:</strong></p>";
    if (!Object.keys(t2).length) {
        html += "<p>无</p>";
    } else {
        for (let oldH in t2) {
            html += `<p>${oldH} -> ${t2[oldH]}</p>`;
        }
    }

    if (pendingEvent.new_status) {
        html += `<p>事件后优势: ${pendingEvent.new_status}</p>`;
    } else {
        html += `<p>事件后优势: 无</p>`;
    }

    view.innerHTML = html;
}

// ============================
// 10) 确认事件
// ============================
function confirmEvent() {
    const t1Keys = Object.keys(pendingEvent.team_1_changes);
    const t2Keys = Object.keys(pendingEvent.team_2_changes);

    if (!t1Keys.length && !t2Keys.length && !pendingEvent.new_status) {
        alert("当前事件没有任何换人，也没有事件后优势！");
        return;
    }

    // 把换人应用到 currentTeam
    applyChangesToCurrentTeam("team_1", pendingEvent.team_1_changes);
    applyChangesToCurrentTeam("team_2", pendingEvent.team_2_changes);

    // 记录事件
    const newEvent = {
        team_1_changes: { ...pendingEvent.team_1_changes },
        team_2_changes: { ...pendingEvent.team_2_changes },
        new_status: pendingEvent.new_status || ""
    };
    matchData.events.push(newEvent);

    // 清空
    pendingEvent = { team_1_changes: {}, team_2_changes: {}, new_status: "" };
    document.getElementById("event_new_status").value = "";

    refreshUI();
    alert("本次事件已确认！后续事件将继承新的阵容");
}

/** 应用“old->new”到 currentTeam1/currentTeam2 */
function applyChangesToCurrentTeam(teamKey, changes) {
    let curTeam = (teamKey === "team_1") ? currentTeam1 : currentTeam2;
    for (let oldH in changes) {
        let newH = changes[oldH];
        let idx = curTeam.indexOf(oldH);
        if (idx !== -1) {
            curTeam[idx] = newH;
        }
    }
}

// ============================
// 11) 渲染事件列表 + 删除事件
// ============================
function renderEventList() {
    const eventListDiv = document.getElementById("eventList");
    eventListDiv.innerHTML = "";

    if (!matchData.events.length) {
        eventListDiv.innerHTML = "<p>暂无事件</p>";
        return;
    }

    matchData.events.forEach((ev, idx) => {
        const wrapper = document.createElement("div");
        wrapper.className = "event-item";

        const title = document.createElement("p");
        title.style.fontWeight = "bold";
        title.textContent = `事件 ${idx + 1}:`;
        wrapper.appendChild(title);

        // 队伍1
        const t1Keys = Object.keys(ev.team_1_changes);
        if (t1Keys.length) {
            const t1Title = document.createElement("p");
            t1Title.textContent = "队伍 1 换人:";
            wrapper.appendChild(t1Title);
            t1Keys.forEach(oldH => {
                const line = document.createElement("p");
                line.textContent = `${oldH} -> ${ev.team_1_changes[oldH]}`;
                wrapper.appendChild(line);
            });
        } else {
            const p1 = document.createElement("p");
            p1.textContent = "队伍 1 无换人";
            wrapper.appendChild(p1);
        }

        // 队伍2
        const t2Keys = Object.keys(ev.team_2_changes);
        if (t2Keys.length) {
            const t2Title = document.createElement("p");
            t2Title.textContent = "队伍 2 换人:";
            wrapper.appendChild(t2Title);
            t2Keys.forEach(oldH => {
                const line = document.createElement("p");
                line.textContent = `${oldH} -> ${ev.team_2_changes[oldH]}`;
                wrapper.appendChild(line);
            });
        } else {
            const p2 = document.createElement("p");
            p2.textContent = "队伍 2 无换人";
            wrapper.appendChild(p2);
        }

        // 事件后优势
        const statusLine = document.createElement("p");
        statusLine.textContent = ev.new_status
            ? `事件后优势: ${ev.new_status}`
            : "事件后优势: 无";
        wrapper.appendChild(statusLine);

        // 删除事件按钮
        const delBtn = document.createElement("button");
        delBtn.textContent = "删除事件";
        delBtn.style.marginTop = "8px";
        delBtn.onclick = () => {
            matchData.events.splice(idx, 1);
            refreshUI();
            alert(`已删除事件 ${idx + 1}！`);
        };
        wrapper.appendChild(delBtn);

        eventListDiv.appendChild(wrapper);
    });
}

// ============================
// 12) 全局刷新：更新所有UI
// ============================
function refreshUI() {
    // 让页面上的输入框/下拉框与 matchData 保持一致
    document.getElementById("map_name").value = matchData.map_name;
    document.getElementById("weaker").value = matchData.weaker;
    document.getElementById("starting_status").value = matchData.starting_status;
    document.getElementById("map_result").value = matchData.map_result;

    // 再填充初始阵容下拉
    fillTeamDropdowns();
    // 显示顶部初始阵容
    renderInitialPreview();
    // 当前事件换人
    renderPendingChangesView();
    // 事件列表
    renderEventList();
    // 事件“换人”下拉
    updateHeroChangeDropdowns();
}

// ============================
// 13) 生成 JSON (带 Highlight.js)
// ============================
function generateJSON() {
    const fullData = {
        "maps": [
            {
                "map_name": matchData.map_name,
                "weaker": matchData.weaker,
                "starting_status": matchData.starting_status,
                "team_1": matchData.team_1, // 初始阵容
                "team_2": matchData.team_2,
                "events": matchData.events,
                "map_result": matchData.map_result
            }
        ],
        "final_result": matchData.map_result
    };

    const jsonStr = JSON.stringify(fullData, null, 2);
    const out = document.getElementById("jsonOutput");
    out.textContent = jsonStr;

    // Highlight.js
    out.classList.remove("hljs");
    window.hljs.highlightElement(out);
}

// ============================
// 14) 反向导入 JSON
// ============================
function importJSON() {
    const area = document.getElementById("importJsonTextarea");
    const raw = area.value.trim();
    if (!raw) {
        alert("请先粘贴 JSON！");
        return;
    }
    let parsed;
    try {
        parsed = JSON.parse(raw);
    } catch (e) {
        alert("JSON 解析失败！");
        return;
    }

    if (!parsed.maps || !Array.isArray(parsed.maps) || !parsed.maps.length) {
        alert("JSON 中未找到有效 maps 数据！");
        return;
    }
    const firstMap = parsed.maps[0];

    // 1) 恢复初始阵容
    matchData.map_name = firstMap.map_name || "";
    matchData.weaker = firstMap.weaker || "team_1";
    matchData.starting_status = firstMap.starting_status || "team_1_advantage";
    matchData.team_1 = firstMap.team_1 || [];
    matchData.team_2 = firstMap.team_2 || [];
    matchData.events = firstMap.events || [];
    matchData.map_result = firstMap.map_result || "team_1_win";

    // 2) 重置当前阵容 = 初始阵容
    currentTeam1 = [...matchData.team_1];
    currentTeam2 = [...matchData.team_2];

    // 3) 依次应用事件
    applyAllEventsToCurrentTeams();

    // 清空 pending
    pendingEvent = { team_1_changes: {}, team_2_changes: {}, new_status: "" };
    document.getElementById("event_new_status").value = "";

    area.value = "";
    refreshUI();
    alert("JSON 导入成功！已更新地图/队伍/事件");
}

/** 把 matchData.events 全部应用到 currentTeam1/currentTeam2 */
function applyAllEventsToCurrentTeams() {
    for (let ev of matchData.events) {
        applyChangesToCurrentTeam("team_1", ev.team_1_changes);
        applyChangesToCurrentTeam("team_2", ev.team_2_changes);
    }
}
