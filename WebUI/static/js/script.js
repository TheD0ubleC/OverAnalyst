/******************************************************************************
 * 1. 填充英雄列表
 *    - 去掉对 selectedHeroes 的引用
 *    - 英雄图片统一带 object-contain
 ******************************************************************************/
function populateList(listId, heroes) {
    const list = document.getElementById(listId);
    if (!list) return;
    heroes.forEach(hero => {
      const heroDiv = document.createElement("div");
      heroDiv.classList.add("draggable", "p-2", "rounded", "mb-2");
      heroDiv.setAttribute("draggable", "true");
      // 统一使用 object-contain，防止拉伸
      heroDiv.innerHTML = `
        <img src="static/Images/${hero}.png" 
             alt="${hero}" 
             class="rounded-full w-12 h-12 object-contain"/>
      `;
      heroDiv.dataset.hero = hero;
      // 根据列表 ID 判断角色类型
      heroDiv.dataset.role = listId.includes("Tank") ? "tank" 
                          : listId.includes("Dps")  ? "dps" 
                          : "support";
      list.appendChild(heroDiv);
  
      // 拖拽开始：隐藏原元素
      heroDiv.addEventListener("dragstart", event => {
        event.dataTransfer.setData("text/plain", hero);
        event.dataTransfer.setData("text/html", heroDiv.outerHTML);
        setTimeout(() => heroDiv.style.display = "none", 0);
      });
  
      // 拖拽结束：如果没有被添加到槽位，就重新显示
      heroDiv.addEventListener("dragend", () => {
        heroDiv.style.display = "block";
      });
  
      // 点击添加：根据父容器判断是 team1 / mTeam1 / team2 / mTeam2
      heroDiv.addEventListener("click", () => {
        let teamPrefix = "";
        if (listId.startsWith("mTeam1"))      teamPrefix = "mTeam1";
        else if (listId.startsWith("team1")) teamPrefix = "team1";
        else if (listId.startsWith("mTeam2"))teamPrefix = "mTeam2";
        else if (listId.startsWith("team2")) teamPrefix = "team2";
  
        handleHeroClick(heroDiv, teamPrefix, heroDiv.dataset.role);
      });
    });
  }
  
  /******************************************************************************
   * 2. 点击添加英雄到槽位
   *    - 不再检查 selectedHeroes
   *    - 保持 object-contain 样式
   ******************************************************************************/
  function handleHeroClick(heroDiv, teamPrefix, role) {
    let targetSlot = null;
    if (role === "tank") {
      targetSlot = document.getElementById(teamPrefix + "Tank");
    } else if (role === "dps") {
      const slot1 = document.getElementById(teamPrefix + "Dps1");
      const slot2 = document.getElementById(teamPrefix + "Dps2");
      if (slot1 && !slot1.hasChildNodes()) targetSlot = slot1;
      else if (slot2 && !slot2.hasChildNodes()) targetSlot = slot2;
    } else if (role === "support") {
      const slot1 = document.getElementById(teamPrefix + "Support1");
      const slot2 = document.getElementById(teamPrefix + "Support2");
      if (slot1 && !slot1.hasChildNodes()) targetSlot = slot1;
      else if (slot2 && !slot2.hasChildNodes()) targetSlot = slot2;
    }
  
    // 如果找到空槽位，就克隆 heroDiv 并添加进去
    if (targetSlot && !targetSlot.hasChildNodes()) {
      const clone = heroDiv.cloneNode(true);  // 保留 object-contain
      targetSlot.innerHTML = "";
      targetSlot.appendChild(clone);
  
      // 移除原列表中的该元素
      heroDiv.remove();
  
      // 给克隆的头像绑定拖拽和点击事件
      clone.addEventListener("dragstart", event => {
        event.dataTransfer.setData("text/plain", clone.dataset.hero);
        event.dataTransfer.setData("text/html", clone.outerHTML);
      });
      clone.addEventListener("dragend", () => {
        // 如果槽位内不再包含该克隆元素，说明被拖出
        if (!targetSlot.contains(clone)) {
          // 无需做特殊处理，只要不阻止即可
        }
      });
      clone.addEventListener("click", () => {
        removeHeroFromSlot(clone, targetSlot);
      });
    }
  }
  
  /******************************************************************************
   * 3. 槽位移除英雄：返回原列表
   *    - 去掉对 selectedHeroes 的引用
   *    - 保持 object-contain 样式
   ******************************************************************************/
  function removeHeroFromSlot(hero, slot) {
    const heroName = hero.dataset.hero;
    const role = hero.dataset.role;
  
    // 根据槽位 ID 判断原列表（移动端 or 桌面端）
    let teamPrefix = "";
    if (slot.id.startsWith("mTeam1"))      teamPrefix = "mTeam1";
    else if (slot.id.startsWith("mTeam2")) teamPrefix = "mTeam2";
    else if (slot.id.startsWith("team1"))  teamPrefix = "team1";
    else                                   teamPrefix = "team2";
  
    const originalListId = 
      role === "tank"    ? teamPrefix + "TankList" :
      role === "dps"     ? teamPrefix + "DpsList"  :
                           teamPrefix + "SupportList";
    const originalList = document.getElementById(originalListId);
  
    if (originalList) {
      // 如果原列表里已存在同名英雄，则只需要把它显示出来
      let existing = originalList.querySelector(`[data-hero="${heroName}"]`);
      if (existing) {
        existing.style.display = "block";
      } else {
        // 否则创建一个新的英雄元素
        const newHeroDiv = document.createElement("div");
        newHeroDiv.classList.add("draggable", "p-2", "rounded", "mb-2");
        newHeroDiv.setAttribute("draggable", "true");
        // 注意这里也要加 object-contain
        newHeroDiv.innerHTML = `
          <img src="static/Images/${heroName}.png" 
               alt="${heroName}" 
               class="rounded-full w-12 h-12 object-contain"/>
        `;
        newHeroDiv.dataset.hero = heroName;
        newHeroDiv.dataset.role = role;
        originalList.appendChild(newHeroDiv);
  
        // 绑定事件
        newHeroDiv.addEventListener("dragstart", event => {
          event.dataTransfer.setData("text/plain", heroName);
          event.dataTransfer.setData("text/html", newHeroDiv.outerHTML);
          setTimeout(() => newHeroDiv.style.display = "none", 0);
        });
        newHeroDiv.addEventListener("dragend", () => {
          newHeroDiv.style.display = "block";
        });
        newHeroDiv.addEventListener("click", () => {
          handleHeroClick(newHeroDiv, teamPrefix, role);
        });
      }
    }
    // 清空槽位
    slot.innerHTML = "";
  }
  
  /******************************************************************************
   * 4. 槽位拖拽放置事件
   *    - 不再检查 selectedHeroes
   *    - 保持 object-contain 样式
   ******************************************************************************/
  document.querySelectorAll(".slot").forEach(slot => {
    slot.addEventListener("dragover", event => {
      event.preventDefault();
    });
  
    slot.addEventListener("drop", event => {
      event.preventDefault();
      let heroName = event.dataTransfer.getData("text/plain");
      let heroHTML = event.dataTransfer.getData("text/html");
      if (!heroName) return;  // 如果没有英雄信息，直接返回
  
      // 将 HTML 字符串转成 DOM
      let tempDiv = document.createElement("div");
      tempDiv.innerHTML = heroHTML;
      let newHero = tempDiv.firstChild;
  
      // 如果槽位匹配角色，且槽位为空
      if (newHero.dataset.role === slot.dataset.role && !slot.hasChildNodes()) {
        slot.innerHTML = "";
        slot.appendChild(newHero);
  
        // 绑定事件
        newHero.addEventListener("dragstart", event => {
          event.dataTransfer.setData("text/plain", newHero.dataset.hero);
          event.dataTransfer.setData("text/html", newHero.outerHTML);
        });
        newHero.addEventListener("dragend", () => {
          if (!slot.contains(newHero)) {
            // 说明被拖出了槽位
          }
        });
        newHero.addEventListener("click", () => {
          removeHeroFromSlot(newHero, slot);
        });
      }
    });
  });
  
  /******************************************************************************
   * 5. 检查是否所有槽位都填满
   ******************************************************************************/
  function areAllSlotsFilled() {
    const selectedPC = getAllSelectedHeroes("pc");
    const selectedMobile = getAllSelectedHeroes("mobile");

    // 只要 PC 端或者移动端有一个完整的 5v5，就算填满
    if (
        (selectedPC.team1.length === 5 && selectedPC.team2.length === 5) || 
        (selectedMobile.team1.length === 5 && selectedMobile.team2.length === 5)
    ) {
        return true;
    } else {
        return false;
    }
}


