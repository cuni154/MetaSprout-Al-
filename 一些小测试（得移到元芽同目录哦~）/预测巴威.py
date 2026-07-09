# 预测巴威_v4.1_修正.py
# 修正：反思函数变量名错误

import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 鳌鳌 import 共鸣空间, 概念核

class 台风适配器:
    def __init__(self):
        self.空间 = 共鸣空间(输入维=12)
        self.预测历史 = []
        self.误差历史 = []
        self.反思日志 = []
        self.路径核 = None
        self.气压核 = None
        self.风速核 = None
        self._初始化核()
        self.上次经度 = None
        self.上次纬度 = None
        self.上次气压 = None
        self.上次风速 = None
        self.误差累积 = 0.0
        self.反思次数 = 0
        self.路径偏差累积 = [0.0, 0.0]

    def _初始化核(self):
        核 = 概念核()
        核.核向量 = [0.0, 0.0] + [0.0]*10
        核.方差 = 1.0
        核.强度 = 1.0
        核.标签 = "路径核"
        self.路径核 = 核
        self.空间.概念库.append(核)
        
        核 = 概念核()
        核.核向量 = [0.0] + [0.0]*11
        核.方差 = 1.0
        核.强度 = 1.0
        核.标签 = "气压核"
        self.气压核 = 核
        self.空间.概念库.append(核)
        
        核 = 概念核()
        核.核向量 = [0.0] + [0.0]*11
        核.方差 = 1.0
        核.强度 = 1.0
        核.标签 = "风速核"
        self.风速核 = 核
        self.空间.概念库.append(核)

    def 气象数据到刺激(self, 观测):
        气压 = 观测.get("pressure", 1013.0)
        纬度 = 观测.get("lat", 20.0)
        海温 = 观测.get("sst", 28.0)
        风切变 = 观测.get("wind_shear", 5.0)
        湿度 = 观测.get("humidity", 70.0)
        风速 = 观测.get("wind_speed", 20.0)
        眼墙温度 = 观测.get("eye_temp", 26.0)
        深对流 = 观测.get("deep_convection", 0.5)
        垂直风切变 = 观测.get("vertical_shear", 5.0)
        海面高度异常 = 观测.get("ssh_anomaly", 0.0)

        v0 = max(-1.0, min(1.0, (1013.0 - 气压) / 50.0))
        v1 = max(-1.0, min(1.0, 纬度 / 25.0))
        v2 = max(-1.0, min(1.0, (海温 - 26.0) / 8.0))
        v3 = max(-1.0, min(1.0, 风切变 / 20.0))
        v4 = max(-1.0, min(1.0, (湿度 - 60.0) / 30.0))
        v5 = max(-1.0, min(1.0, (风速 - 15.0) / 30.0))
        v6 = max(-1.0, min(1.0, (眼墙温度 - 25.0) / 5.0))
        v7 = max(-1.0, min(1.0, (深对流 - 0.5) * 2.0))
        v8 = max(-1.0, min(1.0, 垂直风切变 / 15.0))
        v9 = max(-1.0, min(1.0, 海面高度异常 / 0.3))
        v10 = 0.0
        if self.上次气压 is not None:
            v10 = max(-1.0, min(1.0, (气压 - self.上次气压) / 5.0))
        v11 = 0.0
        self.上次气压 = 气压
        return [v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11]

    def 喂观测(self, 观测):
        刺激 = self.气象数据到刺激(观测)
        if self.上次经度 is not None:
            dlon = 观测["lon"] - self.上次经度
            dlat = 观测["lat"] - self.上次纬度
            核 = self.路径核
            核.核向量[0] += (max(-1.0, min(1.0, dlon * 2.0)) - 核.核向量[0]) * 0.3
            核.核向量[1] += (max(-1.0, min(1.0, dlat * 2.0)) - 核.核向量[1]) * 0.3
            核.方差 *= 0.95
            if 核.方差 < 0.15: 核.方差 = 0.15
            
            d压力 = (观测["pressure"] - self.上次气压)
            核 = self.气压核
            目标 = max(-1.0, min(1.0, d压力 / 10.0))
            核.核向量[0] += (目标 - 核.核向量[0]) * 0.3
            核.方差 *= 0.95
            if 核.方差 < 0.15: 核.方差 = 0.15
            
            if self.上次风速 is not None:
                d风速 = (观测["wind_speed"] - self.上次风速)
                核 = self.风速核
                目标 = max(-1.0, min(1.0, d风速 / 10.0))
                核.核向量[0] += (目标 - 核.核向量[0]) * 0.3
                核.方差 *= 0.95
                if 核.方差 < 0.15: 核.方差 = 0.15

        self.上次经度 = 观测["lon"]
        self.上次纬度 = 观测["lat"]
        self.上次气压 = 观测["pressure"]
        self.上次风速 = 观测["wind_speed"]
        self.预测历史.append(观测)

    def 预测下一步(self, 当前观测, 小时=6):
        核路径 = self.路径核
        lon_off = 核路径.核向量[0] * 0.5 * (小时 / 6)
        lat_off = 核路径.核向量[1] * 0.5 * (小时 / 6)
        预测经度 = 当前观测["lon"] + lon_off
        预测纬度 = 当前观测["lat"] + lat_off
        
        核气压 = self.气压核
        p_change = 核气压.核向量[0] * 5.0 * (小时 / 6)
        预测气压 = 当前观测["pressure"] + p_change
        
        核风速 = self.风速核
        w_change = 核风速.核向量[0] * 5.0 * (小时 / 6)
        预测风速 = 当前观测["wind_speed"] + w_change
        
        if 预测气压 < 870: 预测气压 = 870
        if 预测气压 > 1050: 预测气压 = 1050
        if 预测风速 < 0: 预测风速 = 0.0
        if 预测风速 > 80: 预测风速 = 80
        
        sigma = (核路径.方差 + 核气压.方差 + 核风速.方差) / 3
        uncertainty_km = 50 + sigma * 200
        
        return {
            "lon": round(预测经度, 2),
            "lat": round(预测纬度, 2),
            "pressure": round(预测气压, 1),
            "wind_speed": round(预测风速, 1),
            "uncertainty_km": round(uncertainty_km, 0),
            "sigma": round(sigma, 3),
            "hours": 小时
        }

    def 反思(self, 实际观测, 预测结果, 步长小时=6):
        """
        反思函数：比较预测和实际，调整核参数
        """
        预测经度 = 实际观测["lon"] + 预测结果.get("lon_offset", 0)
        预测纬度 = 实际观测["lat"] + 预测结果.get("lat_offset", 0)
        预测气压 = 预测结果.get("pressure", 实际观测["pressure"])
        预测风速 = 预测结果.get("wind_speed", 实际观测["wind_speed"])
        
        经度误差 = 实际观测["lon"] - 预测经度
        纬度误差 = 实际观测["lat"] - 预测纬度
        气压误差 = 实际观测["pressure"] - 预测气压
        风速误差 = 实际观测["wind_speed"] - 预测风速
        
        self.误差累积 += abs(经度误差) + abs(纬度误差) + abs(气压误差) + abs(风速误差)
        self.反思次数 += 1
        self.路径偏差累积[0] += 经度误差
        self.路径偏差累积[1] += 纬度误差
        
        # 修正：使用 实际观测 而不是 actual_观测
        日志条目 = {
            "时间": 实际观测.get("time", "未知"),
            "经度误差": round(经度误差, 3),
            "纬度误差": round(纬度误差, 3),
            "气压误差": round(气压误差, 1),
            "风速误差": round(风速误差, 1),
        }
        self.反思日志.append(日志条目)
        
        # 根据误差调整核
        if abs(经度误差) > 0.05 or abs(纬度误差) > 0.05:
            lon_目标 = max(-1.0, min(1.0, 经度误差 * 2.0 / (步长小时/6)))
            lat_目标 = max(-1.0, min(1.0, 纬度误差 * 2.0 / (步长小时/6)))
            self.路径核.核向量[0] += (lon_目标 * 0.3 - self.路径核.核向量[0]) * 0.2
            self.路径核.核向量[1] += (lat_目标 * 0.3 - self.路径核.核向量[1]) * 0.2
            self.路径核.方差 *= 1.05
            if self.路径核.方差 > 2.0: self.路径核.方差 = 2.0
        
        if abs(气压误差) > 1.0:
            目标 = max(-1.0, min(1.0, 气压误差 / 10.0))
            self.气压核.核向量[0] += (目标 * 0.3 - self.气压核.核向量[0]) * 0.2
            self.气压核.方差 *= 1.05
            if self.气压核.方差 > 2.0: self.气压核.方差 = 2.0
        
        if abs(风速误差) > 1.0:
            目标 = max(-1.0, min(1.0, 风速误差 / 10.0))
            self.风速核.核向量[0] += (目标 * 0.3 - self.风速核.核向量[0]) * 0.2
            self.风速核.方差 *= 1.05
            if self.风速核.方差 > 2.0: self.风速核.方差 = 2.0
        
        return {
            "经度误差": round(经度误差, 3),
            "纬度误差": round(纬度误差, 3),
            "气压误差": round(气压误差, 1),
            "风速误差": round(风速误差, 1)
        }

    def 反思报告(self):
        if self.反思次数 == 0:
            return "还没有进行过反思。"
        平均误差 = self.误差累积 / self.反思次数
        偏航_经度 = self.路径偏差累积[0] / self.反思次数
        偏航_纬度 = self.路径偏差累积[1] / self.反思次数
        return {
            "反思次数": self.反思次数,
            "平均累积误差": round(平均误差, 2),
            "偏航_经度": round(偏航_经度, 3),
            "偏航_纬度": round(偏航_纬度, 3),
            "最近5条日志": self.反思日志[-5:] if self.反思日志 else []
        }

    def 打印状态(self):
        print("\n  三核状态:")
        if self.路径核:
            μ = self.路径核.核向量
            print(f"    路径核: μ=[{μ[0]:.3f}, {μ[1]:.3f}] σ={self.路径核.方差:.3f}")
        if self.气压核:
            μ = self.气压核.核向量
            print(f"    气压核: μ=[{μ[0]:.3f}] σ={self.气压核.方差:.3f}")
        if self.风速核:
            μ = self.风速核.核向量
            print(f"    风速核: μ=[{μ[0]:.3f}] σ={self.风速核.方差:.3f}")
        print(f"  历史数据: {len(self.预测历史)} 条")


