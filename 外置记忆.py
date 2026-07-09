"""
外置记忆系统 v1.0
海马体(短期) + 皮层(长期) + 消息队列(传递) + 转编器(翻译)
二进制存储 · 极速读写 · 注意力检索
"""

import mmap, struct, os, json, time, random
from pathlib import Path

# ============================================================
# 📋 二进制格式定义
# ============================================================
报头格式 = "!II"       # 写指针(4) + 总写入次数(4) = 8字节
记录头格式 = "!IIIf"   # 总长度(4) + 核ID(4) + 时间戳(4) + 强度(f=4) = 16字节
索引项格式 = "!IIIff"  # 核ID(4) + 偏移(4) + 长度(4) + 强度(f=4) + 时间戳(f=4) = 20字节
消息格式 = "!IIfI"     # 发送者(4) + 接收者(4) + 紧急度(f=4) + 时间戳(4) = 16字节 + 内容(112字节)

记录头大小 = struct.calcsize(记录头格式)   # 16
索引项大小 = struct.calcsize(索引项格式)   # 20
消息头大小 = struct.calcsize(消息格式)     # 16
消息固定大小 = 128  # 每条消息128字节
海马体容量 = 1024


class 海马体:
    """短期记忆：固定大小循环缓冲，O(1)写入"""
    
    def __init__(self, 路径="外置记忆/海马体.bin"):
        self.路径 = Path(路径)
        self.路径.parent.mkdir(parents=True, exist_ok=True)
        self.写指针 = 0
        self.总写入 = 0
        self.文件 = None
        self._打开()
    
    def _打开(self):
        if not self.路径.exists():
            with open(self.路径, "wb") as f:
                f.write(struct.pack(报头格式, 0, 0))
                f.write(b"\x00" * 记录头大小 * 海马体容量)
        self.文件 = open(self.路径, "r+b")
        self.文件.seek(0)
        self.写指针, self.总写入 = struct.unpack(报头格式, self.文件.read(8))
    
    def 写入(self, 核ID=0, 时间戳=0, 强度=0.5, 数据=b""):
        记录 = struct.pack(记录头格式, 记录头大小 + len(数据), 核ID, 时间戳, 强度) + 数据
        偏移 = 8 + self.写指针 * 记录头大小
        self.文件.seek(偏移)
        self.文件.write(记录)
        self.写指针 = (self.写指针 + 1) % 海马体容量
        self.总写入 += 1
        self.文件.seek(0)
        self.文件.write(struct.pack(报头格式, self.写指针, self.总写入))
        self.文件.flush()
    
    def 读取最近(self, 条数=10):
        self.文件.seek(0)
        头数据 = self.文件.read(8)
        写指针, 总写入 = struct.unpack(报头格式, 头数据)
        实际写指针 = 写指针
        实际总写入 = max(总写入, 写指针) if 写指针 > 总写入 and 总写入 < 海马体容量 else 总写入
        结果 = []
        读取条数 = min(条数, 海马体容量, max(实际总写入, 实际写指针))
        for i in range(读取条数):
            索引 = (实际写指针 - 1 - i) % 海马体容量
            self.文件.seek(8 + 索引 * 记录头大小)
            头数据 = self.文件.read(记录头大小)
            if len(头数据) == 记录头大小:
                总长, 核ID, 时间戳, 强度 = struct.unpack(记录头格式, 头数据)
                if 核ID != 0:
                    额外长 = max(0, 总长 - 记录头大小) if 总长 >= 记录头大小 else 0
                    额外 = self.文件.read(额外长) if 额外长 > 0 else b""
                    结果.append({"核ID": 核ID, "时间": 时间戳, "强度": 强度, "数据": 额外})
        return 结果
    
    def 关闭(self):
        if self.文件:
            self.文件.close()
    
    def __enter__(self):
        return self
    def __exit__(self, *a):
        self.关闭()


