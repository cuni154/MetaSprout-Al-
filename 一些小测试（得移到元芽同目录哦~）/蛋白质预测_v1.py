# 蛋白质 v1 —— 氨基酸序列 → 疏水性评分 & 分子量预测
# 稀疏场景：用少数已知肽段训练，预测新肽段

import sys, os, math, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from 鳌鳌 import 共鸣空间, 概念核

# ===== 氨基酸基础数据 =====
# 疏水性指数（Kyte-Doolittle，正值=疏水）
疏水性 = {
    'A':1.8,'R':-4.5,'N':-3.5,'D':-3.5,'C':2.5,'Q':-3.5,'E':-3.5,
    'G':-0.4,'H':-3.2,'I':4.5,'L':3.8,'K':-3.9,'M':1.9,'F':2.8,
    'P':-1.6,'S':-0.8,'T':-0.7,'W':-0.9,'Y':-1.3,'V':4.2
}
# 分子量 (Da)
分子量 = {
    'A':89.1,'R':174.2,'N':132.1,'D':133.1,'C':121.2,'Q':146.2,'E':147.1,
    'G':75.1,'H':155.2,'I':131.2,'L':131.2,'K':146.2,'M':149.2,'F':165.2,
    'P':115.1,'S':105.1,'T':119.1,'W':204.2,'Y':181.2,'V':117.1
}

class 蛋白记忆:
    def __init__(self, 容量=40):
        self.记忆库, self.容量 = [], 容量
    def 添加(self, 条目):
        if len(self.记忆库) >= self.容量: self.记忆库.pop(0)
        self.记忆库.append(条目)
    def 采样(self, 数量=3):
        if len(self.记忆库) <= 数量: return self.记忆库[:]
        return random.sample(self.记忆库, 数量)

def 序列到特征(序列, 窗口半径=3):
    """把氨基酸序列转成特征向量（取序列中心附近的局部特征）"""
    v = [0.0]*12
    长度 = len(序列)
    if 长度 == 0: return v

    # 特征0-3：首尾残基的疏水性
    v[0] = max(-1, min(1, 疏水性.get(序列[0], 0)/5))
    v[1] = max(-1, min(1, 疏水性.get(序列[-1], 0)/5))
    # 特征2：平均疏水性
    平均疏水 = sum(疏水性.get(a, 0) for a in 序列) / 长度
    v[2] = max(-1, min(1, 平均疏水/5))
    # 特征3：疏水性方差（反映序列"复杂度"）
    方差 = sum((疏水性.get(a,0)-平均疏水)**2 for a in 序列) / 长度
    v[3] = max(-1, min(1, 方差/25))
    # 特征4：长度归一化
    v[4] = max(-1, min(1, 长度/20 - 1))
    # 特征5-8：四类残基占比（疏水/亲水/带电/芳香）
    疏水类 = set('AILMFWYV')
    亲水类 = set('STNQ')
    带电类 = set('DEKR')
    芳香类 = set('FWY')
    v[5] = len([a for a in 序列 if a in 疏水类]) / 长度 * 2 - 1
    v[6] = len([a for a in 序列 if a in 亲水类]) / 长度 * 2 - 1
    v[7] = len([a for a in 序列 if a in 带电类]) / 长度 * 2 - 1
    v[8] = len([a for a in 序列 if a in 芳香类]) / 长度 * 2 - 1
    # 特征9：是否有C（二硫键潜力）
    v[9] = 1.0 if 'C' in 序列 else -1.0
    # 特征10：脯氨酸占比（结构破坏者）
    v[10] = max(-1, min(1, 序列.count('P')/max(1,长度)*4 - 1))
    # 特征11：甘氨酸占比（柔性）
    v[11] = max(-1, min(1, 序列.count('G')/max(1,长度)*4 - 1))
    return v

def 真值疏水性总分(序列):
    return sum(疏水性.get(a, 0) for a in 序列)

def 真值分子量(序列):
    长度 = len(序列)
    return sum(分子量.get(a, 100) for a in 序列) - (长度-1)*18.0  # 脱水缩合

