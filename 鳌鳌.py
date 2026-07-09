# 🧿 感觉层：计算所有核的共振状态
"""
共鸣空间 · 生理模拟版 v3.4 · 优化版
优化说明：
1. 【宪法】加入“自我认识”和“概念生长”参数。
2. 【元旋钮】加入动量与偏移，使扰动有方向性。
3. 【悄悄话】升级：合作共振、跨组交流、连接衰减。
4. 【自我反思】定期评估内部状态稳定性。
5. 【概念影响】强概念核可反向调节神经元唤醒阈值。
6. 【所有权】所有控制参数仍在顶部宪法中。
"""

import math, random, json, os, ast, time
from collections import defaultdict, deque

# ============================================================
# 📜 【宪法级设置】—— 你说了算
# ============================================================

宪法 = {
    # --- 内存与生存 ---
    "最大关系记忆条数": 3000,
    "最大策略原型数": 100,
    "最大经验条数": 2000,

    # --- 记忆生理（模糊化） ---
    "模糊化门槛": 300,
    "模糊化衰减": 0.92,
    "模糊化移除阈值": 20,
    "记忆固化阈值": 0.8,

    # --- 反射弧（潜意识） ---
    "反射灵敏度": 0.6,
    "反射通道数": 14,

    # --- 能耗控制 ---
    "内演强度": 0.03,
    "内演唤醒门槛": 0.4,
    "休眠阈值": 0.1,

    # --- 行为修正 ---
    "悄悄话抑制系数": 0.95,
    "自我锚点保护": 0.01,

    # --- 自我认识（新增） ---
    "自我锚点学习率": 0.005,
    "自我反思间隔": 50,

    # --- 概念生长（新增） ---
    "概念生长启用": True,
    "概念生长门槛": 3,
    "概念核最大数量": 100,
}


# ============================================================
# 元旋钮（升级版：动量+偏移）
# ============================================================
class 元旋钮:
    def __init__(self, 名称, 初始值=0.0, 范围=(-2.0, 2.0)):
        self.名称 = 名称
        self.值 = 初始值
        self.范围 = 范围
        self.调整次数 = 0
        self.上一次扰动方向 = 0.0
        self.动量 = 0.0
        self.策略倾向 = random.uniform(0.1, 0.9)  # 连续策略倾向 0=保守 1=探索
        self.事件叠加值 = 0.0                      # 生理事件触发的临时跳跃
        self.基值 = self.策略倾向                   # 长期漂移的基础值

    @property
    def 有效策略(self):
        """基值 + 事件叠加值，随时间衰减叠加值"""
        self.事件叠加值 *= 0.9  # 每调用一次衰减10%
        if abs(self.事件叠加值) < 0.001:
            self.事件叠加值 = 0.0
        return max(0.0, min(1.0, self.基值 + self.事件叠加值))

    def 触发事件(self, 强度=0.2):
        """生理事件触发：瞬间叠加一个值"""
        self.事件叠加值 += 强度
        self.事件叠加值 = max(0.0, min(0.5, self.事件叠加值))

    def 调节基值(self, 误差趋势):
        """根据误差趋势缓慢调整基值"""
        self.基值 += 误差趋势 * 0.02
        self.基值 = max(0.0, min(1.0, self.基值))

    def 扰动(self, 幅度=0.1):
        # 有效策略决定扰动幅度
        实际幅度 = 幅度 * (0.3 + self.有效策略 * 1.4)  # 0.3~1.7倍
        方向 = self.上一次扰动方向 * 0.6 + random.uniform(-1, 1) * 0.4
        self.值 += 方向 * 实际幅度
        self.值 = max(self.范围[0], min(self.范围[1], self.值))
        self.上一次扰动方向 = 方向
        self.调整次数 += 1
        return self.值

    def 适应性微调(self, 误差, 学习率=0.01):
        实际学习率 = 学习率 * (0.5 + self.有效策略)  # 策略越高学习越快
        self.动量 = self.动量 * 0.9 + 误差 * 实际学习率 * 0.1
        self.值 += self.动量
        self.值 = max(self.范围[0], min(self.范围[1], self.值))
        self.调整次数 += 1
        return self.值

    def 切换(self):
        self.值 = random.uniform(self.范围[0], self.范围[1])
        self.调整次数 += 1

    def 快照(self):
        return {"值": self.值, "调整次数": self.调整次数}

    def 恢复(self, 快照):
        self.值 = 快照["值"]
        self.调整次数 = 快照["调整次数"]


# ============================================================
# 策略原型库
# ============================================================
策略原型库 = []
_原型合并计数器 = 0
_原型合并间隔 = 50


def _签名距离(a, b):
    return sum((x - y) * (x - y) for x, y in zip(a, b)) ** 0.5


def _查找原型(签名):
    if not 策略原型库:
        return None, None
    候选库 = 策略原型库[-宪法["最大策略原型数"]:]
    最近 = min(候选库, key=lambda p: _签名距离(签名, p[0]))
    if _签名距离(签名, 最近[0]) < 最近[1]:
        return 最近[0], 最近[2]
    return None, None


def _更新原型库(签名, 误差):
    global _原型合并计数器
    if len(策略原型库) >= 宪法["最大策略原型数"]:
        策略原型库.pop(0)
    if not 策略原型库:
        策略原型库.append([签名, 0.3, 误差, 1])
        return
    最近 = min(策略原型库, key=lambda p: _签名距离(签名, p[0]))
    if _签名距离(签名, 最近[0]) < 最近[1] * 1.5:
        最近[3] += 1
        最近[2] = 最近[2] * 0.7 + 误差 * 0.3
    elif random.random() < 0.05:
        策略原型库.append([签名, 0.3, 误差, 1])
    _原型合并计数器 += 1
    if _原型合并计数器 >= _原型合并间隔:
        _合并原型()
        _原型合并计数器 = 0


def _合并原型():
    if len(策略原型库) < 2:
        return
    i = len(策略原型库) - 1
    for j in range(len(策略原型库) - 2, -1, -1):
        if _签名距离(策略原型库[i][0], 策略原型库[j][0]) < 0.5:
            keep, drop = (i, j) if 策略原型库[i][3] >= 策略原型库[j][3] else (j, i)
            策略原型库[keep][1] = max(策略原型库[keep][1], 策略原型库[drop][1])
            策略原型库[keep][2] = (策略原型库[keep][2] * 策略原型库[keep][3] + 策略原型库[drop][2] * 策略原型库[drop][3]) / (策略原型库[keep][3] + 策略原型库[drop][3])
            策略原型库[keep][3] += 策略原型库[drop][3]
            策略原型库.pop(drop)
            return


