# 银河系 & 仙女星系轨道预测 v1
# 基于元芽引擎预测两大星系未来45亿年的相对运动

import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from 鳌鳌 import 共鸣空间, 概念核

# ===== 天文常数 =====
M31_DISTANCE = 2.537e6
M31_RADIAL_VEL = -110.0
M31_TANGENTIAL_VEL = 17.0
M31_MASS = 1.5e12
MW_MASS = 1.5e12
G = 4.3009e-3

class 轨道记忆:
    def __init__(self, 容量=50):
        self.记忆库, self.容量 = [], 容量
    def 添加(self, 条目):
        if len(self.记忆库) >= self.容量: self.记忆库.pop(0)
        self.记忆库.append(条目)
    def 采样(self, 数量=5):
        if len(self.记忆库) <= 数量: return self.记忆库[:]
        return random.sample(self.记忆库, 数量)

class 星系适配器:
    def __init__(self):
        self.空间 = 共鸣空间(输入维=10)
        self._初始化核()
        self.预测历史 = []
        self.误差历史 = []
        self.上次距离 = None
        self.上次径向速度 = None
        self.上次切向速度 = None
        self.上次相对角度 = None
        self.海马体 = []
        self.皮层 = 轨道记忆(容量=60)
        self.巩固间隔 = 5
        self.当前段 = 0
        self.段计数 = 0

    def _初始化核(self):
        初始μ = [
            {"dr": 0.5, "dtheta": 0.1},
            {"dr": -0.5, "dtheta": 0.3},
            {"dr": -1.0, "dtheta": 0.8},
        ]
        for i in range(3):
            核 = 概念核()
            核.核向量 = [初始μ[i]["dr"], 初始μ[i]["dtheta"]] + [random.uniform(-0.05, 0.05) for _ in range(8)]
            核.方差 = 0.5
            核.强度 = 1.0
            核.概率权重 = 1.0 / 3
            核.段编号 = i  # 动态添加属性
            self.空间.概念库.append(核)

    def 观测到刺激(self, 距离_ly, 径向速度_kms, 切向速度_kms, 相对角度_deg, 时间_Gyr):
        v = [0.0] * 10
        v[0] = max(-1, min(1, (距离_ly - 1e6) / 2e6))
        v[1] = max(-1, min(1, 径向速度_kms / 200.0))
        v[2] = max(-1, min(1, 切向速度_kms / 50.0))
        v[3] = max(-1, min(1, 相对角度_deg / 180.0))
        v[4] = max(-1, min(1, 时间_Gyr / 5.0))
        if self.上次距离 is not None:
            v[5] = max(-1, min(1, (距离_ly - self.上次距离) / 1e5))
        if self.上次径向速度 is not None:
            v[6] = max(-1, min(1, (径向速度_kms - self.上次径向速度) / 50.0))
        if self.上次切向速度 is not None:
            v[7] = max(-1, min(1, (切向速度_kms - self.上次切向速度) / 20.0))
        if self.上次相对角度 is not None:
            v[8] = max(-1, min(1, (相对角度_deg - self.上次相对角度) / 30.0))
        v[9] = self.当前段 / 2.0
        self.上次距离, self.上次径向速度 = 距离_ly, 径向速度_kms
        self.上次切向速度, self.上次相对角度 = 切向速度_kms, 相对角度_deg
        return v

    def _判断段(self, 距离_ly, 径向速度_kms):
        if 距离_ly > 1.5e6: return 0
        elif 距离_ly > 2e5: return 1
        else: return 2

    def 喂观测(self, 距离_ly, 径向速度_kms, 切向速度_kms, 相对角度_deg, 时间_Gyr, 实际经度=None, 实际纬度=None):
        刺激 = self.观测到刺激(距离_ly, 径向速度_kms, 切向速度_kms, 相对角度_deg, 时间_Gyr)
        新段 = self._判断段(距离_ly, 径向速度_kms)
        if 新段 != self.当前段: self.当前段 = 新段
        self.段计数 += 1

        主导核 = next((k for k in self.空间.概念库 if getattr(k, '段编号', None) == self.当前段), None)
        for 核 in self.空间.概念库:
            if getattr(核, '段编号', None) == self.当前段:
                self.空间.处理(刺激, 目标=None)

        μ = 主导核.核向量 or [0.0]*10
        预测_dr = μ[0] * 5e4
        预测_dtheta = μ[1] * 5.0

        误差 = None
        if self.上次距离 is not None:
            实际_dr = 距离_ly - self.上次距离
            实际_dtheta = 相对角度_deg - self.上次相对角度 if self.上次相对角度 else 0.0
            误差 = math.sqrt((预测_dr - 实际_dr)**2 + (预测_dtheta - 实际_dtheta)**2)
            self.误差历史.append(误差)

            步长 = 0.3 if self.当前段 == 2 else 0.2
            目标_dr = max(-1.0, min(1.0, 实际_dr / 5e4))
            目标_dtheta = max(-1.0, min(1.0, 实际_dtheta / 5.0))
            主导核.核向量[0] += (目标_dr - 主导核.核向量[0]) * 步长
            主导核.核向量[1] += (目标_dtheta - 主导核.核向量[1]) * 步长
            主导核.核向量[0] = max(-2.0, min(2.0, 主导核.核向量[0]))
            主导核.核向量[1] = max(-2.0, min(2.0, 主导核.核向量[1]))

            目标σ = max(0.2, min(1.0, 误差 / 1e4))
            主导核.方差 += (目标σ - 主导核.方差) * 0.3

            记忆 = {"dr": 实际_dr, "dt": 实际_dtheta, "误差": 误差, "段": self.当前段, "刺激": 刺激[:]}
            self.海马体.append(记忆)
            if len(self.海马体) >= self.巩固间隔:
                self._巩固()

        self.预测历史.append({
            "时间_Gyr": 时间_Gyr, "距离_ly": 距离_ly,
            "径向速度": 径向速度_kms, "切向速度": 切向速度_kms,
            "相对角度": 相对角度_deg,
            "预测_dr": 预测_dr, "预测_dtheta": 预测_dtheta,
            "误差": 误差, "段": self.当前段,
        })
        return {"预测_dr": 预测_dr, "预测_dtheta": 预测_dtheta, "误差": 误差}

    def _巩固(self):
        if not self.海马体: return
        self.海马体.sort(key=lambda m: m["误差"])
        for mem in self.海马体[:min(5, len(self.海马体))]:
            self.皮层.添加(mem)
        self.海马体.clear()
        for 核 in self.空间.概念库:
            段 = getattr(核, '段编号', None)
            样本 = self.皮层.采样(数量=5)
            if not 样本: continue
            avg_dr = sum(m["dr"] for m in 样本) / len(样本)
            avg_dt = sum(m["dt"] for m in 样本) / len(样本)
            目标_dr = max(-1.0, min(1.0, avg_dr / 5e4))
            目标_dt = max(-1.0, min(1.0, avg_dt / 5.0))
            核.核向量[0] += (目标_dr - 核.核向量[0]) * 0.1
            核.核向量[1] += (目标_dt - 核.核向量[1]) * 0.1

    def 打印状态(self):
        print(f"  当前段: {self.当前段}  段计数: {self.段计数}")
        for i, 核 in enumerate(self.空间.概念库):
            μ = 核.核向量 or [0]*10
            print(f"  [{i}] 段={getattr(核, '段编号', '?')} μ=[{μ[0]:.4f}, {μ[1]:.4f}] σ={核.方差:.3f}")