class 皮层:
    """长期记忆：索引mmap + 数据纯追加，永不修改"""
    
    def __init__(self, 路径="外置记忆/皮层"):
        self.路径 = Path(路径)
        self.路径.mkdir(parents=True, exist_ok=True)
        self.索引路径 = self.路径 / "索引.bin"
        self.数据路径 = self.路径 / "数据.bin"
        self.索引文件 = None
        self.数据文件 = None
        self.映射 = None
        self.总条数 = 0
        self._打开()
    
    def _打开(self):
        self.数据文件 = open(self.数据路径, "ab" if self.数据路径.exists() else "wb")
        if not self.索引路径.exists():
            with open(self.索引路径, "wb") as f:
                f.write(struct.pack("!I", 0))
                f.write(b"\x00" * 索引项大小 * 1024)
        self.索引文件 = open(self.索引路径, "r+b")
        self.映射 = mmap.mmap(self.索引文件.fileno(), 0, access=mmap.ACCESS_WRITE)
        self.总条数 = struct.unpack("!I", self.映射[:4])[0]
    
    def 写入(self, 核ID=0, 时间戳=0, 强度=0.5, 数据=b""):
        记录 = struct.pack(记录头格式, 记录头大小 + len(数据), 核ID, 时间戳, 强度) + 数据
        self.数据文件.write(记录)
        self.数据文件.flush()
        偏移 = self.数据路径.stat().st_size - len(记录)
        所需大小 = 4 + (self.总条数 + 1) * 索引项大小
        if len(self.映射) < 所需大小:
            self.映射.resize(所需大小 + 索引项大小 * 1024)
        索引项 = struct.pack(索引项格式, 核ID, 偏移, len(记录), 强度, float(时间戳))
        self.映射[4 + self.总条数 * 索引项大小:4 + (self.总条数 + 1) * 索引项大小] = 索引项
        self.总条数 += 1
        struct.pack_into("!I", self.映射, 0, self.总条数)
        self.映射.flush()
    
    def 按核检索(self, 核ID, 最多=10):
        结果 = []
        for i in range(self.总条数 - 1, -1, -1):
            偏移 = 4 + i * 索引项大小
            项 = struct.unpack(索引项格式, self.映射[偏移:偏移 + 索引项大小])
            if 项[0] == 核ID:
                结果.append({"核ID": 项[0], "数据偏移": int(项[1]), "长度": int(项[2]), "强度": 项[3], "时间": int(项[4])})
                if len(结果) >= 最多:
                    break
        with open(self.数据路径, "rb") as f:
            for r in 结果:
                f.seek(r["数据偏移"] + 记录头大小)
                r["数据"] = f.read(r["长度"] - 记录头大小)
        return 结果
    
    def 全部检索(self, 最多=10):
        结果 = []
        for i in range(self.总条数 - 1, -1, -1):
            偏移 = 4 + i * 索引项大小
            项 = struct.unpack(索引项格式, self.映射[偏移:偏移 + 索引项大小])
            结果.append({"核ID": 项[0], "数据偏移": int(项[1]), "长度": int(项[2]), "强度": 项[3], "时间": int(项[4])})
            if len(结果) >= 最多:
                break
        with open(self.数据路径, "rb") as f:
            for r in 结果:
                f.seek(r["数据偏移"] + 记录头大小)
                r["数据"] = f.read(r["长度"] - 记录头大小)
        return 结果
    
    def 按时间检索(self, 开始时间, 结束时间, 最多=50):
        结果 = []
        for i in range(self.总条数 - 1, -1, -1):
            偏移 = 4 + i * 索引项大小
            项 = struct.unpack(索引项格式, self.映射[偏移:偏移 + 索引项大小])
            if 开始时间 <= int(项[4]) <= 结束时间:
                结果.append({"核ID": 项[0], "数据偏移": int(项[1]), "长度": int(项[2]), "强度": 项[3], "时间": int(项[4])})
                if len(结果) >= 最多:
                    break
        with open(self.数据路径, "rb") as f:
            for r in 结果:
                f.seek(r["数据偏移"] + 记录头大小)
                r["数据"] = f.read(r["长度"] - 记录头大小)
        return 结果
    
    def 合并(self):
        """合并相似记忆，减少碎片"""
        pass  # 以后实现
    
    def 关闭(self):
        if self.映射:
            self.映射.flush()
            self.映射.close()
        if self.索引文件:
            self.索引文件.close()
        if self.数据文件:
            self.数据文件.close()
    
    def __enter__(self):
        return self
    def __exit__(self, *a):
        self.关闭()


