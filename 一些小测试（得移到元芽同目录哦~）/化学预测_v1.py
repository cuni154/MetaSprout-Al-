# 化学 v1 —— 反应焓变(ΔH)预测
# 输入：反应物/生成物的键能 → 预测反应焓变
# 稀疏场景：只给少数反应的数据，预测同类型其他反应

import sys, os, math, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from 鳌鳌 import 共鸣空间, 概念核

class 化学记忆:
    def __init__(self, 容量=40):
        self.记忆库, self.容量 = [], 容量
    def 添加(self, 条目):
        if len(self.记忆库) >= self.容量: self.记忆库.pop(0)
        self.记忆库.append(条目)
    def 采样(self, 数量=3):
        if len(self.记忆库) <= 数量: return self.记忆库[:]
        return random.sample(self.记忆库, 数量)

# 已知键能（kJ/mol）
键能 = {"C-H":413,"C-C":348,"C=C":614,"C≡C":839,"C-O":358,"C=O":799,"O-H":463,"O=O":498,"H-H":436,"C-N":305,"N-H":391,"N≡N":945}

def 计算真值焓变(反应物键, 生成物键):
    """ΔH = Σ(断键吸热) - Σ(成键放热)"""
    断键 = sum(键能[k] for k in 反应物键)
    成键 = sum(键能[k] for k in 生成物键)
    return 断键 - 成键

class 化学适配器:
    def __init__(self):
        self.空间 = 共鸣空间(输入维=12)
        self._初始化核()
        self.预测历史 = []
        self.误差历史 = []
        self.上次焓变 = None
        self.海马体 = []
        self.皮层 = 化学记忆(容量=40)
        self.巩固间隔 = 4
        self.段计数 = 0

    def _初始化核(self):
        初始 = [{"dh": -50}, {"dh": 0}, {"dh": 50}]
        for i in range(3):
            核 = 概念核()
            核.核向量 = [初始[i]["dh"]] + [random.uniform(-5, 5) for _ in range(11)]
            核.方差 = 0.5; 核.强度 = 1.0; 核.概率权重 = 1.0/3
            核.标签 = f"段{i}"
            self.空间.概念库.append(核)

    def 反应到刺激(self, 反应物键列表, 生成物键列表, 温度=298.0):
        v = [0.0]*12
        # 特征1：断键总数
        v[0] = max(-1, min(1, len(反应物键列表)/10 - 1))
        # 特征2：成键总数
        v[1] = max(-1, min(1, len(生成物键列表)/10 - 1))
        # 特征3：净键数变化
        v[2] = max(-1, min(1, (len(生成物键列表)-len(反应物键列表))/5))
        # 特征4：最强键（反应物）
        if 反应物键列表:
            v[3] = max(-1, min(1, max(键能[k] for k in 反应物键列表)/1000 - 0.5))
        # 特征5：最强键（生成物）
        if 生成物键列表:
            v[4] = max(-1, min(1, max(键能[k] for k in 生成物键列表)/1000 - 0.5))
        # 特征6：是否含C=C双键
        v[5] = 1.0 if "C=C" in 反应物键列表 else -1.0
        # 特征7：是否含N≡N三键
        v[6] = 1.0 if "N≡N" in 反应物键列表 else -1.0
        # 特征8：温度
        v[7] = max(-1, min(1, (温度-298)/200))
        # 特征9：平均键能（反应物）
        if 反应物键列表:
            v[8] = max(-1, min(1, sum(键能[k] for k in 反应物键列表)/len(反应物键列表)/600 - 0.5))
        # 特征10：键类型丰富度
        types_r = set(k[0] for k in 反应物键列表)
        v[9] = max(-1, min(1, len(types_r)/5 - 0.5))
        # 特征11-12：C和O的存在
        v[10] = 1.0 if any("C" in k for k in 反应物键列表) else -1.0
        v[11] = 1.0 if any("O" in k for k in 反应物键列表) else -1.0
        return v

    def _判断段(self, dh):
        if dh < -100: return 0   # 强放热
        elif dh < 100: return 1   # 接近平衡
        else: return 2            # 吸热

    def 喂观测(self, 反应物键, 生成物键, 实际焓变=None, 温度=298.0):
        刺激 = self.反应到刺激(反应物键, 生成物键, 温度)
        新段 = self._判断段(实际焓变) if 实际焓变 is not None else 1
        self.段计数 += 1

        主导核 = next((k for k in self.空间.概念库 if k.标签 == f"段{新段}"), None)
        for 核 in self.空间.概念库:
            if 核.标签 == f"段{新段}":
                self.空间.处理(刺激, 目标=None)

        μ = 主导核.核向量 or [0.0]*12
        预测焓变 = 实际焓变 + μ[0] if 实际焓变 is not None else μ[0]*100

        误差 = None
        if 实际焓变 is not None and self.上次焓变 is not None:
            误差 = abs(预测焓变 - 实际焓变)
            self.误差历史.append(误差)
            步长 = 0.3
            目标_dh = max(-200, min(200, 实际焓变 - self.上次焓变))
            主导核.核向量[0] += (目标_dh - 主导核.核向量[0]) * 步长
            目标σ = max(0.2, min(1.0, 误差/200))
            主导核.方差 += (目标σ - 主导核.方差) * 0.3
            self.海马体.append({"dh": 实际焓变, "误差": 误差, "段": 新段})
            if len(self.海马体) >= self.巩固间隔:
                self.海马体.sort(key=lambda m: m["误差"])
                self.皮层.添加(self.海马体[0])
                self.海马体.clear()

        self.上次焓变 = 实际焓变
        self.预测历史.append({"实际焓变": 实际焓变, "预测焓变": 预测焓变, "误差": 误差, "段": 新段})
        return 预测焓变, 误差

    def 打印状态(self):
        print(f"  段计数: {self.段计数}")
        for i, 核 in enumerate(self.空间.概念库):
            μ = 核.核向量 or [0]*12
            print(f"  [{i}] {核.标签} μ=[{μ[0]:.1f}] σ={核.方差:.3f}")


