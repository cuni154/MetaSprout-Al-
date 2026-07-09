# 经济学 v1 —— 股票价格趋势预测
# 稀疏场景：仅用少量历史数据预测未来走势

import sys, os, math, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from 鳌鳌 import 共鸣空间, 概念核

class 经济记忆:
    def __init__(self, 容量=50):
        self.记忆库, self.容量 = [], 容量
    def 添加(self, 条目):
        if len(self.记忆库) >= self.容量: self.记忆库.pop(0)
        self.记忆库.append(条目)
    def 采样(self, 数量=4):
        if len(self.记忆库) <= 数量: return self.记忆库[:]
        return random.sample(self.记忆库, 数量)

def 生成股价序列(天数=100, 起始价=100.0, 波动率=0.02, 趋势=0.001):
    """生成模拟股价（几何布朗运动 + 趋势）"""
    random.seed(42)
    prices = [起始价]
    for i in range(1, 天数):
        change = random.gauss(趋势, 波动率)
        prices.append(prices[-1] * (1 + change))
    return prices

def 计算特征(价格序列, idx, 趋势=0.0008, 窗口=5):
    """从价格序列中提取特征"""
    if idx < 窗口: return [0.0]*10
    v = [0.0]*10
    # 近期价格
    recent = 价格序列[max(0,idx-窗口):idx+1]
    # 特征0：5日均线斜率
    if len(recent) >= 2:
        v[0] = max(-1, min(1, (recent[-1]-recent[0])/(len(recent)*recent[0])*100))
    # 特征1：波动率（5日标准差/均值）
    if len(recent) >= 2:
        mean = sum(recent)/len(recent)
        std = math.sqrt(sum((x-mean)**2 for x in recent)/len(recent))
        v[1] = max(-1, min(1, std/mean * 10))
    # 特征2：当前价格相对位置（5日范围）
    if len(recent) >= 2:
        lo, hi = min(recent), max(recent)
        if hi > lo:
            v[2] = max(-1, min(1, (recent[-1]-lo)/(hi-lo)*2 - 1))
    # 特征3：距最高点的距离
    if len(recent) >= 2:
        v[3] = max(-1, min(1, (max(recent)-recent[-1])/recent[-1]*10))
    # 特征4：距最低点的距离
    if len(recent) >= 2:
        v[4] = max(-1, min(1, (recent[-1]-min(recent))/recent[-1]*10))
    # 特征5：价格变化加速度（2日 vs 5日）
    if idx >= 2:
        d1 = 价格序列[idx] - 价格序列[idx-1]
        d5 = 价格序列[idx] - 价格序列[max(0,idx-5)]
        v[5] = max(-1, min(1, (d1*5 - d5)/max(1,abs(d5))*10))
    # 特征6：相对起始价格的变化率
    v[6] = max(-1, min(1, (价格序列[idx]-价格序列[0])/价格序列[0]*5))
    # 特征7：日内范围（假设 high-low ≈ 2%）
    v[7] = max(-1, min(1, 0.015 * 50))
    # 特征8：天数（时间因子）
    v[8] = max(-1, min(1, idx/100.0))
    # 特征9：趋势方向（正/负）
    v[9] = 1.0 if 趋势 > 0 else -1.0
    return v

class 经济适配器:
    def __init__(self):
        self.空间 = 共鸣空间(输入维=10)
        self._初始化核()
        self.预测历史 = []
        self.误差历史 = []
        self.上次价格 = None
        self.上次变化 = None
        self.海马体 = []
        self.皮层 = 经济记忆(容量=50)
        self.巩固间隔 = 6
        self.段计数 = 0

    def _初始化核(self):
        初始 = [{"dp": 0.002}, {"dp": 0.0}, {"dp": -0.002}]
        for i in range(3):
            核 = 概念核()
            核.核向量 = [初始[i]["dp"]] + [random.uniform(-0.001, 0.001) for _ in range(9)]
            核.方差 = 0.3; 核.强度 = 1.0; 核.概率权重 = 1.0/3; 核.标签 = f"段{i}"
            self.空间.概念库.append(核)

    def _判断段(self, 价格变化率):
        if 价格变化率 > 0.005: return 0    # 上涨
        elif 价格变化率 < -0.005: return 2  # 下跌
        else: return 1                    # 震荡

    def 喂观测(self, 价格, 实际变化=None, 特征=None):
        if 特征 is None: 特征 = [0.0]*10
        新段 = self._判断段(实际变化) if 实际变化 is not None else 1
        self.段计数 += 1
        主导核 = next((k for k in self.空间.概念库 if k.标签 == f"段{新段}"), None)
        for 核 in self.空间.概念库:
            if 核.标签 == f"段{新段}":
                self.空间.处理(特征, 目标=None)

        μ = 主导核.核向量 or [0.0]*10
        预测变化 = 实际变化 + μ[0] if 实际变化 is not None else μ[0]

        误差 = None
        if 实际变化 is not None and self.上次变化 is not None:
            误差 = abs(预测变化 - 实际变化)
            self.误差历史.append(误差)
            步长 = 0.3
            目标_dp = max(-0.05, min(0.05, 实际变化 - self.上次变化))
            主导核.核向量[0] += (目标_dp - 主导核.核向量[0]) * 步长
            目标σ = max(0.1, min(0.5, 误差*50))
            主导核.方差 += (目标σ - 主导核.方差) * 0.3
            self.海马体.append({"dp": 实际变化, "误差": 误差, "段": 新段})
            if len(self.海马体) >= self.巩固间隔:
                self.海马体.sort(key=lambda m: m["误差"])
                self.皮层.添加(self.海马体[0])
                self.海马体.clear()

        self.上次变化 = 实际变化
        self.上次价格 = 价格
        self.预测历史.append({"价格": 价格, "实际变化": 实际变化, "预测变化": 预测变化, "误差": 误差, "段": 新段})
        return 预测变化, 误差

    def 打印状态(self):
        print(f"  段计数: {self.段计数}")
        for i, 核 in enumerate(self.空间.概念库):
            μ = 核.核向量 or [0]*10
            print(f"  [{i}] {核.标签} μ=[{μ[0]:.5f}] σ={核.方差:.4f}")