def 生成历史轨道(步数=50):
    random.seed(42)
    数据 = []
    距离 = 3.0e6
    径向速度 = -80.0
    切向速度 = 20.0
    角度 = 0.0
    t = -3.0
    for i in range(步数):
        r = 距离 / M31_DISTANCE
        引力因子 = 1.0 / (r**2 + 0.01)
        距离变化 = (径向速度 * 1e3 / 3e5) * 1e6 * 0.01
        距离 += 距离变化
        径向速度 += (-引力因子 * 50.0 + random.uniform(-5, 5)) * 0.1
        切向速度 += (引力因子 * 10.0 + random.uniform(-2, 2)) * 0.1
        角度 += 切向速度 * 0.01 + random.uniform(-0.5, 0.5)
        距离 = max(1e4, 距离)
        径向速度 = max(-300, min(50, 径向速度))
        切向速度 = max(0, min(80, 切向速度))
        角度 %= 360.0
        数据.append({
            "时间_Gyr": round(t + i * 0.06, 2),
            "距离_ly": round(距离, 0),
            "径向速度": round(径向速度, 1),
            "切向速度": round(切向速度, 1),
            "相对角度": round(角度, 1),
        })
    return 数据


def 生成未来轨道(步数=50):
    random.seed(2025)
    数据 = []
    距离 = 2.537e6
    径向速度 = -110.0
    切向速度 = 17.0
    角度 = 138.0
    t = 0.0
    for i in range(步数):
        r = 距离 / M31_DISTANCE
        引力因子 = 1.0 / (r**2 + 0.01)
        距离变化 = (径向速度 * 1e3 / 3e5) * 1e6 * 0.01
        距离 += 距离变化
        径向速度 += (-引力因子 * 60.0 + random.uniform(-3, 3)) * 0.1
        切向速度 += (引力因子 * 15.0 + random.uniform(-1, 1)) * 0.1
        角度 += 切向速度 * 0.008 + random.uniform(-0.3, 0.3)
        距离 = max(1e3, 距离)
        径向速度 = max(-400, min(100, 径向速度))
        切向速度 = max(0, min(100, 切向速度))
        角度 %= 360.0
        数据.append({
            "时间_Gyr": round(t + i * 0.1, 1),
            "距离_ly": round(距离, 0),
            "径向速度": round(径向速度, 1),
            "切向速度": round(切向速度, 1),
            "相对角度": round(角度, 1),
        })
    return 数据