def 加载数据(文件路径):
    if not os.path.exists(文件路径):
        print(f"⚠️ 数据文件不存在: {文件路径}")
        return None
    with open(文件路径, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for d in data:
        d.setdefault("sst", 28.0)
        d.setdefault("wind_shear", 5.0)
        d.setdefault("humidity", 70.0)
        d.setdefault("eye_temp", 26.0)
        d.setdefault("deep_convection", 0.5)
        d.setdefault("vertical_shear", 5.0)
        d.setdefault("ssh_anomaly", 0.0)
    return data


def 主函数():
    print("=" * 60)
    print("  🌀 元芽 · 巴威台风路径预测 v4.1")
    print("  反思机制修正版")
    print("=" * 60)

    数据文件 = "巴威_历史路径.json"
    历史数据 = 加载数据(数据文件)
    if 历史数据 is None:
        print("⚠️ 未找到真实数据，生成模拟数据...")
        历史数据 = []
        lon, lat = 130.0, 18.3
        press, wind = 930, 55
        for i in range(15):
            lon -= random.uniform(0.2, 0.8)
            lat += random.uniform(0.2, 0.6)
            press += random.uniform(-3, 4)
            wind += random.uniform(-3, 2)
            历史数据.append({
                "lon": round(lon, 2),
                "lat": round(lat, 2),
                "pressure": round(press, 1),
                "wind_speed": round(wind, 1),
                "sst": 28.0,
                "wind_shear": 5.0,
                "humidity": 70.0,
                "time": f"2026-07-{(i+1):02d}T08:00:00"
            })
    else:
        print(f"✅ 已加载 {len(历史数据)} 条历史观测")

    适配器 = 台风适配器()
    print("\n🧬 阶段1：训练三核...")
    for 观测 in 历史数据[:8]:
        适配器.喂观测(观测)

    print("\n🧬 阶段2：预测 + 反思训练...")
    for i in range(8, len(历史数据) - 1):
        当前观测 = 历史数据[i]
        下一观测 = 历史数据[i+1]
        
        预测 = 适配器.预测下一步(当前观测, 小时=6)
        预测["lon_offset"] = 预测["lon"] - 当前观测["lon"]
        预测["lat_offset"] = 预测["lat"] - 当前观测["lat"]
        
        误差 = 适配器.反思(下一观测, 预测, 步长小时=6)
        
        print(f"   步{i}: 预测 {当前观测['lon']:.1f},{当前观测['lat']:.1f} → "
              f"实际 {下一观测['lon']:.1f},{下一观测['lat']:.1f} "
              f"误差: lon={误差['经度误差']:.3f} lat={误差['纬度误差']:.3f}")

    最新 = 历史数据[-1]
    print(f"\n📌 最新观测 (时间: {最新.get('time', '未知')})")
    print(f"   位置: {最新['lon']:.1f}°E, {最新['lat']:.1f}°N")
    print(f"   气压: {最新['pressure']:.1f} hPa")
    print(f"   风速: {最新['wind_speed']:.1f} m/s")

    适配器.打印状态()

    print("\n🔮 阶段3：最终预测未来路径（反思后）")
    print("  小时 |   经度(°E) |   纬度(°N) | 气压(hPa) | 风速(m/s) | 不确定(km)")
    print("  -----|------------|------------|-----------|-----------|-----------")
    for h in [12, 24, 36, 48, 72]:
        预测 = 适配器.预测下一步(最新, 小时=h)
        if 预测:
            print(f"  {h:4} | {预测['lon']:10.1f} | {预测['lat']:10.1f} | {预测['pressure']:9.1f} | {预测['wind_speed']:9.1f} | {预测['uncertainty_km']:9.0f}")

    print("\n🧠 反思报告:")
    报告 = 适配器.反思报告()
    if isinstance(报告, dict):
        print(f"   反思次数: {报告['反思次数']}")
        print(f"   平均累积误差: {报告['平均累积误差']}")
        print(f"   偏航(经度): {报告['偏航_经度']} (正=预测偏东)")
        print(f"   偏航(纬度): {报告['偏航_纬度']} (正=预测偏北)")
        if abs(报告['偏航_经度']) > 0.1 or abs(报告['偏航_纬度']) > 0.1:
            print("   ⚠️ 检测到系统性偏差，建议调整学习率或增加训练数据。")
    else:
        print(f"   {报告}")

    print("\n🌊 登陆强度估计（以72小时预测为准）:")
    预测72 = 适配器.预测下一步(最新, 小时=72)
    if 预测72:
        登陆风速 = 预测72["wind_speed"]
        登陆气压 = 预测72["pressure"]
        if 登陆风速 >= 52: 等级 = "超强台风"
        elif 登陆风速 >= 42: 等级 = "强台风"
        elif 登陆风速 >= 33: 等级 = "台风"
        elif 登陆风速 >= 25: 等级 = "强热带风暴"
        else: 等级 = "热带风暴"
        print(f"  预测72小时后位置: {预测72['lon']:.1f}°E, {预测72['lat']:.1f}°N")
        print(f"  估计气压: {登陆气压:.1f} hPa")
        print(f"  估计风速: {登陆风速:.1f} m/s")
        print(f"  对应等级: {等级}")

    适配器.空间.保存("巴威_预测状态_v4.1.json")
    print("\n✅ 预测完成，状态已保存至 巴威_预测状态_v4.1.json")


if __name__ == "__main__":
    主函数()