def 主函数():
    print("="*60)
    print("  💹 元芽 · 经济学股票趋势预测 v1")
    print("  稀疏场景：前30天训练 → 预测后70天")
    print("="*60)

    # 生成180天数据，但只暴露前30天给模型
    价格 = 生成股价序列(天数=100, 起始价=100.0, 波动率=0.015, 趋势=0.0008)

    适配器 = 经济适配器()
    适配器.空间.设置任务上下文("股票趋势预测")

    # 训练：前30天
    print("\n📚 训练阶段（前30天）")
    for i in range(30):
        if i == 0: continue
        变化 = (价格[i]-价格[i-1])/价格[i-1]
        特征 = 计算特征(价格, i, 趋势=0.0008)
        适配器.喂观测(价格[i], 实际变化=变化, 特征=特征)
        h = 适配器.预测历史[-1]
        if i <= 10 or i == 29:
            cls = "📈" if 变化 > 0 else "📉"
            print(f"  Day {i:>3}  价格={价格[i]:>7.2f}  变化={变化:>+.4f}  {cls}  误差={h['误差']}")

    if 适配器.误差历史:
        avg = sum(适配器.误差历史)/len(适配器.误差历史)
        print(f"\n  ✅ 训练平均误差: {avg:.5f}")

    # 预测：后70天（不提供实际变化，看预测方向是否正确）
    print("\n🔮 预测阶段（Day 30-99）")
    print(f"\n  {'Day':>4} | {'实际价格':>9} | {'预测变化':>10} | {'实际变化':>10} | {'方向正确?':>8}")
    print(f"  {'─'*55}")

    预测误差 = []
    for i in range(30, 100):
        特征 = 计算特征(价格, i, 趋势=0.0008)
        # 用模型预测（不传实际变化）
        预测变化, _ = 适配器.喂观测(价格[i], 实际变化=None, 特征=特征)
        # 但我们需要实际变化来计算误差
        实际变化 = (价格[i]-价格[i-1])/价格[i-1] if i > 0 else 0
        误差 = abs((预测变化 or 0) - 实际变化) if 预测变化 is not None else None
        if 误差 is not None: 预测误差.append(误差)

        # 方向判断
        预测方向 = "↑" if (预测变化 or 0) > 0 else "↓"
        实际方向 = "↑" if 实际变化 > 0 else "↓"
        正确 = "✅" if 预测方向 == 实际方向 else "❌"

        if i % 10 == 0 or i == 99:
            print(f"  {i:>4} | {价格[i]:>9.2f} | {预测变化:>+10.5f} | {实际变化:>+10.5f} | {正确}  {预测方向} vs {实际方向}")

    if 预测误差:
        print(f"\n  📈 预测平均误差: {sum(预测误差)/len(预测误差):.5f}")
        print(f"  📈 最大误差: {max(预测误差):.5f}")

    # 方向准确率
    if len(适配器.预测历史) > 30:
        预测方向数 = 0
        总 = 0
        for i in range(30, min(100, len(适配器.预测历史))):
            h = 适配器.预测历史[i]
            if h["预测变化"] is not None and h["实际变化"] is not None:
                预测方向 = 1 if h["预测变化"] > 0 else -1
                实际方向 = 1 if h["实际变化"] > 0 else -1
                if 预测方向 == 实际方向: 预测方向数 += 1
                总 += 1
        if 总 > 0:
            print(f"  📊 方向预测准确率: {预测方向数}/{总} = {预测方向数/总*100:.0f}%")

    适配器.打印状态()
    适配器.空间.保存("经济学预测_v1_状态.json")
    print(f"\n✅ 状态已保存")

if __name__ == "__main__":
    主函数()