def 主函数():
    print("="*60)
    print("  ⚗ 元芽 · 化学焓变预测 v1")
    print("  稀疏数据场景：仅用6个反应训练，预测4个新反应")
    print("="*60)

    # 训练集（6个已知反应）
    训练集 = [
        {"name": "甲烷燃烧", "r": ["C-H"]*4+["O=O"]*2, "p": ["C=O"]*2+["O-H"]*4, "dh": -802},
        {"name": "氢气燃烧", "r": ["H-H"]+["O=O"], "p": ["O-H"]*2, "dh": -242},
        {"name": "氨合成", "r": ["N≡N"]+["H-H"]*3, "p": ["N-H"]*6, "dh": -92},
        {"name": "乙烯加氢", "r": ["C=C"]+["H-H"], "p": ["C-C"]+["C-H"]*2, "dh": -137},
        {"name": "水分解", "r": ["O-H"]*2, "p": ["O=O"]+["H-H"], "dh": +572},
        {"name": "甲醇合成", "r": ["C-O"]+["H-H"]*2, "p": ["C-H"]*3+["O-H"], "dh": -91},
    ]

    # 测试集（4个未见反应）
    测试集 = [
        {"name": "乙烷燃烧", "r": ["C-C"]+["C-H"]*6+["O=O"]*7, "p": ["C=O"]*4+["O-H"]*6, "dh": -1560},
        {"name": "氨分解", "r": ["N-H"]*6, "p": ["N≡N"]+["H-H"]*3, "dh": +92},
        {"name": "乙炔加氢(→乙烯)", "r": ["C≡C"]+["H-H"]*2, "p": ["C=C"]+["C-H"]*2, "dh": -175},
        {"name": "乙醇氧化", "r": ["C-C"]+["C-O"]+["O-H"]+["C-H"]*5, "p": ["C=O"]+["C-O"]+["O-H"]*2+["C-H"]*3, "dh": -327},
    ]

    适配器 = 化学适配器()
    适配器.空间.设置任务上下文("化学焓变预测")

    print("\n📚 训练阶段（6个反应）")
    for 反应 in 训练集:
        适配器.喂观测(反应["r"], 反应["p"], 实际焓变=反应["dh"])
        h = 适配器.预测历史[-1]
        err_str = f"{h['误差']:>6.1f}" if h['误差'] is not None else "  (首项)"
        print(f"  {反应['name']:>8}  实际ΔH={反应['dh']:>6}kJ/mol  预测ΔH={h['预测焓变']:>8.1f}  误差={err_str}")

    if 适配器.误差历史:
        print(f"  ✅ 训练平均误差: {sum(适配器.误差历史)/len(适配器.误差历史):.1f} kJ/mol")
    适配器.打印状态()

    print("\n🔮 预测阶段（4个新反应）")
    预测误差 = []
    for 反应 in 测试集:
        适配器.喂观测(反应["r"], 反应["p"], 实际焓变=反应["dh"])
        h = 适配器.预测历史[-1]
        if h["误差"] is not None:
            预测误差.append(h["误差"])
        print(f"  {反应['name']:>10}  实际ΔH={反应['dh']:>6}kJ/mol  预测ΔH={h['预测焓变']:>8.1f}  误差={h['误差']:>6.1f}")

    if 预测误差:
        print(f"\n  📈 预测平均误差: {sum(预测误差)/len(预测误差):.1f} kJ/mol")
        print(f"  📈 最大误差: {max(预测误差):.1f} kJ/mol")

    适配器.空间.保存("化学预测_v1_状态.json")
    print(f"\n✅ 状态已保存")

if __name__ == "__main__":
    主函数()