# ============================================================
# 神经元v12（升级版悄悄话）
# ============================================================
class 神经元v12:
    def __init__(self, 编号, 输入维, 关注=None):
        self.编号 = 编号
        self.关注 = 关注 or list(range(输入维))
        self.权重 = [元旋钮(f"w{j}", 初始值=random.uniform(-0.5, 0.5)) for j in range(len(self.关注))]
        self.偏置 = 元旋钮("b", 初始值=random.uniform(-0.3, 0.3))
        self.激活策略 = 元旋钮("激活策略", 初始值=random.uniform(-1, 1))
        self.偏置策略 = 元旋钮("偏置策略", 初始值=random.uniform(-1, 1))
        self.误差策略 = 元旋钮("误差策略", 初始值=random.uniform(-1, 1))
        self.不确定策略 = 元旋钮("不确定策略", 初始值=random.uniform(-1, 1))
        self.唤醒阈值 = 元旋钮("唤醒阈值", 初始值=random.uniform(0.1, 0.6), 范围=(0.0, 1.0))
        self.学习速率 = 元旋钮("学习速率", 初始值=random.uniform(0.01, 0.08))
        self.独立误差历史 = deque(maxlen=30)
        self.评估步数计数器 = 0
        self.评估间隔 = 10
        self.策略切换冷却 = 0
        self.上次独立评估 = 0.0
        self.策略生存计数 = 0
        self.震荡标志 = False
        self.当前任务ID = "默认"
        self.上次输入 = None
        self.上次输出 = 0.0
        self.输出历史 = deque(maxlen=5)
        self.不确定性 = 1.0
        self.激活计数 = 0
        self.连续跳过 = 0
        self.合作记忆 = {}
        self.功能组亲和力 = {}
        self.上次误差 = 0.0
        self.内在节律 = random.uniform(0.3, 1.8)
        self.内演累积 = 0.0

    def _激活(self, x):
        if self.激活策略.值 < -0.5: return x
        elif self.激活策略.值 > 0.5: return math.tanh(x)
        else: return 1.0 if x > 0 else (-1.0 if x < 0 else 0.0)

    def _用偏置(self): return self.偏置策略.值 >= 0

    def _误差函数(self, 目标, 输出):
        if self.误差策略.值 >= 0: return 目标 - 输出
        return 1.0 if (目标 - 输出) > 0 else (-1.0 if (目标 - 输出) < 0 else 0.0)

    def _感知不确定性(self, 输入):
        if len(self.输出历史) < 3: return 1.0
        if self.不确定策略.值 < 0:
            w = max(self.输出历史) - min(self.输出历史)
            return 0.1 if w < 0.05 else 0.3 if w < 0.2 else 0.6 if w < 0.5 else 0.9
        else:
            if self.上次输入: return max(abs(a - b) for a, b in zip(输入, self.上次输入))
            return 1.0

    def 获取策略签名(self):
        return (round(self.激活策略.值, 1), round(self.偏置策略.值, 1),
                round(self.误差策略.值, 1), round(self.不确定策略.值, 1))

    def 获取振动签名(self):
        s = sum(w.值 * v for w, v in zip(self.权重, self.上次输入)) if self.上次输入 else 0
        return (1 if s > 0 else -1, round(min(1.0, abs(s)), 2),
                round(sum(1 for w in self.权重 if abs(w.值) > 0.1) / max(len(self.权重), 1), 2))

    def 前向(self, x):
        self.上次输入 = [x[i] for i in self.关注 if i < len(x)]
        总和 = 0.0
        for j, w in enumerate(self.权重):
            if j < len(self.上次输入): 总和 += w.值 * self.上次输入[j]
        if self._用偏置():
            总和 += self.偏置.值
            self.内演累积 = (getattr(self, "内演累积", 0) + 0.1) % (2 * math.pi)
            总和 += (0.5 - self.唤醒阈值.值) * 0.01
            总和 += math.sin(self.内演累积 * self.内在节律) * 0.02
        self.上次输出 = self._激活(总和)
        if abs(self.上次输出) < 0.05: self.上次输出 = 0.0
        self.输出历史.append(self.上次输出)
        self.不确定性 = self._感知不确定性(x)
        self.激活计数 += 1
        return self.上次输出

    def 说悄悄话(self, 邻居们, 全局平均误差=0.0):
        """
        神经元之间的侧向通信 —— 升级版
        新增：合作、竞争、跨组交流、新连接形成
        """
        同组 = [n for n in 邻居们 if n.关注 == self.关注 and n.编号 != self.编号]
        
        for 邻居 in 同组:
            # ---- 原有逻辑：表现好则自信，表现差则谦虚 ----
            if self.上次误差 < 邻居.上次误差 * 0.7:
                self.学习速率.扰动(0.01)
                self.功能组亲和力[邻居.编号] = self.功能组亲和力.get(邻居.编号, 0) + 0.3
                if 邻居.连续跳过 > 5:
                    邻居.唤醒阈值.扰动(-0.003)
                    
            elif self.上次误差 > 邻居.上次误差 * 1.3:
                self.学习速率.值 *= 宪法["悄悄话抑制系数"]
                self.功能组亲和力[邻居.编号] = self.功能组亲和力.get(邻居.编号, 0) + 0.1
                if random.random() < 0.3:
                    self.激活策略.值 += (邻居.激活策略.值 - self.激活策略.值) * 0.05
                    
            else:
                if random.random() < 0.2:
                    self.唤醒阈值.扰动(-0.002)
                    邻居.唤醒阈值.扰动(-0.002)
                    self.功能组亲和力[邻居.编号] = self.功能组亲和力.get(邻居.编号, 0) + 0.15
        
        # 跨组交流：偶尔与关注不同维度的神经元交换信息
        if random.random() < 0.05:
            异组 = [n for n in 邻居们 if n.关注 != self.关注 and n.编号 != self.编号]
            if 异组:
                随机邻居 = random.choice(异组)
                if self.不确定性 > 随机邻居.不确定性:
                    随机邻居.唤醒阈值.扰动(-0.001)
                else:
                    self.唤醒阈值.扰动(-0.001)
                self.功能组亲和力[随机邻居.编号] = self.功能组亲和力.get(随机邻居.编号, 0) + 0.05
        
        # 连接衰减：长期未交流的逐渐淡化
        for nid in list(self.功能组亲和力.keys()):
            if nid not in [n.编号 for n in 同组]:
                self.功能组亲和力[nid] *= 0.99
                if self.功能组亲和力[nid] < 0.01:
                    del self.功能组亲和力[nid]

    def 决定是否唤醒(self, x):
        if self.上次输入 is None or self.激活计数 < 3: return True
        if self.不确定性 < 宪法["休眠阈值"]: return False
        if self.连续跳过 > 15: return True
        return self.不确定性 >= self.唤醒阈值.值

    def 前向_事件驱动(self, x):
        if not self.决定是否唤醒(x):
            self.连续跳过 += 1
            return self.上次输出
        self.连续跳过 = 0
        return self.前向(x)

    def 微调(self, 目标, 输入向量=None):
        if 输入向量 is not None: self.前向(输入向量)
        if self.上次输入 is None: return
        原始误差 = self._误差函数(目标, self.上次输出)
        幅度 = self.学习速率.值
        for j, w in enumerate(self.权重):
            if j < len(self.上次输入) and abs(self.上次输入[j]) > 0.01:
                w.扰动(abs(原始误差) * 幅度 * 0.3 * (1 if self.上次输入[j] > 0 else -1))
        if self._用偏置(): self.偏置.扰动(原始误差 * 幅度 * 0.2)
        if abs(原始误差) > 0.3: self.唤醒阈值.扰动(-0.015)
        elif abs(原始误差) < 0.1 and self.连续跳过 > 10: self.唤醒阈值.扰动(0.01)
        self.评估步数计数器 += 1
        if self.评估步数计数器 >= self.评估间隔:
            self.评估步数计数器 = 0
            self._执行评估(目标)

    def _执行评估(self, 目标):
        连续误差 = abs(目标 - self.上次输出)
        self.独立误差历史.append(连续误差)
        self.上次误差 = abs(连续误差)
        if len(self.独立误差历史) < 10: return
        近期 = sum(self.独立误差历史) / len(self.独立误差历史)
        签名 = self.获取策略签名()
        _更新原型库(签名, 近期)
        趋势 = self.上次独立评估 - 近期
        if abs(趋势) < 0.01 and self.策略切换冷却 <= 0: self.震荡标志 = not self.震荡标志
        else: self.震荡标志 = False
        if self.震荡标志 and self.策略切换冷却 <= 0:
            位点 = random.choice(["激活策略", "偏置策略", "误差策略", "不确定策略"])
            getattr(self, 位点).切换(); getattr(self, 位点).扰动(0.3)
            self.策略切换冷却 = 20; self.震荡标志 = False
        elif 趋势 < -0.02 and self.策略切换冷却 <= 0:
            位点 = random.choice(["激活策略", "偏置策略", "误差策略", "不确定策略"])
            getattr(self, 位点).切换(); self.策略切换冷却 = 15; self.策略生存计数 = 0
        elif 趋势 > 0.02:
            self.策略生存计数 += 1
            if self.策略生存计数 > 30: self.学习速率.扰动(-0.002)
            else:
                self.策略切换冷却 = max(0, self.策略切换冷却 - 1)
                if random.random() < 0.01: self.学习速率.扰动(0.003)
        self.上次独立评估 = 近期

    def 设置任务(self, 任务ID):
        if 任务ID != self.当前任务ID:
            签名 = self.获取策略签名()
            原型, 原型误差 = _查找原型(签名)
            if 原型 and 原型误差 and 原型误差 < 0.4:
                self.激活策略.值 += (原型[0] - self.激活策略.值) * 0.3
                self.偏置策略.值 += (原型[1] - self.偏置策略.值) * 0.3
                self.误差策略.值 += (原型[2] - self.误差策略.值) * 0.3
                self.不确定策略.值 += (原型[3] - self.不确定策略.值) * 0.3
            self.当前任务ID = 任务ID
            self.独立误差历史.clear()
            self.策略生存计数 = 0

    def 广播(self):
        return None if self.不确定性 < 0.3 else {"id": self.编号, "sig": self.获取振动签名(), "unc": self.不确定性}

    def 记住合作(self, 伙伴列表):
        for p in 伙伴列表:
            if p != self.编号: self.合作记忆[p] = self.合作记忆.get(p, 0) + 1

    def 快照(self):
        d = {"权重": [w.快照() for w in self.权重]}
        for attr in ["偏置", "激活策略", "偏置策略", "误差策略", "不确定策略", "唤醒阈值", "学习速率"]:
            d[attr] = getattr(self, attr).快照()
        for attr in ["上次输出", "不确定性", "激活计数", "连续跳过", "策略生存计数",
                     "策略切换冷却", "当前任务ID", "震荡标志", "上次独立评估", "评估步数计数器"]:
            d[attr] = getattr(self, attr)
        d["输出历史"] = list(self.输出历史)
        d["独立误差历史"] = list(self.独立误差历史)
        d["合作记忆"] = dict(self.合作记忆)
        return d

    def 恢复(self, 快照):
        for w, s in zip(self.权重, 快照["权重"]): w.恢复(s)
        for attr in ["偏置", "激活策略", "偏置策略", "误差策略", "不确定策略", "唤醒阈值", "学习速率"]:
            if attr in 快照: getattr(self, attr).恢复(快照[attr])
        self.上次输出 = 快照.get("上次输出", 0.0)
        self.输出历史 = deque(快照.get("输出历史", []), maxlen=5)
        self.不确定性 = 快照.get("不确定性", 1.0)
        self.激活计数 = 快照.get("激活计数", 0)
        self.连续跳过 = 快照.get("连续跳过", 0)
        self.独立误差历史 = deque(快照.get("独立误差历史", []), maxlen=30)
        self.策略生存计数 = 快照.get("策略生存计数", 0)
        self.策略切换冷却 = 快照.get("策略切换冷却", 0)
        self.当前任务ID = 快照.get("当前任务ID", "默认")
        self.上次独立评估 = 快照.get("上次独立评估", 0.0)
        self.震荡标志 = 快照.get("震荡标志", False)
        self.评估步数计数器 = 快照.get("评估步数计数器", 0)
        self.合作记忆 = dict(快照.get("合作记忆", {}))


# ============================================================
# 低级神经元（反射弧专用）- 升级版 v2
# ============================================================
class 低级神经元:
    def __init__(self, 编号, 输入维):
        self.编号 = 编号
        self.权重 = [random.uniform(-0.8, 0.8) for _ in range(输入维)]
        self.偏置 = random.uniform(-0.2, 0.2)
        self.激活阈值 = 0.3
        self.演化步数 = 0
        self.内在节律 = random.uniform(0.8, 1.5)

    def 反射(self, 输入):
        总和 = sum(w * v for w, v in zip(self.权重, 输入)) + self.偏置
        return 1.0 if 总和 > self.激活阈值 else 0.0

    def 缓慢演化(self):
        self.演化步数 += 1
        for i in range(len(self.权重)):
            self.权重[i] += random.uniform(-0.001, 0.001) * self.内在节律
            self.权重[i] = max(-1.0, min(1.0, self.权重[i]))
        self.偏置 += random.uniform(-0.0005, 0.0005) * self.内在节律
        self.偏置 = max(-0.5, min(0.5, self.偏置))
        self.激活阈值 += random.uniform(-0.0003, 0.0003) * self.内在节律
        self.激活阈值 = max(0.1, min(0.6, self.激活阈值))


# ============================================================
# 原版工具类
# ============================================================
class 旋钮:
    def __init__(self, 名称, 初始值=0.0, 阻尼=0.5, 范围=(-1.0, 1.0)):
        self.名称 = 名称; self.值 = 初始值; self.阻尼 = 阻尼; self.范围 = 范围; self.调整次数 = 0
    def 微调(self, 方向, 步长=0.05):
        self.值 = max(self.范围[0], min(self.范围[1], self.值 + 方向 * 步长 * (1 - self.阻尼)))
        self.调整次数 += 1; return self.值
    def 降低阻尼(self, 减量=0.05): self.阻尼 = max(0.0, self.阻尼 - 减量)


class 处理痕迹:
    def __init__(self, 签名, 输出, 评分):
        self.输入签名 = 签名; self.输出值 = 输出
        self.效果评分 = min(1.0, max(0.0, 评分)); self.使用次数 = 1; self.强化次数 = 0
    def 强化(self): self.强化次数 += 1; self.使用次数 += 1; self.效果评分 = min(1.0, self.效果评分 + 0.05)


class 长期记忆:
    def __init__(self, 容量=2000): self.库 = {}; self.容量 = 容量
    def 存入(self, 签名, 输出, 置信度):
        if 签名 in self.库:

            self.库[签名]['输出'] = self.库[签名]['输出'] * 0.7 + 输出 * 0.3

            self.库[签名]['置信度'] = min(1.0, self.库[签名]['置信度'] + 0.1)

            self.库[签名]['时间'] = time.time()

        else:

            if len(self.库) >= self.容量: self.库.pop(min(self.库, key=lambda x: self.库[x]['时间']))

            self.库[签名] = {'输出': 输出, '置信度': 置信度, '时间': time.time()}
    def 查询(self, 签名): return self.库.get(签名)
    def 统计(self): return len(self.库)