function getAllSelectedHeroes(version = "pc") {
    const slots = document.querySelectorAll(".slot");
    const team1 = [];
    const team2 = [];

    slots.forEach(slot => {
        const heroImage = slot.querySelector("img"); // 选取英雄头像
        if (heroImage) {
            const heroName = heroImage.alt;

            if (version === "pc") {
                // PC 端槽位
                if (slot.id.startsWith("team1")) team1.push(heroName);
                if (slot.id.startsWith("team2")) team2.push(heroName);
            } else if (version === "mobile") {
                // 移动端槽位
                if (slot.id.startsWith("mTeam1")) team1.push(heroName);
                if (slot.id.startsWith("mTeam2")) team2.push(heroName);
            }
        }
    });

    return { team1, team2 };
}


  /******************************************************************************
   * 6. 弹窗 & 选项示例
   ******************************************************************************/
  function openModal() {
    document.getElementById("modal").classList.remove("hidden");
  }
  
  function closeModal() {
    document.getElementById("modal").classList.add("hidden");
  }
  
  function option1() {
    // 点击“胜率计算”前，先检查所有槽位是否填满
    if (!areAllSlotsFilled()) {
      alert("还有槽位为空，请先选满英雄！");
      return;
    }
    // 如果槽位已满，则进行后续操作
    get_predict();
  }
  function option2() {
    // 点击“胜率计算”前，先检查所有槽位是否填满
    if (!areAllSlotsFilled()) {
      alert("还有槽位为空，请先选满英雄！");
      return;
    }
    // 如果槽位已满，则进行后续操作
    auto_team_swap("team_1");
  }
  function option3() {
    // 点击“胜率计算”前，先检查所有槽位是否填满
    if (!areAllSlotsFilled()) {
      alert("还有槽位为空，请先选满英雄！");
      return;
    }
    // 如果槽位已满，则进行后续操作
    auto_team_swap("team_2");
  }
  
  /******************************************************************************
   * 7. 调用后端接口示例
   ******************************************************************************/
  function get_predict() {
    // 获取 PC 端和移动端的英雄数据
    const selectedPC = getAllSelectedHeroes("pc");
    const selectedMobile = getAllSelectedHeroes("mobile");

    // 选择填满的槽位数据
    let team1 = [], team2 = [];
    if (selectedPC.team1.length === 5 && selectedPC.team2.length === 5) {
        team1 = selectedPC.team1;
        team2 = selectedPC.team2;
    } else if (selectedMobile.team1.length === 5 && selectedMobile.team2.length === 5) {
        team1 = selectedMobile.team1;
        team2 = selectedMobile.team2;
    } else {
        alert("❌ 请选择完整的队伍（PC 或移动端）！");
        return;
    }

    const map = "暴雪世界"; // 或者 document.getElementById("map").value;

    // **用 `form.submit()` 直接提交到 Flask**
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/over_analyst/predict";

    // 追加隐藏输入字段
    team1.forEach(hero => {
        let input = document.createElement("input");
        input.type = "hidden";
        input.name = "team_1[]";
        input.value = hero;
        form.appendChild(input);
    });

    team2.forEach(hero => {
        let input = document.createElement("input");
        input.type = "hidden";
        input.name = "team_2[]";
        input.value = hero;
        form.appendChild(input);
    });

    let mapInput = document.createElement("input");
    mapInput.type = "hidden";
    mapInput.name = "map";
    mapInput.value = map;
    form.appendChild(mapInput);

    document.body.appendChild(form);
    form.submit(); // 直接提交表单，跳转到 Flask 渲染的 `predict.html`
}

  
/*

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
*/

