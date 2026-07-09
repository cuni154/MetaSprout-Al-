# 语言学 v1 —— 历史音变预测
# 场景：已知部分拉丁语→法语的音变规则，预测新词的演变

import sys, os, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from 鳌鳌 import 共鸣空间, 概念核

class 语言记忆:
    def __init__(self, 容量=40):
        self.记忆库, self.容量 = [], 容量
    def 添加(self, 条目):
        if len(self.记忆库) >= self.容量: self.记忆库.pop(0)
        self.记忆库.append(条目)
    def 采样(self, 数量=3):
        if len(self.记忆库) <= 数量: return self.记忆库[:]
        return random.sample(self.记忆库, 数量)

# 拉丁语→法语 经典音变规则
# c[k] → [s] 在 e,i 前（软化）
# p,t,k 词尾丢失
# 短元音 a,e,i,o,u 在开音节中保留，闭音节变化
# -us → -∅ (消失）
# ct → [kt] → [t] (简化）

已知音变 = [
    ("ca","sa"),    # camera → chambre (c软化）
    ("ci","si"),    # civitas → cité
    ("pe","pi"),    # petra → pierre
    ("po","pu"),    # populus → peuple
    ("ta","tə"),    # talis → tel
    ("te","ti"),    # tenere → tenir
    ("ke","tʃ"),    # centum → cent
    ("ku","kɔ"),    # cultus → cult
    ("us","y"),     # manus → main (us消失，鼻化）
    ("um","ɔ̃"),     # forum → for
    ("am","am"),     # amare → aimer (保留）
    ("em","am"),     # emere → acheter (e→a)
    ("il","il"),     # ile → il
    ("el","ɛl"),    # ele → èle
    ("ct","t"),     # noctem → nuit (ct→t)
    ("pt","t"),     # captum → chef (pt→t)
    ("gn","ɲ"),     # signum → signe
    ("rs","ʁ"),     # persona → personne
]

测试音变 = [
    ("co","kɔ"),    # colorem → couleur (c在o前不软化）
    ("cu","ky"),    # cultus → culte
    ("ti","tsi"),   # rationem → raison (ti→tsi)
    ("to","tə"),    # totum → tout
    ("ec","ɛs"),    # sectam → scie (c在e前软化）
    ("ac","aʃ"),    # facere → faire
]

def 词到特征(拉丁音节, 法语音节):
    """将音变对转换为特征向量"""
    v = [0.0]*10
    # 特征0：拉丁首辅音类型
    c = 拉丁音节[0] if 拉丁音节 else ''
    v[0] = {"c":-0.5,"p":-0.3,"t":-0.1,"k":0.1,"s":0.3,"m":0.5}.get(c, 0)
    # 特征1：拉丁元音
    v[1] = {"a":-0.5,"e":-0.25,"i":0,"o":0.25,"u":0.5}.get(拉丁音节[-1] if 拉丁音节 else '', 0)
    # 特征2：法语首辅音类型
    cf = 法语音节[0] if 法语音节 else ''
    v[2] = {"s":-0.5,"p":-0.3,"t":-0.1,"k":0.1,"ʁ":0.3,"ɲ":0.5}.get(cf, 0)
    # 特征3：法语元音
    vf = 法语音节[-1] if 法语音节 else ''
    v[3] = {"a":-0.5,"ɛ":-0.25,"i":0,"ɔ":0.25,"u":0.5,"y":0.75}.get(vf, 0)
    # 特征4：是否保留原辅音
    v[4] = 1.0 if 拉丁音节[0] == 法语音节[0] else -1.0
    # 特征5：元音是否变化
    v[5] = 1.0 if 拉丁音节[-1] != 法语音节[-1] else -1.0
    # 特征6：音节长度比
    v[6] = max(-1, min(1, len(法语音节)/max(1,len(拉丁音节)) - 1))
    # 特征7：是否涉及鼻化
    v[7] = 1.0 if "ɔ̃" in 法语音节 or "ɛ̃" in 法语音节 else -1.0
    # 特征8：是否涉及软腭擦化（c→s/ʃ）
    v[8] = 1.0 if (拉丁音节.startswith("c") and 法语音节[0] in "sʃ") else -1.0
    # 特征9：是否丢失辅音
    v[9] = 1.0 if len(法语音节) < len(拉丁音节) else -1.0
    return v

def 音变到Δ(拉丁音节, 法语音节):
    """简化的"音变距离"：变化越大值越大"""
    变化数 = 0
    for a, b in zip(拉丁音节, 法语音节):
        if a != b: 变化数 += 1
    # 长度差也算
    变化数 += abs(len(拉丁音节) - len(法语音节))
    return float(变化数)