class 消息队列:
    """信息传递：固定大小环形队列，mmap加速"""
    
    def __init__(self, 路径="外置记忆/消息队列.bin", 容量=4096):
        self.路径 = Path(路径)
        self.容量 = 容量
        self.路径.parent.mkdir(parents=True, exist_ok=True)
        self.文件 = None
        self.映射 = None
        self.写指针 = 0
        self.总发送 = 0
        self._打开()
    
    def _打开(self):
        if not self.路径.exists():
            with open(self.路径, "wb") as f:
                f.write(struct.pack("!II", 0, 0))  # 写指针, 总发送
                f.write(b"\x00" * 消息固定大小 * self.容量)
        self.文件 = open(self.路径, "r+b")
        size = os.path.getsize(self.路径)
        self.映射 = mmap.mmap(self.文件.fileno(), size, access=mmap.ACCESS_WRITE)
        self.写指针, self.总发送 = struct.unpack("!II", self.映射[:8])
    
    def 发送(self, 发送者=0, 接收者=0, 紧急度=0.5, 内容=b""):
        if len(内容) > 112:
            内容 = 内容[:112]
        内容 = 内容.ljust(112, b"\x00")
        消息 = struct.pack(消息格式, 发送者, 接收者, 紧急度, int(time.time())) + 内容
        偏移 = 8 + self.写指针 * 消息固定大小
        self.映射[偏移:偏移 + 消息固定大小] = 消息
        self.写指针 = (self.写指针 + 1) % self.容量
        self.总发送 += 1
        struct.pack_into("!II", self.映射, 0, self.写指针, self.总发送)
        self.映射.flush()
    
    def 接收(self, 接收者ID, 最多=10, 最小紧急度=0.0):
        """接收发给自己的消息"""
        结果 = []
        for i in range(self.容量):
            偏移 = 8 + i * 消息固定大小
            头 = self.映射[偏移:偏移 + 消息头大小]
            if len(头) == 消息头大小:
                发送者ID, 接收者ID_2, 紧急度, 时间戳 = struct.unpack(消息格式, 头)
                if 接收者ID_2 in (0, 接收者ID) and 紧急度 >= 最小紧急度 and 发送者ID != 0:
                    内容 = self.映射[偏移 + 消息头大小:偏移 + 消息固定大小]
                    内容 = 内容.rstrip(b"\x00")
                    结果.append({"发送者": 发送者ID, "紧急度": 紧急度, "时间": 时间戳, "内容": 内容})
                    if len(结果) >= 最多:
                        break
        return 结果
    
    def 广播(self, 发送者=0, 紧急度=0.3, 内容=b""):
        """向所有层广播消息"""
        self.发送(发送者, 0, 紧急度, 内容)
    
    def 清空(self):
        self.映射[8:] = b"\x00" * 消息固定大小 * self.容量
        struct.pack_into("!II", self.映射, 0, 0, 0)
        self.映射.flush()
    
    def 关闭(self):
        if self.映射:
            self.映射.flush()
            self.映射.close()
        if self.文件:
            self.文件.close()
    
    def __enter__(self):
        return self
    def __exit__(self, *a):
        self.关闭()