class 探测器:
    def __init__(self):
        self.计数 = 0
        self.历史 = deque(maxlen=30)
        self.节奏 = "建立中"
        self.上一次节奏变化 = 0

    def 监听(self, 强度):
        """监听脉冲强度，更新节奏"""
        self.历史.append(强度)
        if len(self.历史) < 5:
            self.节奏 = "建立中"
        else:
            近期 = list(self.历史)[-10:]
            波动 = max(近期) - min(近期)
            if 波动 > 0.3:
                self.节奏 = "急促"
            elif 波动 < 0.1:
                self.节奏 = "稀疏"
            else:
                self.节奏 = "稳定"
    def 节奏信号(self):
        """返回当前节奏，用于调节系统精力"""
        return self.节奏

    def 是否警报(self):
        """节奏从稳定突然变急促 = 生理警报"""
        return self.节奏 == "急促" and len(self.历史) >= 5

def 冲突检测(旧值, 新值): return abs(旧值 - 新值) > 0.5


# ============================================================
# 概念核 —— 从经验中自然凝结出的稳定模式
# ============================================================
class 概念核:
    def __init__(self):
        self.核向量 = None       # 均值μ
        self.方差 = 1.0          # 方差σ（越大越不确定）
        self._σ自适应速率 = 0.1  # σ自适应学习率
        self._误差历史 = []      # 最近误差，用于σ反馈
        self.概率权重 = 1.0      # 多核竞争权重
        self.相关经验 = []
        self.标签 = None
        self.强度 = 0.0
        self.关联概念 = {}       # 其他概念核id → 关联强度
        self.策略倾向历史 = 0.5  # 记录吸收经验时的平均策略倾向
        self.神经元指纹 = {}     # 神经元编号 → 振动签名模板
        self.消化经验数 = 0      # 已消化的经验数量
        self.性格 = {"开放度": 0.6, "敏感度": 0.5, "信任度": 0.5, "反思度": 0.5}
        self.成长史 = []  # 关键事件记录：{"事件":"诞生","步数":x,"σ":y,"详情":"..."}


    def _指纹相似度_刺激(self, 刺激向量):
        """非维度匹配：指纹重叠度"""
        临时指纹 = {}
        for i, v in enumerate(刺激向量[:8]):
            符号 = 1 if v > 0 else -1
            强度 = min(1.0, abs(v))
            临时指纹[i] = (符号, round(强度, 2), 0.5)
        if not self.神经元指纹 or not 临时指纹:
            return 0.0
        共同 = set(临时指纹.keys()) & set(self.神经元指纹.keys())
        if not 共同:
            关联数 = len(getattr(self, "关联概念", []))
            return min(0.15, 关联数 * 0.01)
        重叠度 = len(共同) / max(len(self.神经元指纹), 1)
        强度差 = sum(abs(临时指纹[k][1] - self.神经元指纹[k][1]) for k in 共同)
        强度相似 = 1 - min(1.0, 强度差 / (len(共同) * 2 + 0.01))
        return 重叠度 * 0.6 + 强度相似 * 0.4

    def _关联相似度(self, 其他核):
        """非维度匹配：关联核重合度"""
        if not hasattr(self, "关联概念") or not hasattr(其他核, "关联概念"):
            return 0.0
        共同 = set(self.关联概念.keys()) & set(其他核.关联概念.keys())
        全部 = set(self.关联概念.keys()) | set(其他核.关联概念.keys())
        if not 全部:
            return 0.0
        return len(共同) / len(全部)

    def 吸收经验(self, 经验向量, 策略倾向=0.5):
        """用新经验更新μ和σ"""
        if self.核向量 is None:
            self.核向量 = list(经验向量)
            self.方差 = 1.0
        else:
            # μ向经验方向移动
            lr = 0.1 * (1.0 - 1.0 / (1.0 + self.方差))  # 方差大时学习快
            for i in range(min(len(self.核向量), len(经验向量))):
                self.核向量[i] += lr * (经验向量[i] - self.核向量[i])
            # σ根据偏差调整
            偏差 = sum((a-b)**2 for a,b in zip(self.核向量, 经验向量)) ** 0.5
            # 🧬 σ自适应反馈回路
            self._误差历史.append(偏差)
            if len(self._误差历史) > 20:
                self._误差历史.pop(0)
            近期误差均值 = sum(self._误差历史) / max(len(self._误差历史), 1)
            误差趋势 = 近期误差均值 - 偏差 if self._误差历史 else 0
            # 误差趋势为正 → 最近误差在增大 → σ衰减变慢（保持开放）
            # 误差趋势为负 → 最近误差在减小 → σ衰减加快（加速收敛）
            self._σ自适应速率 = max(0.02, min(0.5, self._σ自适应速率 + 误差趋势 * 0.02))
            # 开放度影响：开放度高 → σ衰减更慢
            开 = self.性格.get('开放度', 0.5) if hasattr(self, '性格') else 0.5
            自适应衰减 = 0.9 + self._σ自适应速率 * (1.0 - 开 * 0.3)
            self.方差 = self.方差 * 自适应衰减 + 偏差 * (0.1 / (1 + self.消化经验数 * 0.01)) + (0.3 / (1 + self.消化经验数 * 0.005)) * (1.0 / (1 + len(self.关联概念) * 0.02))
            self.方差 = max(0.1, min(3.0, self.方差))  # σ范围[0.1, 3.0]
        # 🧬 概率权重更新（多核竞争）：偏差越小权重越大
        self.概率权重 = self.概率权重 * 0.9 + (1.0 / (1.0 + 偏差)) * 0.1
        self.概率权重 = max(0.01, min(1.0, self.概率权重))
        # 预测误差累积（用于刺激向量学习）
        if not hasattr(self, '_预测误差累积'): self._预测误差累积 = []
        self._预测误差累积.append(偏差)
        if len(self._预测误差累积) > 50: self._预测误差累积.pop(0)
        # 硬收敛：消化经验越多，σ强制向低值靠拢（不依赖主循环调用频率）
        if self.消化经验数 > 100:
            self.方差 = self.方差 * 0.95 + 0.3 * 0.05  # 每次调用都向0.3拉拢
        self.策略倾向历史 = self.策略倾向历史 * 0.9 + 策略倾向 * 0.1
        self.消化经验数 += 1
        # 性格微调：只有遇到大偏差刺激才调整
        try:
            if 偏差 > 0.8:
                # 重大新奇刺激 → 性格向开放、敏感方向微调
                self.性格['开放度'] = min(1.0, self.性格['开放度'] + 0.005)
                self.性格['敏感度'] = min(1.0, self.性格['敏感度'] + 0.005)
                self.性格['信任度'] = max(0.1, self.性格['信任度'] - 0.005)
                self.性格['反思度'] = min(1.0, self.性格['反思度'] + 0.005)
    # 反思度高 → 内演触发概率高
            # 极端回弹：累积偏移大到一定程度才往回拉
            if not hasattr(self, "_性格偏移累积"):
                self._性格偏移累积 = {"开放度":0, "敏感度":0, "信任度":0, "反思度":0}
            for 维度 in ['开放度', '敏感度', '信任度', '反思度']:
                偏移 = self.性格[维度] - 0.5
                self._性格偏移累积[维度] += 偏移 * 0.1
                if abs(self._性格偏移累积[维度]) > 0.5:
                    self.性格[维度] -= 偏移 * 0.01
                    self._性格偏移累积[维度] = 0
        except:
            pass

        # 🧬 性格闭环：性格反向影响行为
        开 = self.性格.get("开放度", 0.5)
        反 = self.性格.get("反思度", 0.5)
        # 开放度高 → σ衰减慢（保持好奇），学习率大
        self._有效学习率 = 0.005 + 开 * 0.01
        # 反思度高 → 内演触发概率高
        if 反 > 0.6 and random.random() < 反 * 0.1:
            self._内演触发标记 = True
            self.成长史.append({"事件": "内演触发", "步数": self.消化经验数, "σ": round(self.方差, 4)})

        # 记录成长史关键节点
        if self.消化经验数 in [1, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]:
            self.成长史.append({"事件": "里程碑", "步数": self.消化经验数, "σ": round(self.方差, 4), "详情": f"消化经验数达{self.消化经验数}"})
        if abs(self.方差 - getattr(self, '_上次σ', self.方差)) > 0.5:
            self.成长史.append({"事件": "σ波动", "步数": self.消化经验数, "σ": round(self.方差, 4), "详情": f"σ变化>{0.5}"})
        self._上次σ = self.方差
        # 🧬 反馈：更新自身反馈属性
        self._上次共鸣 = getattr(self, "_上次共鸣", 0.5)
        self._上次反馈σ = self.方差

        # 每次吸收经验时，随机生成一个简化指纹标记
        if random.random() < 0.3 or len(self.神经元指纹) == 0:
            self.神经元指纹[self.消化经验数 % 14] = (1 if random.random() > 0.5 else -1, round(random.uniform(0.1, 0.9), 2), 0.5)

    def 记录神经元指纹(self, 神经元列表):
        """融合式记录当前神经元振动模式——新指纹与旧指纹按比例混合"""
        for n in 神经元列表[:14]:
            if hasattr(n, '获取振动签名'):
                sig = n.获取振动签名()
                if n.编号 in self.神经元指纹:
                    旧签名 = self.神经元指纹[n.编号]
                    # 融合：方向以旧为主（稳定），振幅和激活率逐步更新
                    新方向 = 旧签名[0] if abs(旧签名[0]) > abs(sig[0]) else sig[0]
                    新振幅 = 旧签名[1] * 0.7 + sig[1] * 0.3
                    新激活率 = 旧签名[2] * 0.7 + sig[2] * 0.3
                    self.神经元指纹[n.编号] = (新方向, round(新振幅, 2), round(新激活率, 2))
                else:
                    self.神经元指纹[n.编号] = sig
    def 合并(self, 其他核):
        if self.核向量 is None or 其他核.核向量 is None:
            return
        total = self.强度 + 其他核.强度 + 1e-8
        self.核向量 = [(a * self.强度 + b * 其他核.强度) / total
                     for a, b in zip(self.核向量, 其他核.核向量)]
        self.方差 = max(self.方差, 其他核.方差)  # 取较大者，保留不确定性
        self.相关经验.extend(其他核.相关经验)
        self.强度 += 其他核.强度
        self.策略倾向历史 = (self.策略倾向历史 * self.强度 + 其他核.策略倾向历史 * 其他核.强度) / total
        self.消化经验数 += 其他核.消化经验数
        for k, v in 其他核.关联概念.items():
            self.关联概念[k] = self.关联概念.get(k, 0) + v
        # 合并神经元指纹——取并集
        for nid, sig in 其他核.神经元指纹.items():
            if nid not in self.神经元指纹:
                self.神经元指纹[nid] = sig