def 主函数():
    print("=" * 60)
    print("  🌌 元芽 · 银河系 & 仙女星系轨道预测 v1")
    print("  基于引力动力学 + 三段核学习")
    print("=" * 60)

    print("\n📚 训练阶段：历史轨道数据（过去30亿年）")
    历史数据 = 生成历史轨道(步数=50)
    print(f"  数据量: {len(历史数据)} 步")

    适配器 = 星系适配器()
    适配器.空间.设置任务上下文("星系轨道预测")

    for 观测 in 历史数据:
        适配器.喂观测(
            距离_ly=观测["距离_ly"],
            径向速度_kms=观测["径向速度"],
            切向速度_kms=观测["切向速度"],
            相对角度_deg=观测["相对角度"],
            时间_Gyr=观测["时间_Gyr"],
        )

    if 适配器.误差历史:
        训练误差 = sum(适配器.误差历史) / len(适配器.误差历史)
        print(f"  ✅ 训练完成，平均误差: {训练误差:.0f} 光年/步")

    适配器.打印状态()

    print("\n🔮 预测阶段：未来50步（约50亿年）")
    未来数据 = 生成未来轨道(步数=50)

    print(f"\n  {'时间(Gyr)':>8} | {'距离(万ly)':>10} | {'径向速度':>8} | {'切向速度':>8} | {'段':>4}")
    print(f"  {'─'*60}")

    预测误差 = []
    for 观测 in 未来数据:
        result = 适配器.喂观测(
            距离_ly=观测["距离_ly"],
            径向速度_kms=观测["径向速度"],
            切向速度_kms=观测["切向速度"],
            相对角度_deg=观测["相对角度"],
            时间_Gyr=观测["时间_Gyr"],
        )
        if result["误差"] is not None:
            预测误差.append(result["误差"])

        h = 适配器.预测历史[-1]
        seg_name = ["远离期", "接近期", "碰撞期"][h["段"]]
        print(f"  {h['时间_Gyr']:>8.1f} | {h['距离_ly']/1e4:>10.1f} | {h['径向速度']:>8.1f} | {h['切向速度']:>8.1f} | {seg_name:>4}")

        if len(适配器.预测历史) % 10 == 0:
            print(f"\n  ── 第 {len(适配器.预测历史)} 步 ──")
            适配器.打印状态()
            print(f"\n  {'时间(Gyr)':>8} | {'距离(万ly)':>10} | {'径向速度':>8} | {'切向速度':>8} | {'段':>4}")
            print(f"  {'─'*60}")

    print(f"\n{'='*60}")
    print("  📊 预测汇总")
    print(f"{'='*60}")
    适配器.打印状态()

    if 预测误差:
        平均误差 = sum(预测误差) / len(预测误差)
        最大误差 = max(预测误差)
        print(f"\n  📈 平均预测误差: {平均误差:.0f} 光年/步")
        print(f"  📈 最大预测误差: {最大误差:.0f} 光年/步")

        for 段名, 范围 in [("远离期(0-20步)", (0,20)), ("接近期(20-35步)", (20,35)), ("碰撞期(35-50步)", (35,50))]:
            段数据 = [预测误差[i] for i in range(*范围) if i < len(预测误差)]
            if 段数据:
                print(f"  📈 {段名}: 平均={sum(段数据)/len(段数据):.0f} 最大={max(段数据):.0f}")

    if 适配器.预测历史:
        最后 = 适配器.预测历史[-1]
        print(f"\n  💥 预计碰撞时间: 约 {最后['时间_Gyr']:.1f} Gyr 后")
        print(f"  📍 碰撞时距离: {最后['距离_ly']/1e3:.0f} 千光年")

    适配器.空间.保存("星系轨道预测_v1_状态.json")
    print(f"\n✅ 状态已保存到 星系轨道预测_v1_状态.json")


if __name__ == "__main__":
    主函数()