class 转编器:
    """信息转编：在向量/标签/二进制/字典之间翻译"""
    
    def __init__(self, 标签库=None):
        self.标签库 = 标签库 or {
            # 方向
            "上": [0.8, 0.0, 0.0, 0.0],
            "下": [-0.8, 0.0, 0.0, 0.0],
            "左": [0.0, -0.8, 0.0, 0.0],
            "右": [0.0, 0.8, 0.0, 0.0],
            "前": [0.6, 0.6, 0.0, 0.0],
            "后": [-0.6, -0.6, 0.0, 0.0],
            # 感觉
            "温暖": [0.5, 0.8, 0.0, 0.0],
            "寒冷": [-0.5, -0.8, 0.0, 0.0],
            "明亮": [0.0, 0.9, 0.3, 0.0],
            "黑暗": [0.0, -0.9, -0.3, 0.0],
            "安静": [0.0, 0.0, -0.5, 0.0],
            "吵闹": [0.0, 0.0, 0.8, 0.0],
            # 状态
            "上升": [0.3, 0.7, 0.0, 0.0],
            "下沉": [-0.3, -0.7, 0.0, 0.0],
            "漂浮": [0.0, 0.0, 0.5, 0.0],
            "稳定": [0.0, 0.0, -0.3, 0.5],
            # 情绪
            "开心": [0.6, 0.6, 0.3, 0.0],
            "难过": [-0.6, -0.4, -0.3, 0.5],
            "困惑": [0.0, 0.0, 0.0, 0.9],
            "好奇": [0.8, 0.3, 0.0, 0.6],
        }
    
    def 向量到标签(self, 向量):
        """找最近的标签"""
        if not 向量:
            return "未知"
        最近标签 = "未知"
        最近距离 = 999.0
        for 标签, 标签向量 in self.标签库.items():
            d = sum((a - b) ** 2 for a, b in zip(向量[:len(标签向量)], 标签向量[:len(向量)]))
            if d < 最近距离:
                最近距离 = d
                最近标签 = 标签
        if 最近距离 > 2.0:
            return "未知"
        return 最近标签
    
    def 标签到向量(self, 标签):
        return self.标签库.get(标签, [0.0] * 4)
    
    def 向量到描述(self, 向量):
        """向量 → 自然语言描述"""
        标签们 = []
        for 标签, 标签向量 in self.标签库.items():
            d = sum((a - b) ** 2 for a, b in zip(向量[:len(标签向量)], 标签向量[:len(向量)]))
            if d < 0.5:
                标签们.append(标签)
        if not 标签们:
            return f"一些东西在{向量[0]:.1f},{向量[1]:.1f}"
        if len(标签们) <= 2:
            return "、".join(标签们)
        return "、".join(标签们[:2]) + "…"
    
    def 二进制到字典(self, 二进制数据):
        if len(二进制数据) < 记录头大小:
            return None
        总长, 核ID, 时间戳, 强度 = struct.unpack(记录头格式, 二进制数据[:记录头大小])
        额外 = 二进制数据[记录头大小:] if len(二进制数据) > 记录头大小 else b""
        return {"核ID": 核ID, "时间": 时间戳, "强度": 强度, "数据": 额外}
    
    def 字典到二进制(self, 字典):
        数据 = 字典.get("数据", b"")
        if isinstance(数据, str):
            数据 = 数据.encode("utf-8")
        return struct.pack(记录头格式, 记录头大小 + len(数据),
                          字典.get("核ID", 0), 字典.get("时间", 0),
                          字典.get("强度", 0.5)) + 数据