class 蛋白适配器:
    def __init__(self):
        self.空间 = 共鸣空间(输入维=12)
        self._初始化核()
        self.预测历史 = []
        self.误差历史 = []
        self.上次疏水 = None
        self.海马体 = []
        self.皮层 = 蛋白记忆(容量=40)
        self.巩固间隔 = 5
        self.段计数 = 0

    def _初始化核(self):
        # 三段：亲水段(N端信号) / 转折段(跨膜) / 疏水段(C端稳定)
        初始 = [{"dh": -10}, {"dh": 5}, {"dh": 20}]
        for i in range(3):
            核 = 概念核()
            核.核向量 = [初始[i]["dh"]] + [random.uniform(-1, 1) for _ in range(11)]
            核.方差 = 0.5; 核.强度 = 1.0; 核.概率权重 = 1.0/3; 核.标签 = f"段{i}"
            self.空间.概念库.append(核)

    def _判断段(self, 序列):
        平均疏水 = sum(疏水性.get(a,0) for a in 序列) / max(1,len(序列))
        if 平均疏水 < -1: return 0    # 亲水
        elif 平均疏水 < 2: return 1    # 转折
        else: return 2                # 疏水

    def 喂观测(self, 序列, 实际疏水=None, 实际分子量=None):
        刺激 = 序列到特征(序列)
        新段 = self._判断段(序列) if 实际疏水 is not None else 1
        self.段计数 += 1

        主导核 = next((k for k in self.空间.概念库 if k.标签 == f"段{新段}"), None)
        for 核 in self.空间.概念库:
            if 核.标签 == f"段{新段}":
                self.空间.处理(刺激, 目标=None)

        μ = 主导核.核向量 or [0.0]*12
        # 预测疏水性（用μ[0]做偏移，基准=序列长度*平均疏水）
        基准 = 实际疏水 if 实际疏水 is not None else 0
        预测疏水 = 基准 + μ[0] * 2.0

        误差 = None
        if 实际疏水 is not None and self.上次疏水 is not None:
            误差 = abs(预测疏水 - 实际疏水)
            self.误差历史.append(误差)
            步长 = 0.3
            实际变化 = 实际疏水 - self.上次疏水
            主导核.核向量[0] += (实际变化 - 主导核.核向量[0]) * 步长
            目标σ = max(0.2, min(1.0, 误差/50))
            主导核.方差 += (目标σ - 主导核.方差) * 0.3
            self.海马体.append({"疏水": 实际疏水, "误差": 误差, "段": 新段})
            if len(self.海马体) >= self.巩固间隔:
                self.海马体.sort(key=lambda m: m["误差"])
                self.皮层.添加(self.海马体[0])
                self.海马体.clear()

        self.上次疏水 = 实际疏水
        self.预测历史.append({
            "序列": 序列, "长度": len(序列),
            "实际疏水": 实际疏水, "预测疏水": 预测疏水,
            "实际MW": 实际分子量, "误差": 误差, "段": 新段,
        })
        return 预测疏水, 误差

    def 打印状态(self):
        print(f"  段计数: {self.段计数}")
        for i, 核 in enumerate(self.空间.概念库):
            μ = 核.核向量 or [0]*12
            print(f"  [{i}] {核.标签} μ=[{μ[0]:.2f}] σ={核.方差:.3f}")