function auto_team_swap(team) {
    // 获取 PC 端和移动端的英雄数据
    const selectedPC = getAllSelectedHeroes("pc");
    const selectedMobile = getAllSelectedHeroes("mobile");

    // 选择填满的槽位数据
    let team1 = [], team2 = [];
    if (selectedPC.team1.length === 5 && selectedPC.team2.length === 5) {
        team1 = selectedPC.team1;
        team2 = selectedPC.team2;
    } else if (selectedMobile.team1.length === 5 && selectedMobile.team2.length === 5) {
        team1 = selectedMobile.team1;
        team2 = selectedMobile.team2;
    } else {
        alert("❌ 请选择完整的队伍（PC 或移动端）！");
        return;
    }

    // 确保数据正确
    console.log("队伍 1:", team1);
    console.log("队伍 2:", team2);

    // 获取地图名字（可以动态修改）
    const map = "暴雪世界"; // 或者 document.getElementById("map").value;

    // **修正：使用 `URLSearchParams` 以符合 Flask `request.form.getlist()`**
    const formData = new URLSearchParams();
    team1.forEach(hero => formData.append("team_1[]", hero));
    team2.forEach(hero => formData.append("team_2[]", hero));
    formData.append("map", map);
    formData.append("team", team);

    // 发送 `POST` 请求给后端
    fetch("/over_analyst/auto_team_swap", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: formData.toString() // URL 编码数据
    })
    .then(response => response.text()) // **Flask 直接返回字符串**
    .then(result => {
        alert(result); // 直接弹窗显示后端返回的信息
    })
    .catch(err => {
        alert("请求出错: " + err);
    });
}