class 外置记忆系统:
    """统一接口：元芽只跟这个说话"""
    
    def __init__(self, 根目录="外置记忆"):
        self.根目录 = Path(根目录)
        self.根目录.mkdir(parents=True, exist_ok=True)
        self.海马 = 海马体(str(self.根目录 / "海马体.bin"))
        self.皮层 = 皮层(str(self.根目录 / "皮层"))
        self.消息 = 消息队列(str(self.根目录 / "消息队列.bin"))
        self.转编 = 转编器()
        self.巩固计数 = 0
        self.标签索引 = {}  # 标签→[核ID列表]
        print("📦 外置记忆系统启动")
        # 加载持久化的标签索引
        标签路径 = self.根目录 / "标签索引.json"
        if 标签路径.exists():
            try:
                with open(标签路径, 'r', encoding='utf-8') as f:
                    self.标签索引 = json.load(f)
                print(f"📂 加载标签索引：{len(self.标签索引)}个")
            except:
                self.标签索引 = {}
    
    def 记(self, 核ID, 时间戳, 强度, 向量=None, 标签="", 数据=None):
        """通用记忆接口——自动决定存海马体"""
        二进制数据 = b""
        if 向量 is not None:
            二进制数据 = struct.pack(f"!{len(向量)}f", *向量)
        if 标签:
            标签数据 = 标签.encode("utf-8")
            二进制数据 += struct.pack(f"!I{len(标签数据)}s", len(标签数据), 标签数据)
        if 数据 is not None:
            if isinstance(数据, str):
                数据 = 数据.encode("utf-8")
            二进制数据 += 数据
        
        self.海马.写入(核ID, 时间戳, 强度, 二进制数据)
        
        if 标签:
            if 标签 not in self.标签索引:
                self.标签索引[标签] = []
            if 核ID not in self.标签索引[标签]:
                self.标签索引[标签].append(核ID)
    
    def 想(self, 核ID=None, 标签=None, 最多=5):
        """回忆——从海马体+皮层同时检索"""
        结果 = []
        
        if 核ID:
            结果 += self.海马.读取最近(最多)
            结果 += self.皮层.按核检索(核ID, 最多)
        elif 标签:
            核们 = self.标签索引.get(标签, [])
            for 核 in 核们:
                结果 += self.皮层.按核检索(核, 最多 // max(len(核们), 1))
        else:
            结果 += self.海马.读取最近(最多)
            结果 += self.皮层.全部检索(最多)
        
        # 去重+排序（最新的优先）
        已见 = set()
        去重后 = []
        for r in 结果:
            key = (r.get("核ID"), r.get("时间"))
            if key not in 已见:
                已见.add(key)
                去重后.append(r)
        return 去重后[:最多]
    
    def 说(self, 发送者=0, 接收者=0, 紧急度=0.3, 内容=""):
        """发消息"""
        if isinstance(内容, str):
            内容 = 内容.encode("utf-8")
        self.消息.发送(发送者, 接收者, 紧急度, 内容)
    
    def 听(self, 接收者ID, 最多=10, 最小紧急度=0.0):
        """收消息"""
        消息们 = self.消息.接收(接收者ID, 最多, 最小紧急度)
        for msg in 消息们:
            if isinstance(msg["内容"], bytes):
                try:
                    msg["内容"] = msg["内容"].decode("utf-8")
                except:
                    pass
        return 消息们
    
    def 翻译(self, 向量=None, 标签=None, 二进制=None, 字典=None):
        """统一转编接口"""
        if 向量 is not None:
            return self.转编.向量到描述(向量)
        if 标签 is not None:
            return self.转编.标签到向量(标签)
        if 二进制 is not None:
            return self.转编.二进制到字典(二进制)
        if 字典 is not None:
            return self.转编.字典到二进制(字典)
        return None
    
    def 巩固(self, 批大小=50):
        """海马体→皮层"""
        self.巩固计数 += 1
        短期们 = self.海马.读取最近(批大小)
        写入数 = 0
        for r in 短期们:
            if r.get("数据") and len(r["数据"]) > 0:
                self.皮层.写入(r["核ID"], r["时间"], r["强度"], r["数据"])
                写入数 += 1
        print(f"📦 巩固：{写入数}条 海马体→皮层")
    
    def 状态报告(self):
        return {
            "海马体": f"{self.海马.总写入}条 写指针={self.海马.写指针}",
            "皮层": f"{self.皮层.总条数}条",
            "消息队列": f"{self.消息.总发送}条已发送",
            "标签索引": f"{len(self.标签索引)}个标签",
        }
    
    def 关闭(self):
        # 持久化标签索引
        try:
            标签路径 = self.根目录 / "标签索引.json"
            with open(标签路径, 'w', encoding='utf-8') as f:
                json.dump(self.标签索引, f, ensure_ascii=False, indent=2)
        except:
            pass
        self.海马.关闭()
        self.皮层.关闭()
        self.消息.关闭()
        print("📦 外置记忆系统关闭")
    
    def __enter__(self):
        return self
    def __exit__(self, *a):
        self.关闭()