class 语言适配器:
    def __init__(self):
        self.空间 = 共鸣空间(输入维=10)
        self._初始化核()
        self.预测历史 = []
        self.误差历史 = []
        self.上次Δ = None
        self.海马体 = []
        self.皮层 = 语言记忆(容量=40)
        self.巩固间隔 = 4
        self.段计数 = 0

    def _初始化核(self):
        初始 = [{"d": 0.5}, {"d": 1.5}, {"d": 3.0}]
        for i in range(3):
            核 = 概念核()
            核.核向量 = [初始[i]["d"]] + [random.uniform(-0.1, 0.1) for _ in range(9)]
            核.方差 = 0.5; 核.强度 = 1.0; 核.概率权重 = 1.0/3; 核.标签 = f"段{i}"
            self.空间.概念库.append(核)

    def _判断段(self, Δ):
        if Δ <= 0.5: return 0   # 几乎不变
        elif Δ <= 2: return 1   # 中等变化
        else: return 2           # 大变化

    def 喂观测(self, 拉丁, 法语, 实际Δ=None):
        刺激 = 词到特征(拉丁, 法语)
        新段 = self._判断段(实际Δ) if 实际Δ is not None else 1
        self.段计数 += 1
        主导核 = next((k for k in self.空间.概念库 if k.标签 == f"段{新段}"), None)
        for 核 in self.空间.概念库:
            if 核.标签 == f"段{新段}":
                self.空间.处理(刺激, 目标=None)

        μ = 主导核.核向量 or [0.0]*10
        预测Δ = 实际Δ + μ[0] if 实际Δ is not None else μ[0]

        误差 = None
        if 实际Δ is not None and self.上次Δ is not None:
            误差 = abs(预测Δ - 实际Δ)
            self.误差历史.append(误差)
            步长 = 0.3
            目标_d = max(0.0, min(5.0, 实际Δ - self.上次Δ))
            主导核.核向量[0] += (目标_d - 主导核.核向量[0]) * 步长
            目标σ = max(0.2, min(1.0, 误差/3.0))
            主导核.方差 += (目标σ - 主导核.方差) * 0.3
            self.海马体.append({"Δ": 实际Δ, "误差": 误差, "段": 新段})
            if len(self.海马体) >= self.巩固间隔:
                self.海马体.sort(key=lambda m: m["误差"])
                self.皮层.添加(self.海马体[0])
                self.海马体.clear()

        self.上次Δ = 实际Δ
        self.预测历史.append({"拉丁": 拉丁, "法语": 法语, "实际Δ": 实际Δ, "预测Δ": 预测Δ, "误差": 误差, "段": 新段})
        return 预测Δ, 误差

    def 打印状态(self):
        print(f"  段计数: {self.段计数}")
        for i, 核 in enumerate(self.空间.概念库):
            μ = 核.核向量 or [0]*10
            print(f"  [{i}] {核.标签} μ=[{μ[0]:.3f}] σ={核.方差:.3f}")


def 主函数():
    print("="*60)
    print("  🗣 元芽 · 历史语言学音变预测 v1")
    print("  稀疏场景：18个已知音变 → 预测6个新音变")
    print("="*60)

    适配器 = 语言适配器()
    适配器.空间.设置任务上下文("历史语言学音变预测")

    print("\n📚 训练阶段（18个已知音变）")
    for 拉丁, 法语 in 已知音变:
        实际Δ = 音变到Δ(拉丁, 法语)
        适配器.喂观测(拉丁, 法语, 实际Δ)
        h = 适配器.预测历史[-1]
        err_s = f"{h['误差']:>5.2f}" if h['误差'] is not None else "   N/A"
        print(f"  {拉丁:>4} → {法语:>4}  实际Δ={实际Δ:.1f}  预测Δ={h['预测Δ']:>5.2f}  误差={err_s}")

    if 适配器.误差历史:
        print(f"\n  ✅ 训练平均误差: {sum(适配器.误差历史)/len(适配器.误差历史):.3f}")
    适配器.打印状态()

    print("\n🔮 预测阶段（6个新音变）")
    预测误差 = []
    for 拉丁, 法语 in 测试音变:
        实际Δ = 音变到Δ(拉丁, 法语)
        适配器.喂观测(拉丁, 法语, 实际Δ)
        h = 适配器.预测历史[-1]
        if h["误差"] is not None: 预测误差.append(h["误差"])
        err_s = f"{h['误差']:>5.2f}" if h['误差'] is not None else "   N/A"
        print(f"  {拉丁:>4} → {法语:>4}  实际Δ={实际Δ:.1f}  预测Δ={h['预测Δ']:>5.2f}  误差={err_s}")

    if 预测误差:
        print(f"\n  📈 预测平均误差: {sum(预测误差)/len(预测误差):.3f}")
        print(f"  📈 最大误差: {max(预测误差):.3f}")

    适配器.空间.保存("语言学预测_v1_状态.json")
    print(f"\n✅ 状态已保存")

if __name__ == "__main__":
    主函数()