// 定义各角色的英雄数组
const tankHeroes = ["莱因哈特", "温斯顿", "路霸", "查莉娅", "D.Va", "末日铁拳", "奥丽莎", "破坏球", "渣客女王", "西格玛", "拉玛刹", "毛加", "骇灾"];
const dpsHeroes = ["死神", "猎空", "半藏", "托比昂", "法老之鹰", "黑百合", "堡垒", "秩序之光", "源氏", "卡西迪", "狂鼠", "士兵：76", "美", "黑影", "索杰恩", "艾什", "回声", "探奇"];
const supportHeroes = ["天使", "禅雅塔", "卢西奥", "安娜", "布丽吉塔", "莫伊拉", "巴蒂斯特", "雾子", "生命之梭", "伊拉锐", "朱诺"];

// 填充桌面版英雄列表
populateList("team1TankList", tankHeroes);
populateList("team1DpsList", dpsHeroes);
populateList("team1SupportList", supportHeroes);
populateList("team2TankList", tankHeroes);
populateList("team2DpsList", dpsHeroes);
populateList("team2SupportList", supportHeroes);
// 填充移动版英雄列表
populateList("mTeam1TankList", tankHeroes);
populateList("mTeam1DpsList", dpsHeroes);
populateList("mTeam1SupportList", supportHeroes);
populateList("mTeam2TankList", tankHeroes);
populateList("mTeam2DpsList", dpsHeroes);
populateList("mTeam2SupportList", supportHeroes);