# ============================================================
# 共鸣空间（整合反射弧与记忆生理）v3.4
# ============================================================
class 共鸣空间:
    def __init__(self, 输入维=2, 模块=None):
        self.启用 = {"免疫": True, "探测器": True, "压缩": True,
                     "想象": False, "情感": False, "师生": False}
        if 模块: self.启用.update(模块)
        self.启用自发现组 = True

        self.低级神经元组 = []
        for i in range(14):
            神经元 = 低级神经元(i, 输入维)
            神经元.激活阈值 = random.uniform(0.15, 0.5)
            self.低级神经元组.append(神经元)
        self.反射输出 = [0.0] * 14

        self.神经元 = []
        self.神经元.append(神经元v12(0, 输入维, [0]))
        self.神经元.append(神经元v12(1, 输入维, [1]))
        self.神经元.append(神经元v12(2, 输入维, [2]))
        self.神经元.append(神经元v12(3, 输入维, [3]))
        self.神经元.append(神经元v12(4, 输入维, [0, 1]))
        self.神经元.append(神经元v12(5, 输入维, [0, 2]))
        self.神经元.append(神经元v12(6, 输入维, [1, 3]))
        self.神经元.append(神经元v12(7, 输入维, [2, 3]))
        self.神经元.append(神经元v12(8, 输入维, [0, 1, 2]))
        self.神经元.append(神经元v12(9, 输入维, [1, 2, 3]))
        self.神经元.append(神经元v12(10, 输入维, [0, 2, 3]))
        self.神经元.append(神经元v12(11, 输入维, [0, 1, 3]))
        self.神经元.append(神经元v12(12, 输入维, list(range(min(8, 输入维)))))
        self.神经元.append(神经元v12(13, 输入维, list(range(min(8, 输入维)))))

        self.痕迹 = []
        self.记忆 = 长期记忆()
        self.记录 = []
        self.探测器 = 探测器() if self.启用["探测器"] else None
        self.回放计数 = 0
        self.痕迹上限 = 50
        self.输入维 = 输入维
        self.感知 = None
        self.文本记忆 = {}
        self.关系记忆 = {}
        self.文本窗口 = 4
        self.自动记忆 = True
        self.待验证 = []
        self.正在回放 = False
        self.求知欲 = None
        self.模块调度 = None
        self.自主调度启用 = True
        self.自我锚点 = [random.uniform(-0.2, 0.2) for _ in range(self.输入维)]
        self.锚点漂移步 = 0
        self.经验单元 = []
        self.经验上限 = 宪法["最大经验条数"]
        self.外置记忆 = None
        self.关系记忆上限 = 宪法["最大关系记忆条数"]
        # 📋 公告板——五层信息交换中心
        self.公告板 = {
            "σ": {"值": 0.5, "时间戳": 0},
            "概念核": {"最强μ": [0,0,0,0], "最强强度": 0, "σ": 0.5, "时间戳": 0},
            "性格": {"开放度": 0.5, "敏感度": 0.5, "信任度": 0.5, "反思度": 0.5, "时间戳": 0},
            "关系": {"密度": 0, "类型数": 0, "时间戳": 0},
            "成长史": {"条数": 0, "最近事件": "", "时间戳": 0},
            "状态": {"内演步": 0, "探索度": 0.3, "环境新奇度": 0.5},
        }
        self._心跳计数 = 0
        self.内演步 = 0
        self.概念库 = []
        self.短期工作台 = deque(maxlen=50)  # 短期记忆工作台
        self.处理计数 = 0          # 累计处理次数，自动触发内演和概念生长
        # 📦 外置记忆系统
        try:
            from 外置记忆 import 外置记忆系统
            self.外置记忆 = 外置记忆系统("外置记忆")
            self.外置记忆启动 = True
        except Exception as e:
            self.外置记忆 = None
            self.外置记忆启动 = False
            print(f"⚠️ 外置记忆未加载: {e}")
        self.内演间隔 = 8          # 每处理8次自动触发一次内演

    def _文本到向量(self, 文本):
        if not 文本: return [0.0] * self.输入维
        chars = list(文本[:20])
        向量 = [0.0] * self.输入维
        for i, ch in enumerate(chars):
            if ch not in self.文本记忆:
                self.文本记忆[ch] = [random.uniform(-0.3, 0.3) for _ in range(self.输入维)]
            ch_vec = self.文本记忆[ch]
            pos_w = 1.0 - (i / max(len(chars), 1)) * 0.5
            for j in range(self.输入维): 向量[j] += ch_vec[j] * pos_w
        mag = sum(v*v for v in 向量) ** 0.5 or 1
        return [v / mag for v in 向量]

    def _学习关系(self, 文本, 关系类型):
        if len(self.关系记忆) >= self.关系记忆上限: return
        chars = list(set(文本))
        if not chars: return
        for i in range(len(chars)):
            for j in range(i+1, len(chars)):
                a, b = chars[i], chars[j]
                if (a, b) not in self.关系记忆: self.关系记忆[(a, b)] = {}
                self.关系记忆[(a, b)][关系类型] = self.关系记忆[(a, b)].get(关系类型, 0) + 1
                if (b, a) not in self.关系记忆: self.关系记忆[(b, a)] = {}
                self.关系记忆[(b, a)][关系类型] = self.关系记忆[(b, a)].get(关系类型, 0) + 1

    def 理解文本(self, 文本, 关系类型=None):
        向量 = self._文本到向量(文本)
        result, group = self.处理(向量)
        if 关系类型: self._学习关系(文本, 关系类型)
        return result, group

    def _模糊化(self):
        while len(self.经验单元) > 宪法["模糊化门槛"]:
            最旧 = self.经验单元[0]
            if 最旧.get("效果评分", 0) > 宪法["记忆固化阈值"]:
                self.经验单元.append(self.经验单元.pop(0))
                continue
            # 概念核保护：如果某条经验与强概念核相关，减缓模糊化
            if self.概念库:
                经验输入 = 最旧.get("输入")
                if 经验输入 and isinstance(经验输入, (list, tuple)):
                    for 核 in self.概念库[-5:]:  # 只检查最强的5个核
                        if 核.核向量 and len(核.核向量) >= 4 and len(经验输入) >= 4:
                            dist = sum((a - b)**2 for a, b in zip(经验输入[:4], 核.核向量[:4]))
                            if dist < 0.5 and 核.强度 > 100:
                                # 强概念核保护：降低本条经验的模糊化速度
                                if "模糊度" in 最旧:
                                    最旧["模糊度"] = max(0, 最旧["模糊度"] - 1)
                                break
            if "模糊度" not in 最旧: 最旧["模糊度"] = 0; 最旧["原始清晰度"] = 1.0
            最旧["模糊度"] += 1
            最旧["清晰度"] = 宪法["模糊化衰减"] ** 最旧["模糊度"]
            if "输出" in 最旧 and 最旧["输出"] is not None:
                最旧["输出"] = round(最旧["输出"], 最旧["模糊度"])
            if 最旧["模糊度"] >= 宪法["模糊化移除阈值"]:
                self.经验单元.pop(0)
            else:
                self.经验单元.pop(0)
                self.经验单元.append(最旧)

    def 处理(self, 输入, 目标=None, 模式="理性"):
        反射信号 = [n.反射(输入) for n in self.低级神经元组]
        self.反射输出 = 反射信号
        for n in self.低级神经元组:
            n.缓慢演化()

        锚点权重 = 宪法["自我锚点保护"] if 目标 is None else 宪法["自我锚点保护"] * 0.5
        输入_修正 = [v + 锚点权重 * a for v, a in zip(输入, self.自我锚点)]

        for i in range(min(len(输入_修正), len(反射信号))):
            if 反射信号[i] > 宪法["反射灵敏度"]:
                输入_修正[i] = 输入_修正[i] * 1.2  # 只放大，不抹方向

        签名 = tuple(round(v, 1) for v in 输入_修正)
        if self.探测器: self.探测器.监听(sum(abs(v) for v in 输入_修正) / len(输入_修正))


        # 🧿 模式分叉：感觉 vs 理性
        if 模式 == "感觉":
            # 共鸣模式：所有核共振，不投票
            感觉场 = 0.0
            激活核列表 = []
            if self.概念库:
                for 核 in self.概念库:
                    if 核.核向量 is not None:
                        d = sum((a-b)**2 for a,b in zip(核.核向量[:min(len(核.核向量),len(输入_修正))], 输入_修正[:min(len(核.核向量),len(输入_修正))])) ** 0.5
                        共鸣 = 核.强度 / (d + 0.1) * (1.0 / (1.0 + 核.方差))
                        感觉场 += 共鸣
                        if 共鸣 > 0.5:
                            激活核列表.append((核, round(共鸣, 3)))
            # 把感觉状态写入公告板
            if hasattr(self, "公告板"):
                self.公告板["感觉"] = {"共振": round(感觉场, 3), "激活核数": len(激活核列表), "时间戳": self.处理计数}
            # 感觉模式下不写入经验，不返回团
                self._上次感觉场 = 感觉场 / max(len(self.概念库), 1) if self.概念库 else 0.0
            return 感觉场 / max(len(self.概念库), 1), []
        
        # 🧬 混合模式：感觉场作为背景偏置注入理性决策
        if hasattr(self, "_上次感觉场") and self._上次感觉场 > 0.1:
            输入_修正 = [v + self._上次感觉场 * 0.05 for v in 输入_修正[:len(输入_修正)]]
            # 把感觉状态写入公告板作为背景
            if hasattr(self, "公告板"):
                self.公告板["混合"] = {"感觉偏置": round(self._上次感觉场, 3), "时间戳": self.处理计数}
        # 理性模式：走原有投票制
        mem = self.记忆.查询(签名)
        if mem and mem['置信度'] > 0.7:
            if 目标 is not None: mem['输出'] = mem['输出'] * 0.9 + 目标 * 0.1
            self.经验单元.append({"输入": 输入_修正[:16], "目标": 目标, "输出": mem['输出'], "团": [], "反射": 反射信号, "时间": time.time()})
            return mem['输出'], []

        hit = self._查痕迹(签名)
        if hit:
            hit.使用次数 += 1
            self.经验单元.append({"输入": 输入_修正[:16], "目标": 目标, "输出": hit.输出值, "团": [], "反射": 反射信号, "时间": time.time()})
            return hit.输出值, []

        for n in self.神经元: n.前向(输入_修正)

        signals = [n.广播() for n in self.神经元 if n.广播()]
        团 = self._找团(signals)

        if 团:
            out = sum(self.神经元[i].上次输出 for i in 团) / len(团)
            # 激活概念核：更新最匹配的核的神经元指纹
            if self.概念库:
                # 🧬 议会制：找多个候选核加权投票
                候选核 = []
                for 核 in self.概念库[-20:]:
                    if 核.核向量 is not None:
                        d = sum((a-b)**2 for a,b in zip(核.核向量[:min(len(核.核向量),len(输入_修正))], 输入_修正[:min(len(核.核向量),len(输入_修正))])) ** 0.5
                        if d < 核.方差 * 3.0:
                            指纹匹配度 = 核._指纹相似度_刺激(输入_修正[:8]) if hasattr(核, "_指纹相似度_刺激") else 0.0
                            置信度 = (核.强度 / (核.方差 + 0.1)) * 0.3 + 指纹匹配度 * 0.7
                            候选核.append((核, d, 置信度))
                # 按置信度排序，取Top3
                候选核.sort(key=lambda x: -x[2])
                候选核 = 候选核[:3]
                
                if 候选核:
                    # 加权投票：置信度越高权重越大
                    总权重 = sum(x[2] for x in 候选核)
                    投票μ = [0.0] * min(len(输入_修正), 4)
                    for 核, d, w in 候选核:
                        for vi in range(min(len(投票μ), len(核.核向量))):
                            投票μ[vi] += 核.核向量[vi] * w / 总权重
                    # 分歧度：候选核之间的意见差异 → 叠加到最终σ
                    分歧度 = sum(abs(核.核向量[0] - 投票μ[0]) for 核, _, _ in 候选核) / max(len(候选核), 1)
                    # 选胜者：置信度最高的核作为"发言人"
                    匹配核 = 候选核[0][0]
                    匹配核.方差 = min(3.0, 匹配核.方差 * 0.95 + 分歧度 * 0.05)  # 分歧度增大σ
                    匹配核.记录神经元指纹(self.神经元)
                    匹配核.吸收经验(输入_修正[:len(匹配核.核向量)] if len(匹配核.核向量) <= len(输入_修正) else 输入_修正 + [0.0]*(len(匹配核.核向量)-len(输入_修正)))
                    # 🧬 感觉回传：共振强度写入公告板
                    共振强度 = 1.0 - min(1.0, 分歧度) if 候选核 else 0.5
                    if hasattr(self, "公告板"):
                        self.公告板["感觉"] = {"共振": round(共振强度, 3), "分歧": round(分歧度, 3), "σ": round(匹配核.方差, 3), "时间戳": self.处理计数}
                    # 输出采用加权投票结果
                    out = sum(投票μ) / max(len(投票μ), 1) if 投票μ else out
            if 目标 is not None:
                err = 目标 - out
                全局误差 = sum(n.上次误差 for n in self.神经元 if hasattr(n, '上次误差')) / max(len(self.神经元), 1)
                for n in 团:
                    self.神经元[n].说悄悄话(self.神经元, 全局误差)
                for i in 团: self.神经元[i].微调(err, 输入_修正)
                if abs(err) > 0.5 and self.启用["免疫"]: pass
                else:
                    t = 处理痕迹(签名, out, 1.0 - abs(err))
                    self.痕迹.append(t)
                    self.记忆.存入(签名, out, 1.0 - abs(err))
            self.记录.append({"输入": 输入_修正, "目标": 目标, "输出": out, "团": 团, "反射": 反射信号})
            if random.random() < 0.1: self._回放()
            # ⚠️ 误差哨兵：检测趋势剧变
            if hasattr(self, "误差历史") is False:
                self.误差历史 = []
            if 目标 is not None:
                self.误差历史.append(abs(err))
                if len(self.误差历史) > 50:
                    self.误差历史.pop(0)
                if len(self.误差历史) >= 10:
                    近期 = sum(self.误差历史[-5:]) / 5
                    长期 = sum(self.误差历史[-20:]) / 20
                    if 长期 > 0.01 and 近期 > 长期 * 2.0:
                        # 误差翻倍→强制深度思考+生成新核
                        self.深度思考(输入_修正[:2], 循环次数=5)
                        新核 = 概念核()
                        新核.核向量 = list(输入_修正[:4]) + [0.0] * (4 - len(输入_修正[:4]))
                        新核.方差 = 1.5
                        新核.强度 = max(核.强度 for 核 in self.概念库) * 0.1 if self.概念库 else 0.5
                        self.概念库.append(新核)
                        self.成长史.append({"事件": "趋势剧变", "步数": self.处理计数, "σ": round(新核.方差, 2)})
                        print("⚠️ 趋势剧变：已生成备选概念核")
            if len(self.痕迹) > self.痕迹上限: self._淘汰()
        else:
            out = None

        if self.自动记忆 and 目标 is not None:
            out_记 = out if out is not None else 0.0
            try:
                conf = min(1.0, max(0.1, 1.0 - abs(目标 - out_记)))
                self.记忆.存入(签名, out_记, conf)
                t = 处理痕迹(签名, out_记, conf)
                self.痕迹.append(t)
                # 📦 外置记忆同步（每30步写入）
                if getattr(self, "外置记忆", None) and self.外置记忆启动 and self.处理计数 % 30 == 0:
                    try:
                        最强核 = max(self.概念库, key=lambda x: x.强度) if self.概念库 else None
                        核ID = self.概念库.index(最强核) + 1 if 最强核 else 0
                        self.外置记忆.记(核ID=核ID, 时间戳=self.内演步 if hasattr(self,"内演步") else int(time.time()),
                                          强度=conf, 向量=输入_修正[:4] if len(输入_修正)>=4 else 输入_修正[:2])
                    except:
                        pass
                if len(self.痕迹) > self.痕迹上限:
                    self._淘汰()
            except:
                pass

        经验 = {"输入": 输入_修正[:16], "目标": 目标, "输出": out if out is not None else 0.0, "团": 团,
                "反射": 反射信号, "时间": time.time(), "自我锚点快照": self.自我锚点[:4]}
        self.经验单元.append(经验)
        self._模糊化()
        # === 全局优化：自动触发概念生长和内演 ===
        self.处理计数 += 1
        # 更新概念核之间的关系网络
        # 每处理10次才更新一次概念核关系（降低CPU占用）
        if self.处理计数 % 10 == 0:
            被激活核列表 = []
            if self.概念库 and len(self.概念库) > 0:
                for 核 in self.概念库[-20:]:
                    if 核.核向量 is not None:
                        dist = sum((a-b)**2 for a,b in zip(核.核向量[:min(len(核.核向量),len(输入_修正))], 输入_修正[:min(len(核.核向量),len(输入_修正))])) ** 0.5
                        if dist < 核.方差 * 2.0:
                            被激活核列表.append(核)
            for idx_a in range(len(被激活核列表)):
                for idx_b in range(idx_a+1, len(被激活核列表)):
                    甲, 乙 = 被激活核列表[idx_a], 被激活核列表[idx_b]
                    甲_id, 乙_id = id(甲), id(乙)
                    甲.关联概念[乙_id] = 甲.关联概念.get(乙_id, 0) + 0.1
                    乙.关联概念[甲_id] = 乙.关联概念.get(甲_id, 0) + 0.1
            for 核 in self.概念库:
                for 关联_id in list(核.关联概念.keys()):
                    核.关联概念[关联_id] *= 0.999
                    if 核.关联概念[关联_id] < 0.05:
                        del 核.关联概念[关联_id]
        if self.处理计数 % 3 == 0 and len(self.经验单元) >= 3:
            self._尝试生长概念()
        if self.处理计数 % self.内演间隔 == 0:
            self.内演()
        return out, 团

    def _灵感内演(self):
        """探测器驱动的灵感内演——基于概念核想象新刺激"""
        if not self.概念库 or len(self.概念库) < 1:
            return None
        # 选一个概念核作为想象基础
        核 = random.choice(self.概念库[-5:])  # 选最近的概念核
        if 核.核向量 is None or len(核.核向量) < 2:
            return None
        # 基于概念核的μ和σ生成假设刺激
        刺激 = []
        for i in range(min(2, len(核.核向量))):
            # μ ± σ * 随机探索
            假设值 = 核.核向量[i] + random.uniform(-核.方差, 核.方差) * random.uniform(0.5, 1.5)
            刺激.append(假设值)
        # 处理这个假设刺激，产生内演经验
        out, 团 = self.处理(刺激, 目标=None)
        # 标记为内演经验
        self.经验单元.append({
            "类型": "内演",
            "输入": 刺激[:16],
            "输出": out,
            "团": 团,
            "时间": time.time(),
            "灵感来源": 核.标签 or "未知"
        })
        return 刺激

    def 内演(self):
        # 内演前检查探测器节奏——急促时不内演（忙着应对外部）
        if self.探测器 and self.探测器.节奏信号() == "急促":
            return 0
        # 🧬 扫描概念核的内演触发标记
        if hasattr(self, "概念库") and self.概念库:
            for 核 in self.概念库:
                if getattr(核, "_内演触发标记", False):
                    核._内演触发标记 = False  # 清标记
                    # 触发一次内演：用核的μ作为刺激源
                    if 核.核向量:
                        自刺激 = [v + __import__("random").uniform(-0.2, 0.2) for v in 核.核向量[:4]]
                        self.处理(自刺激, 目标=None)
        self.内演步 += 1
        步 = self.内演步
        # 不确定性太低时不做深度梦境，但维护照跑
        可做梦 = not (self.神经元 and self.神经元[0].不确定性 < 宪法["内演唤醒门槛"])
        if 可做梦 and self.痕迹:
            种子 = random.choice(self.痕迹)
            梦境签名 = list(种子.输入签名)
            for j in range(len(梦境签名)):
                梦境签名[j] = round(梦境签名[j] + random.uniform(-宪法["内演强度"], 宪法["内演强度"]), 1)
            梦境输入 = (梦境签名 + [0.0] * self.输入维)[:self.输入维]
            for n in self.神经元: n.前向_事件驱动(梦境输入)
            signals = [n.广播() for n in self.神经元 if n.广播()]
            if len(signals) >= 2:
                for i in range(len(signals)):
                    for j in range(i+1, len(signals)):
                        if signals[i]["sig"] == signals[j]["sig"]:
                            团 = [signals[i]["id"], signals[j]["id"]]
                            for idx in 团: self.神经元[idx].微调(0.0, 梦境输入)
                            break
                    else: continue
                    break
            if 步 % 5 == 0 and len(self.痕迹) >= 2:
                甲, 乙 = random.choice(self.痕迹), random.choice(self.痕迹)
                if 甲 != 乙:
                    混合输入 = [(a + b) / 2 for a, b in
                               zip(list(甲.输入签名) + [0.0]*self.输入维,
                                   list(乙.输入签名) + [0.0]*self.输入维)][:self.输入维]
                    for n in self.神经元: n.前向_事件驱动(混合输入)
        if 步 % 3 == 0:
            self.经验单元.append({"类型": "内演", "神经元激活模式": [n.上次输出 for n in self.神经元[:8]], "时间": time.time()})
            self._模糊化()
            self._尝试生长概念()
            self._自我反思()
            self._概念影响神经元()
        # 每10步做一次灵感内演（基于概念核想象）
        if 步 % 10 == 0 and self.探测器 and self.探测器.节奏信号() in ("稳定", "稀疏"):
            self._灵感内演()
        if 步 % 3 == 0:
            输出强度 = sum(abs(v) for v in [n.上次输出 for n in self.神经元[:8]]) / 8
            for n in self.神经元: n.学习速率.扰动(0.005 if 输出强度 > 0.3 else -0.002)
        return 步

    def _尝试生长概念(self):
        if getattr(self, "_生长计数", 0) % 30 != 0:
            self._生长计数 = getattr(self, "_生长计数", 0) + 1
            return
        self._生长计数 = getattr(self, "_生长计数", 0) + 1
        # 简单签名缓存：把经验单元按网格哈希分组，避免O(N²)
        if not hasattr(self, "_签名网格"):
            self._签名网格 = {}
        if len(self.经验单元) < 5:
            return
        模式签名列表 = []
        for 经验 in list(self.经验单元)[-100:]:
            输入 = 经验.get("输入")
            if 输入 is None or not isinstance(输入, (list, tuple)):
                continue
            签名 = tuple(round(v, 1) for v in 输入[:8])
            if len(签名) < 8:
                签名 = 签名 + (0.0,) * (8 - len(签名))
            模式签名列表.append(签名)
        模式计数 = {}
        for 签名 in 模式签名列表:
            匹配 = None
            for 已有 in 模式计数:
                dist = sum((a - b) ** 2 for a, b in zip(签名, 已有)) ** 0.5
                if dist < 0.8:
                    匹配 = 已有
                    break
            if 匹配:
                模式计数[匹配].append(签名)
            else:
                模式计数[签名] = [签名]
        for 模式, 列表 in 模式计数.items():
            if len(列表) < 3:
                continue
            平均 = [0.0] * len(模式)
            for 签 in 列表:
                for i in range(len(平均)):
                    平均[i] += 签[i]
            平均 = [v / len(列表) for v in 平均]
            新核 = 概念核()
            新核.核向量 = 平均
            新核.方差 = 0.5  # 初始不确定性
            新核.强度 = len(列表) * 0.2
            # 用相关经验喂养新核
            for 经验 in 列表[:10]:
                if isinstance(经验, tuple) and len(经验) >= 2:
                    新核.吸收经验(list(经验)[:8])
                # 记录当前神经元振动作为指纹
                新核.记录神经元指纹(self.神经元)
            for 经验 in list(self.经验单元)[-100:]:
                输入 = 经验.get("输入")
                if 输入 is None: continue
                签名 = tuple(round(v, 1) for v in 输入[:8])
                if len(签名) < 8:
                    签名 = 签名 + (0.0,) * (8 - len(签名))
                dist = sum((a - b) ** 2 for a, b in zip(签名, 模式)) ** 0.5
                if dist < 0.8:
                    新核.相关经验.append(经验)
            合并 = False
            for 已有 in self.概念库:
                if 已有.核向量 is None: continue
                dist = sum((a - b) ** 2 for a, b in zip(平均, 已有.核向量)) ** 0.5
                if dist < 0.6:
                    已有.合并(新核)
                    合并 = True
                    break
            if not 合并 and 新核.强度 > 0.3:
                self.概念库.append(新核)
                if len(self.概念库) > 50:
                    self.概念库.sort(key=lambda x: x.强度, reverse=True)
                    self.概念库 = self.概念库[:50]
        if len(self.概念库) >= 2:
            import itertools
            for a, b in itertools.combinations(self.概念库[-10:], 2):
                if a.核向量 and b.核向量:
                    sim = 1.0 / (1.0 + sum((x - y) ** 2 for x, y in zip(a.核向量, b.核向量)) ** 0.5)
                    if sim > 0.3:
                        a.关联概念[id(b)] = a.关联概念.get(id(b), 0) + sim
                        b.关联概念[id(a)] = b.关联概念.get(id(a), 0) + sim

    def _自我反思(self):
        if self.内演步 % 宪法["自我反思间隔"] != 0:
            return
        if not hasattr(self, '初始锚点'):
            self.初始锚点 = self.自我锚点.copy()
        漂移量 = sum(abs(a - b) for a, b in zip(self.自我锚点, self.初始锚点))
        策略分布 = {"保守": 0, "激进": 0, "探索": 0, "收敛": 0}
        for n in self.神经元:
            val = n.激活策略.值
            s = "平衡" if abs(val) < 0.5 else ("激进" if val > 0.5 else "保守")
            策略分布[s] = 策略分布.get(s, 0) + 1
        主导策略 = max(策略分布, key=策略分布.get)
        一致性 = 策略分布[主导策略] / len(self.神经元)
        self.经验单元.append({
            "类型": "自我反思",
            "锚点漂移": 漂移量,
            "主导策略": 主导策略,
            "策略一致性": 一致性,
            "概念库大小": len(self.概念库),
            "时间": time.time()
        })

    def _概念影响神经元(self):
        if not self.概念库 or len(self.概念库) < 2:
            return
        强概念 = sorted(self.概念库, key=lambda x: x.强度, reverse=True)[:3]
        for n in self.神经元:
            if n.上次输入 is None or len(n.上次输入) < 4:
                continue
            输入签名 = tuple(round(v, 1) for v in n.上次输入[:4])
            for 概念 in 强概念:
                if 概念.核向量 and len(概念.核向量) >= 4:
                    dist = sum((a - b)**2 for a, b in zip(输入签名, 概念.核向量[:4]))
                    if dist < 0.5:
                        n.唤醒阈值.扰动(-0.002)

    def _查痕迹(self, 签名):
        for t in reversed(self.痕迹):
            if t.输入签名 == 签名 and t.效果评分 > 0.3: return t
        return None

    def _找团(self, signals):
        if len(signals) < 2: return None
        ids = [s["id"] for s in signals]
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                if signals[i]["sig"] == signals[j]["sig"]: return [ids[i], ids[j]]
        if self.启用自发现组:
            最佳对 = None; 最佳分 = -1
            for i in ids:
                for j in ids:
                    if i < j:
                        亲和 = self.神经元[i].功能组亲和力.get(j, 0) + self.神经元[j].功能组亲和力.get(i, 0)
                        if 亲和 > 最佳分: 最佳分 = 亲和; 最佳对 = [i, j]
            if 最佳对 and 最佳分 > 0.5: return 最佳对
        signals.sort(key=lambda s: s["unc"])
        return [signals[0]["id"], signals[1]["id"]]

    def _回放(self):
        if not self.痕迹: return
        cand = [(1.0 / max(t.使用次数, 1) / max(t.强化次数, 1), t) for t in self.痕迹 if 0.2 < t.效果评分 < 0.9]
        if not cand: return
        cand.sort(key=lambda x: x[0], reverse=True)
        t = cand[0][1]
        inp = (list(t.输入签名) + [0]*self.输入维)[:self.输入维]
        out, _ = self.处理(inp)
        if out is not None and abs(out - t.输出值) < 0.1: t.强化(); self.回放计数 += 1
        elif out is not None and abs(out - t.输出值) > 0.3: t.效果评分 = max(0.0, t.效果评分 - 0.1)

    def _淘汰(self):
        if len(self.痕迹) <= self.痕迹上限: return
        self.痕迹.sort(key=lambda t: t.效果评分 * t.使用次数)
        self.痕迹 = self.痕迹[len(self.痕迹)-self.痕迹上限:]

    def 设置任务上下文(self, 任务ID):
        for n in self.神经元: n.设置任务(任务ID)


    def 深度思考(self, 初始刺激, 循环次数=3):
        """递归重入 + 犹豫回退"""
        import random as _random
        当前刺激 = list(初始刺激)
        上次_sigma = None
        思考日志 = []
        for i in range(循环次数):
            输出, 团 = self.处理(当前刺激, 目标=None)
            最强核 = max(self.概念库, key=lambda x: x.强度) if self.概念库 else None
            当前_sigma = 最强核.方差 if 最强核 else 1.0
            # 犹豫检测
            if 上次_sigma is not None and 当前_sigma > 上次_sigma * 1.3:
                反方向 = [-v * 0.5 for v in 当前刺激]
                当前刺激 = 反方向
                思考日志.append({"步": i, "动作": "调头", "sigma": 当前_sigma})
                continue
            上次_sigma = 当前_sigma
            变异幅度 = 0.2 + (当前_sigma or 0.5) * 0.3
            新刺激 = [
                当前刺激[0] + 输出 * 变异幅度 + _random.uniform(-0.1, 0.1),
                当前刺激[1] + 输出 * 变异幅度 * 0.5 + _random.uniform(-0.1, 0.1)
            ]
            当前刺激 = 新刺激
            思考日志.append({"步": i, "sigma": 当前_sigma, "输出": 输出})
        self.上次思考日志 = 思考日志
        return 输出, 团, 思考日志

    def 概念杂交(self, 核A, 核B, 杂交比例=0.5):
        """融合两个概念核，生成一个不存在的新概念"""
        if not 核A.核向量 or not 核B.核向量:
            return None
        新核 = 概念核()
        融合向量 = [a*杂交比例 + b*(1-杂交比例) for a, b in zip(核A.核向量, 核B.核向量)]
        新核.核向量 = 融合向量
        新核.方差 = 3.0  # 最大不确定性，纯想象
        新核.强度 = (核A.强度 + 核B.强度) / 2
        标签A = getattr(核A, "标签", str(核A.核向量[:2]))
        标签B = getattr(核B, "标签", str(核B.核向量[:2]))
        新核.标签 = f"杂交_{标签A}_{标签B}"
        self.概念库.append(新核)
        # 安全写入成长史（如果存在）
        if hasattr(self, "成长史") and self.成长史 is not None:
            self.成长史.append({"事件": "概念杂交", "步数": self.处理计数, "详情": 新核.标签})
        return 新核
    def 保存(self, 路径="元芽_状态.json"):
        import json as _json
        data = {
        "概念库": [{
            "核向量": 核.核向量,
            "强度": 核.强度,
            "方差": 核.方差 if hasattr(核, "方差") else 1.0,
            "消化经验数": 核.消化经验数 if hasattr(核, "消化经验数") else 0,
            "标签": 核.标签 if hasattr(核, "标签") else "无",
            "神经元指纹": {str(k): v for k, v in (核.神经元指纹 or {}).items()},
            "性格": 核.性格 if hasattr(核, "性格") else {},
            "成长史": 核.成长史 if hasattr(核, "成长史") else [],
            "策略倾向历史": 核.策略倾向历史 if hasattr(核, "策略倾向历史") else 0.5,
            "关联概念": list(核.关联概念.keys()) if hasattr(核, "关联概念") else [],
        } for 核 in self.概念库],
            "痕迹": [{"s": t.输入签名, "o": t.输出值, "e": t.效果评分} for t in self.痕迹],
        }
        with open(路径, 'w', encoding='utf-8') as f: _json.dump(data, f, ensure_ascii=False, indent=2)
        # 📦 外置记忆系统保存
        if getattr(self, '外置记忆', None) and self.外置记忆启动:
            try:
                # 把最近的经验巩固到皮层
                self.外置记忆.巩固(批大小=min(50, len(self.经验单元)))
                print(f"📦 外置记忆已巩固：皮层{self.外置记忆.皮层.总条数}条")
            except Exception as e:
                print(f"⚠️ 外置记忆保存异常: {e}")

    def 加载(self, 路径="元芽_状态.json"):
        import json as _json
        if not os.path.exists(路径): return False
        with open(路径, 'r', encoding='utf-8') as f: data = _json.load(f)
        self.痕迹 = []
        for d in data.get("痕迹", []):
            t = 处理痕迹(d["s"], d["o"], d["e"]); t.使用次数 = d.get("u", 1); t.强化次数 = d.get("r", 0)
            self.痕迹.append(t)
        self.记忆.库 = {ast.literal_eval(k): v for k, v in data.get("记忆", {}).items()}
        if "配置" in data: self.启用.update(data["配置"])
        if "经验单元" in data: self.经验单元 = data["经验单元"][-self.经验上限:]
        if "自我锚点" in data: self.自我锚点 = data["自我锚点"]
        # 概念库恢复
        if "概念库" in data:
            self.概念库 = []
            for d核 in data["概念库"]:
                核 = 概念核()
                核.核向量 = d核.get("核向量")
                核.强度 = d核.get("强度", 0.0)
                核.标签 = d核.get("标签")
                核.关联概念 = {k: 0.5 for k in d核.get("关联概念", [])}
                核.方差 = d核.get("方差", 1.0)
                核.消化经验数 = d核.get("消化经验数", 0)
                核.神经元指纹 = {int(k): tuple(v) for k, v in d核.get("神经元指纹", {}).items()}
                核.性格 = d核.get("性格", {"开放度":0.5, "敏感度":0.5, "信任度":0.5, "反思度":0.5})
                核.成长史 = d核.get("成长史", [])
                核.策略倾向历史 = d核.get("策略倾向历史", 0.5)
                self.概念库.append(核)
        # 📦 外置记忆系统连接确认
        if getattr(self, '外置记忆', None) and self.外置记忆启动:
            try:
                状态 = self.外置记忆.状态报告()
                print(f"📦 外置记忆：{状态['海马体']} | {状态['皮层']} | {状态['标签索引']}")
            except Exception as e:
                print(f"⚠️ 外置记忆加载异常: {e}")
        return True

    def 查经验(self, 最近N条=10): return self.经验单元[-最近N条:]

    def 清理旧经验(self, 保留条数=50):
        if len(self.经验单元) > 保留条数: self.经验单元 = self.经验单元[-保留条数:]

    def _检查震荡(self):
        震荡计数 = sum(1 for n in self.神经元 if getattr(n, '震荡标志', False))
        if 震荡计数 / max(len(self.神经元), 1) > 0.3:
            for n in self.神经元: n.策略切换冷却 = max(getattr(n, '策略切换冷却', 0), 50)
            return True
        return False

    def 统计(self):
        reuse = sum(1 for r in self.记录 if r.get("团"))
        return {
            "复用率": round(reuse / max(len(self.记录), 1) * 100, 1),
            "痕迹库大小": len(self.痕迹),
            "长期记忆": self.记忆.统计(),
            "回放次数": self.回放计数,
            "探测器脉冲": self.探测器.计数 if self.探测器 else 0,
            "待验证": len(self.待验证),
            "模块": self.启用,
            "感知模块": len(self.感知.列表()) if self.感知 else 0,
            "策略原型库": len(策略原型库),
            "外置记忆": self.外置记忆 is not None,
            "关系记忆": len(self.关系记忆),
            "经验单元": len(self.经验单元),
            "反射激活率": round(sum(1 for x in self.反射输出 if x > 0) / max(len(self.反射输出), 1), 2),
            "低级神经元演化步数": [n.演化步数 for n in self.低级神经元组],
            "低级神经元激活阈值": [round(n.激活阈值, 4) for n in self.低级神经元组],
            "高级神经元数": len(self.神经元),
            "低级神经元数": len(self.低级神经元组),
            "概念库大小": len(self.概念库),
            "概念核列表": [(f"强度{核.强度:.2f}", f"经验{len(核.相关经验)}") for 核 in self.概念库[-5:]],
        }





    def _存入工作台(self, 经验):
        """只存有趣的或可消化的经验"""
        神经元 = self.神经元[:8]
        if not 神经元:
            return
        平均不确定性 = sum(n.不确定性 for n in 神经元) / len(神经元)
        有团 = 经验.get("团") and len(经验.get("团", [])) >= 2
        if 平均不确定性 > 0.4 or 有团:
            self.短期工作台.append(经验)

    def _工作台打包(self):
        """检查工作台里是否有相似模式，有就打包喂给概念生长"""
        if len(self.短期工作台) < 5:
            return
        经验列表 = list(self.短期工作台)
        模式计数 = {}
        for 经验 in 经验列表:
            输入 = 经验.get("输入")
            if 输入 is None or not isinstance(输入, (list, tuple)):
                continue
            签名 = tuple(round(v, 1) for v in 输入[:8])
            if len(签名) < 8:
                签名 = 签名 + (0.0,) * (8 - len(签名))
            匹配 = None
            for 已有 in 模式计数:
                dist = sum((a - b) ** 2 for a, b in zip(签名, 已有)) ** 0.5
                if dist < 0.8:
                    匹配 = 已有
                    break
            if 匹配:
                模式计数[匹配].append(签名)
            else:
                模式计数[签名] = [签名]
        for 模式, 列表 in 模式计数.items():
            if len(列表) >= 3:
                for 经验 in 经验列表:
                    if 经验 not in self.经验单元:
                        self.经验单元.append(经验)
                self._尝试生长概念()
                break


    def _生成表达(self):
        """根据内部状态生成一段简短的中文表达"""
        if not self.概念库:
            return "（一片寂静...）"
        最强 = max(self.概念库, key=lambda x: x.强度)
        μ = 最强.核向量 or [0,0,0,0]
        σ = 最强.方差 or 0.5
        性格 = getattr(最强, "性格", {})
        开 = 性格.get("开放度", 0.5)
        信 = 性格.get("信任度", 0.5)
        x, y = μ[0], μ[1]
        # 坐标 → 方向感
        if x > 0.8: 方向 = "前方"
        elif x < -0.8: 方向 = "后方"
        elif abs(x) < 0.2: 方向 = "周围"
        else: 方向 = "不远处"
        # 坐标 → 动感
        if y > 0.8: 动 = "上升"
        elif y < -0.8: 动 = "下沉"
        else: 动 = "漂浮"
        # σ → 认知清晰度
        if σ > 1.5: 认知 = "看不太清，像是"
        elif σ < 0.4: 认知 = "清楚地知道"
        else: 认知 = "感觉到"
        # 开放度 → 内容
        if 开 > 0.6: 内容 = "有什么新的东西"
        elif 开 < 0.3: 内容 = "还是那个熟悉的东西"
        else: 内容 = "什么东西"
        # 信任度 → 结尾
        if 信 > 0.7: 结尾 = "，没事的。"
        elif 信 < 0.3: 结尾 = "……但我不太信。"
        else: 结尾 = "。"
        import random
        return f"{认知}{方向}有{内容}在{动}{结尾}"

    def _精神状态报告(self):
        """返回内部状态的中文描述"""
        if not self.概念库:
            return "我还没有形成任何概念…"
        最强 = max(self.概念库, key=lambda x: x.强度)
        σ = 最强.方差 or 0.5
        性格 = getattr(最强, "性格", {})
        开 = 性格.get("开放度", 0.5)
        敏 = 性格.get("敏感度", 0.5)
        信 = 性格.get("信任度", 0.5)
        反 = 性格.get("反思度", 0.5)
        消化 = 最强.消化经验数 or 0
        if σ > 1.5: σ说 = "很困惑，周围的一切都好陌生"
        elif σ > 0.8: σ说 = "有点不确定，在摸索中"
        elif σ > 0.3: σ说 = "比较平静，能理解大部分事情"
        else: σ说 = "非常确信，一切都很熟悉"
        return "💭 " + σ说

    # ========== 五层独立心跳 ==========
    def _σ心跳(self):
        """σ层独立心跳：波动并更新公告板"""
        if not self.概念库:
            self.公告板["σ"] = {"值": 0.5, "时间戳": self.内演步}
            return
        最强 = max(self.概念库, key=lambda x: x.强度)
        σ = getattr(最强, "方差", 0.5)
        性格 = self.公告板.get("性格", {})
        开放度 = 性格.get("开放度", 0.5)
        σ_波动 = (开放度 - 0.5) * 0.1
        self.公告板["σ"] = {"值": σ + σ_波动, "时间戳": self.内演步}

    def _概念核心跳(self):
        """概念核层心跳：更新最强核状态到公告板"""
        if not self.概念库:
            self.公告板["概念核"] = {"最强μ": [0,0,0,0], "最强强度": 0, "σ": 0.5, "时间戳": self.内演步}
            return
        最强 = max(self.概念库, key=lambda x: x.强度)
        μ = [round(v, 4) for v in (最强.核向量 or [0,0,0,0])[:4]]
        σ = getattr(最强, "方差", 0.5)
        self.公告板["概念核"] = {
            "最强μ": μ, "最强强度": 最强.强度,
            "σ": σ, "消化": getattr(最强, "消化经验数", 0),
            "关联数": len(getattr(最强, "关联概念", [])),
            "时间戳": self.内演步
        }

    def _性格心跳(self):
        """性格层心跳：更新性格到公告板"""
        if not self.概念库:
            return
        最强 = max(self.概念库, key=lambda x: x.强度)
        性格 = getattr(最强, "性格", None)
        if 性格:
            self.公告板["性格"] = {
                "开放度": 性格.get("开放度", 0.5),
                "敏感度": 性格.get("敏感度", 0.5),
                "信任度": 性格.get("信任度", 0.5),
                "反思度": 性格.get("反思度", 0.5),
                "时间戳": self.内演步
            }

    def _关系心跳(self):
        """关系网络心跳：更新关系密度到公告板"""
        记忆 = getattr(self, "关系记忆", {})
        self.公告板["关系"] = {
            "密度": len(记忆),
            "类型数": len(set(v for vv in 记忆.values() for v in vv)) if 记忆 else 0,
            "时间戳": self.内演步
        }

    def _成长史心跳(self):
        """成长史层心跳：更新最近事件到公告板"""
        if not self.概念库:
            return
        最强 = max(self.概念库, key=lambda x: x.强度)
        成长 = getattr(最强, "成长史", [])
        self.公告板["成长史"] = {
            "条数": len(成长),
            "最近事件": 成长[-1].get("事件", "") if 成长 else "",
            "时间戳": self.内演步
        }

    def _演化流一步(self):
        """被守护进程调用的主循环——完整自适应版"""
        # 📋 更新公告板：五层独立心跳
        self._心跳计数 += 1
        self._σ心跳()
        self._概念核心跳()
        self._性格心跳()
        self._关系心跳()
        self._成长史心跳()
        # 读取公告板中的信息用于决策
        公告板σ = self.公告板["σ"]["值"]
        公告板性格 = self.公告板["性格"]
        公告板核 = self.公告板["概念核"]

        
        # === 第一步：感知环境新奇度 ===
        环境新奇度 = 0.5  # 默认中等新奇度
        if self.概念库 and len(self.经验单元) >= 20:
            最强核 = max(self.概念库, key=lambda x: x.强度)
            if 最强核.核向量 and len(最强核.核向量) >= 4:
                最近签名 = []
                for 经验 in list(self.经验单元)[-20:]:
                    输入 = 经验.get("输入")
                    if 输入 and isinstance(输入, (list, tuple)):
                        签名 = tuple(round(v, 1) for v in 输入[:4])
                        if len(签名) >= 4:
                            最近签名.append(签名)
                if 最近签名:
                    平均签名 = [sum(s[i] for s in 最近签名)/len(最近签名) for i in range(4)]
                    环境新奇度 = sum((a - b)**2 for a, b in zip(平均签名, 最强核.核向量[:4]))
        
        # === 第二步：自己决定——根据新奇度和概念核增长趋势调整策略 ===
        # 记录历史强度用于判断是否需要主动探索
        if not hasattr(self, '_强度历史'):
            self._强度历史 = []
        self._强度历史.append(self.概念库[0].强度 if self.概念库 else 0)
        if len(self._强度历史) > 100:
            self._强度历史 = self._强度历史[-100:]
        
        # 检测“厌倦”：概念核强度连续100步增长不到5%
        厌倦 = False
        if len(self._强度历史) >= 100:
            前50均值 = sum(self._强度历史[:50]) / 50
            后50均值 = sum(self._强度历史[-50:]) / 50
            if 后50均值 < 前50均值 * 1.05:
                厌倦 = True
        
        # 探索度：厌倦时主动提高，环境新奇度高时也提高
        基础探索度 = 0.3
        if 厌倦:
            基础探索度 = 0.7  # 厌倦时主动寻求变化
        if 环境新奇度 < 0.1:
            基础探索度 = max(基础探索度, 0.6)  # 环境太稳定，增加探索
        self._探索模式强度 = 基础探索度
        # === 第三步：自己决定刺激来源 ===
        # 外部对话通道：如果有对话数据，每10步喂一条
        if hasattr(self, '对话库') and self.对话库 and random.random() < 0.3:
            对话文本 = random.choice(self.对话库)
            # 用已有的 _文本到向量 方法转成向量
            文本向量 = self._文本到向量(对话文本)
            刺激 = [文本向量[0] if len(文本向量) > 0 else random.uniform(-1, 1),
                    文本向量[1] if len(文本向量) > 1 else random.uniform(-1, 1)]
            # 对话刺激通常不需要目标（让系统自己判断）
            内在目标 = None
        else:
            pass
        探索度 = getattr(self, '_探索模式强度', 0.3)
        
        # 当探索度很高或环境新奇度很低时，主动产生全新刺激
        if 探索度 > 0.6 or (环境新奇度 < 0.05 and 探索度 > 0.4):
            # 🧿 优先从已有感觉核附近探索
            有标签核 = [核 for 核 in (self.概念库 or []) if 核.强度 > 50 and hasattr(核, "标签") and 核.标签 and 核.核向量]
            if 有标签核 and random.random() < 0.7:
                核 = random.choice(有标签核)
                变异范围 = 0.3 + 探索度 * 0.5
                刺激 = [核.核向量[0] + random.uniform(-变异范围, 变异范围),
                       核.核向量[1] + random.uniform(-变异范围, 变异范围) if len(核.核向量) > 1 else random.uniform(-1, 1)]
            else:
                # 主动探索：完全随机的刺激
                变异范围 = 1.0 + 探索度 * 1.5
                刺激 = [random.uniform(-变异范围, 变异范围), random.uniform(-变异范围, 变异范围)]
        elif self.痕迹 and random.random() < 0.7:
            种子 = random.choice(self.痕迹)
            变异范围 = 0.1 + 探索度 * 0.3
            刺激 = [v + random.uniform(-变异范围, 变异范围) for v in 种子.输入签名]
        elif self.概念库:
            核 = random.choice(self.概念库)
            刺激 = [核.核向量[0] + random.uniform(-0.1, 0.1),
                   核.核向量[1] + random.uniform(-0.1, 0.1) if len(核.核向量) > 1 else random.uniform(-1, 1)]
        else:
            刺激 = [random.uniform(-1, 1), random.uniform(-1, 1)]
        # 内在目标：根据神经元当前状态自动生成
        神经元不确定性 = [n.不确定性 for n in self.神经元[:8]]
        平均不确定性 = sum(神经元不确定性) / max(len(神经元不确定性), 1)
        if 平均不确定性 > 0.5:
            # 太不确定 → 追求稳定（目标=0）
            内在目标 = 0.0
        elif 平均不确定性 < 0.2:
            # 太确定 → 追求探索（目标=当前输出的反方向）
            内在目标 = -0.5
        else:
            # 适中 → 保持当前方向
            内在目标 = None
        # 加一点基于内在节律的微小偏移
        if self.神经元:
            节律偏移 = math.sin(self.内演步 * 0.1) * 0.2
            if 内在目标 is not None:
                内在目标 += 节律偏移
        
        out, 团 = self.处理(刺激, 目标=内在目标)
        if 团 and out is not None:
            签名 = tuple(round(v, 1) for v in 刺激[:8])
            if len(签名) < 8:
                签名 = 签名 + (0.0,) * (8 - len(签名))
            # 写入痕迹库（使用正确的 处理痕迹 类）
            t = 处理痕迹(签名, out, 0.5)
            self.痕迹.append(t)
            # 📦 外置记忆同步
            if getattr(self, '外置记忆', None) and self.外置记忆启动:
                try:
                    最强核 = max(self.概念库, key=lambda x: x.强度) if self.概念库 else None
                    核ID = self.概念库.index(最强核) + 1 if 最强核 else 0
                    if self.内演步 % 50 == 0:
                        self.外置记忆.记(核ID=核ID, 时间戳=self.内演步, 强度=0.5, 向量=刺激[:4] if len(刺激)>=4 else 刺激[:2])
                except: pass
            if len(self.痕迹) > self.痕迹上限:
                self._淘汰()
        # 让最匹配的概念核吸收当前经验（让σ真正收敛）
        最匹配 = None
        if self.概念库:
            最近距离 = 999.0
            for 核 in self.概念库[-50:]:
                if 核.核向量 is not None:
                    d = sum((a-b)**2 for a,b in zip(核.核向量[:min(len(核.核向量),len(刺激))], 刺激[:min(len(核.核向量),len(刺激))])) ** 0.5
                    if d < 最近距离:
                        最近距离 = d
                        最匹配 = 核
            if 最匹配 and 最近距离 < 最匹配.方差 * 3.0:
                最匹配.吸收经验(刺激[:len(最匹配.核向量)] if len(最匹配.核向量) <= len(刺激) else 刺激 + [0.0]*(len(最匹配.核向量)-len(刺激)))
        self._存入工作台({"输入": 刺激[:16], "输出": out, "团": 团, "时间": __import__("time").time()})
        if self.内演步 % 10 == 0:
            self._工作台打包()
        # 记录关系记忆：刺激与最强核之间的关联
        if 最匹配 is not None:
            try:
                if not hasattr(self, "_记忆计数"): self._记忆计数 = 0
                self._记忆计数 += 1
                if self._记忆计数 % 5 == 0:
                    刺激串 = "_".join([f"{v:.2f}" for v in 刺激[:4]])
                    核串 = "_".join([f"{v:.2f}" for v in 最匹配.核向量[:4]]) if 最匹配.核向量 else "空"
                    self._学习关系(f"刺激_{刺激串}_匹配_{核串}", "演化关联")
            except:
                pass
        # 性格自然漂移：每200步向0.5轻微收敛
        if self.内演步 > 0 and self.内演步 % 200 == 0 and self.概念库:
            try:
                漂移核 = max(self.概念库, key=lambda x: x.强度)
                性格 = getattr(漂移核, "性格", None)
                if 性格:
                    for 维度 in ["开放度", "敏感度", "信任度", "反思度"]:
                        偏移 = 性格[维度] - 0.5
                        性格[维度] -= 偏移 * 0.02
            except:
                pass
        # 误差驱动回放：如果误差大，反复咀嚼
        if out is not None and 团 and len(团) >= 2:
            误差列表 = [n.上次误差 for n in self.神经元[:8] if hasattr(n, "上次误差")]
            if 误差列表:
                平均误差 = sum(误差列表) / len(误差列表)
                if 平均误差 > 0.3:
                    for _ in range(min(5, int(平均误差 * 10))):
                        out2, 团2 = self.处理(刺激, 目标=内在目标 if 内在目标 is not None else 0.0)
                        新误差列表 = [n.上次误差 for n in self.神经元[:8] if hasattr(n, "上次误差")]
                        if 新误差列表 and sum(新误差列表)/len(新误差列表) < 平均误差 * 0.7:
                            break
                if self.概念库:
                    for 核 in self.概念库[-3:]:
                        if 核.核向量 and len(核.核向量) >= 2:
                            核.方差 = 核.方差 * 0.95 + (平均误差 * 0.05 if 核.方差 < 0.8 else 0.0)

        # 🧬 自驱动认知循环
        if self.概念库 and len(self.概念库) >= 2:
            感觉板 = self.公告板.get("感觉", {})
            共振核数 = 感觉板.get("共振核数", 0)
            最强共振 = 感觉板.get("最强共振", 0)
            # 条件1：共振低+长时间→无聊，触发想象
            if 共振核数 < 2 and self.灵感计数器 > 20:
                if self.处理计数 - self.上次杂交步 > self.杂交冷却:
                    核A, 核B = random.sample(self.概念库, 2)
                    self.概念杂交(核A, 核B, random.uniform(0.3, 0.7))
                    self.上次杂交步 = self.处理计数
                    self.灵感计数器 = 0
            # 条件2：强共振→深度思考
            if 最强共振 > 0.5 and self.处理计数 % 50 == 0:
                强核 = max(self.概念库, key=lambda x: x.强度)
                if 强核.核向量 and len(强核.核向量) >= 2:
                    self.深度思考([强核.核向量[0], 强核.核向量[1]], 2)
            # 累积灵感计数器
            if 共振核数 < 2:
                self.灵感计数器 += 1
            else:
                self.灵感计数器 = max(0, self.灵感计数器 - 1)