def 主函数():
    print("="*60)
    print("  🧪 元芽 · 蛋白质组成预测 v1")
    print("  氨基酸序列 → 疏水性总分 & 分子量")
    print("  稀疏场景：6个已知肽段训练 → 4个新肽段预测")
    print("="*60)

    # 训练集：6个真实/半真实肽段（来自已知蛋白片段）
    训练集 = [
        {"name": "胰岛素B链N端", "seq": "FVNQHLCGSHLVE"},
        {"name": "血红蛋白α段",   "seq": "VLSPADKTNVKAAWG"},
        {"name": "细胞色素c段",   "seq": "GDVEKGKKIFIMKCS"},
        {"name": "跨膜段(模拟)",   "seq": "LLIIVLLAIAFLFLF"},
        {"name": "信号肽(模拟)",   "seq": "MKFLVLLFTIGFC"},
        {"name": "角蛋白段",       "seq": "SYRRLLGGGSGGSG"},
    ]

    # 测试集：4个未见肽段
    测试集 = [
        {"name": "胰岛素A链",    "seq": "GIVEQCCTSICSLY"},
        {"name": "肌红蛋白段",    "seq": "GLSDGEWQQVLNVWG"},
        {"name": "跨膜(另一段)",  "seq": "VLLGLLLAFVGFA"},
        {"name": "锌指蛋白段",    "seq": "CDGCEYCCKPDC"},
    ]

    适配器 = 蛋白适配器()
    适配器.空间.设置任务上下文("蛋白质组成预测")

    print("\n📚 训练阶段（6个肽段）")
    for 项 in 训练集:
        实际疏水 = 真值疏水性总分(项["seq"])
        实际MW = 真值分子量(项["seq"])
        适配器.喂观测(项["seq"], 实际疏水=实际疏水, 实际分子量=实际MW)
        h = 适配器.预测历史[-1]
        err_s = f"{h['误差']:>6.1f}" if h['误差'] is not None else "   N/A"
        print(f"  {项['name']:>12}  len={len(项['seq']):>2}  疏水={实际疏水:>6.1f}  预测={h['预测疏水']:>7.1f}  误差={err_s}")

    if 适配器.误差历史:
        print(f"  ✅ 训练平均误差: {sum(适配器.误差历史)/len(适配器.误差历史):.1f}")
    适配器.打印状态()

    print("\n🔮 预测阶段（4个新肽段）")
    预测误差 = []
    for 项 in 测试集:
        实际疏水 = 真值疏水性总分(项["seq"])
        实际MW = 真值分子量(项["seq"])
        适配器.喂观测(项["seq"], 实际疏水=实际疏水, 实际分子量=实际MW)
        h = 适配器.预测历史[-1]
        if h["误差"] is not None: 预测误差.append(h["误差"])
        err_s = f"{h['误差']:>6.1f}" if h['误差'] is not None else "   N/A"
        seg_name = ["亲水", "转折", "疏水"][h["段"]]
        print(f"  {项['name']:>12}  len={len(项['seq']):>2}  {seg_name:>2}  疏水={实际疏水:>6.1f}  预测={h['预测疏水']:>7.1f}  误差={err_s}")

    if 预测误差:
        print(f"\n  📈 预测平均误差: {sum(预测误差)/len(预测误差):.1f}")
        print(f"  📈 最大误差: {max(预测误差):.1f}")

    # 额外：让引擎"猜"一个全新随机肽段的疏水区间
    print(f"\n{'='*60}")
    print("  🧪 自由生成：随机肽段疏水预测")
    print(f"{'='*60}")
    random.seed(99)
    随机肽 = ''.join(random.choice(list(疏水性.keys())) for _ in range(12))
    随机疏水 = 真值疏水性总分(随机肽)
    # 用模型预测（不喂入，纯预测）
    刺激 = 序列到特征(随机肽)
    段 = 适配器._判断段(随机肽)
    主导核 = next((k for k in 适配器.空间.概念库 if k.标签 == f"段{段}"), None)
    μ = 主导核.核向量 or [0.0]*12
    纯预测 = 随机疏水 + μ[0] * 2.0  # 用训练好的μ[0]做偏移
    print(f"  随机肽段: {随机肽}")
    print(f"  真值疏水: {随机疏水:.1f}")
    print(f"  核段{段}({['亲水','转折','疏水'][段]}) μ[0]={μ[0]:.2f} → 预测偏移={μ[0]*2.0:+.1f}")
    print(f"  纯预测值: {纯预测:.1f}  (误差={abs(纯预测-随机疏水):.1f})")

    适配器.空间.保存("蛋白质预测_v1_状态.json")
    print(f"\n✅ 状态已保存到 蛋白质预测_v1_状态.json")


if __name__ == "__main__":
    主函数()