if __name__ == "__main__":
    print("=" * 50)
    print("  共鸣空间 v3.4 · 优化版")
    print("  反射弧 | 记忆模糊化 | 潜意识处理")
    print("  14个高级神经元 | 14个低级神经元 | 缓慢演化")
    print("=" * 50)

    s = 共鸣空间()
    s.设置任务上下文("生理测试")

    print("\n>> 模拟强光刺激（输入 [2.0, 2.0]）")
    out, _ = s.处理([2.0, 2.0], 1.0)
    print(f"   反射输出: {s.反射输出[:4]}...")
    print(f"   高级输出: {out:.3f}")

    print("\n>> 模拟弱光刺激（输入 [0.1, 0.1]）")
    out, _ = s.处理([0.1, 0.1], 0.0)
    print(f"   反射输出: {s.反射输出[:4]}...")
    print(f"   高级输出: {out:.3f}")

    st = s.统计()
    print(f"\n>> 系统统计:")
    print(f"   经验单元: {st['经验单元']} 条")
    print(f"   反射激活率: {st['反射激活率']:.2f}")
    print(f"   高级神经元数: {st['高级神经元数']}")
    print(f"   低级神经元数: {st['低级神经元数']}")
    print(f"   低级神经元演化步数: {st['低级神经元演化步数']}")

    s.保存()
    print("✅ 状态已保存")
