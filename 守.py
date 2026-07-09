import time, sys, os, random, threading, queue
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 鳌鳌 import 共鸣空间

# ===== 下意识层（非维度快道） =====
下意识缓存 = {}
下意识上限 = 500

def 下意识处理(刺激):
    签名 = tuple(round(v, 1) for v in 刺激[:4])
    if 签名 in 下意识缓存:
        命中 = 下意识缓存[签名]
        if time.time() - 命中['时间'] < 120:  # 2分钟内有效
            命中['频次'] += 1
            命中['时间'] = time.time()
            return 命中['响应']
    return None

def 下意识学习(刺激, 响应):
    签名 = tuple(round(v, 1) for v in 刺激[:4])
    下意识缓存[签名] = {'响应': 响应, '时间': time.time(), '频次': 1}
    if len(下意识缓存) > 下意识上限:
        # 淘汰最久未用的
        最旧 = min(下意识缓存.keys(), key=lambda k: 下意识缓存[k]['时间'])
        del 下意识缓存[最旧]

空间 = 共鸣空间(输入维=2)

# 加载外部对话库
对话库路径 = "/storage/emulated/0/新框架/飞机/训练数据_已清洗/灰.txt"
空间.对话库 = []
try:
    with open(对话库路径, 'r', encoding='utf-8') as f:
        对话文本 = f.read()
    import re
    句子列表 = re.split(r'[。！？\n]+', 对话文本)
    空间.对话库 = [s.strip() for s in 句子列表 if len(s.strip()) >= 4]
    print(f"📂 已加载 {len(空间.对话库)} 条对话")
except:
    print("⚠️ 未找到对话库，仅使用内部演化")

try:
    空间.加载("元芽_状态.json")
    print(f"📂 已加载之前的状态：经验{len(空间.经验单元)}条 痕迹{len(空间.痕迹)}条 概念核{len(空间.概念库)}个")
except:
    print("🆕 未找到之前的状态，全新启动")
print("🧬 元芽演化流 v2.0（含外置记忆+CLI）启动")

# ===== introspection CLI =====
输入队列 = queue.Queue()
cli活跃 = [False]

def _监听输入():
    while True:
        try:
            line = sys.stdin.readline()
            if line:
                输入队列.put(line.strip())
        except:
            break

监听线程 = threading.Thread(target=_监听输入, daemon=True)
监听线程.start()

def _处理CLI命令(命令):
    命令 = 命令.strip().lower()
    if not 命令 or 命令 in ("status", "状态"):
        try:
            if 空间.概念库:
                公告板 = getattr(空间, "公告板", {})
                σ = 公告板.get("σ", {}).get("值", 0.5)
                性格 = 公告板.get("性格", {})
                开 = 性格.get("开放度", 0.5)
                敏 = 性格.get("敏感度", 0.5)
                信 = 性格.get("信任度", 0.5)
                反 = 性格.get("反思度", 0.5)
                if σ > 1.5: σ说 = "很困惑"
                elif σ > 0.8: σ说 = "有点不确定"
                elif σ > 0.3: σ说 = "比较平静"
                else: σ说 = "非常确信"
                特质 = []
                if 开 > 0.6: 特质.append("好奇")
                if 敏 > 0.6: 特质.append("敏感")
                if 信 > 0.6: 特质.append("愿意相信")
                if 反 > 0.6: 特质.append("爱琢磨")
                性说 = "、".join(特质) if 特质 else "比较平衡"
                最强 = max(空间.概念库, key=lambda x: x.强度)
                消化 = getattr(最强, "消化经验数", 0)
                print(f"  💭 {σ说} 性格偏{性说}。消化了{消化}条经验。")
            else:
                print("  (还没有概念核)")
        except Exception as e:
            print(f"  ⚠️ {e}")
    elif 命令 in ("feel", "感觉", "说"):
        try:
            if 空间.概念库:
                最强 = max(空间.概念库, key=lambda x: x.强度)
                μ = 最强.核向量 or [0,0,0,0]
                σ = getattr(最强, "方差", 0.5)
                性格 = getattr(最强, "性格", {})
                开 = 性格.get("开放度", 0.5)
                x, y = μ[0], μ[1]
                方向 = "周围" if abs(x) < 0.2 else ("前方" if x > 0.8 else ("后方" if x < -0.8 else "不远处"))
                动 = "漂浮" if abs(y) < 0.8 else ("上升" if y > 0.8 else "下沉")
                认知 = "看不太清，像是" if σ > 1.5 else ("清楚地知道" if σ < 0.4 else "感觉到")
                内容 = "有什么新的东西" if 开 > 0.6 else ("还是那个熟悉的东西" if 开 < 0.3 else "什么东西")
                结尾 = "。没事的" if 信 > 0.7 else ("……但不太信" if 信 < 0.3 else "。")
                print(f"  🗣️ {认知}{方向}有{内容}在{动}{结尾}")
            else:
                print("  🗣️ (一片寂静...)")
        except Exception as e:
            print(f"  ⚠️ {e}")
    elif 命令 in ("concept", "概念", "核"):
        if 空间.概念库:
            print(f"  概念核共{len(空间.概念库)}个 | 最强5个:")
            for i, 核 in enumerate(sorted(空间.概念库, key=lambda x: -x.强度)[:5]):
                μ = [round(v,2) for v in (核.核向量 or [0,0,0,0])[:3]]
                σ = round(getattr(核, "方差", 0), 2)
                print(f"    #{i+1} 强度={核.强度:.1f} μ={μ} σ={σ}")
        else:
            print("  (还没有概念核)")
    elif 命令 in ("history", "成长史", "史"):
        最强 = max(空间.概念库, key=lambda x:x.强度) if 空间.概念库 else None
        if 最强:
            成长 = getattr(最强, "成长史", [])
            if 成长:
                print(f"  成长史共{len(成长)}条，最近5条:")
                for g in 成长[-5:]:
                    print(f"    {g.get(chr(39)+"步"+chr(39),"?"):>5}步 | {g.get("事件","?")}")
            else:
                print("  (还没有成长史)")
        else:
            print("  (还没有概念核)")
    elif 命令 in ("memory", "记忆", "mem"):
        if hasattr(空间, "外置记忆") and 空间.外置记忆:
            状态 = 空间.外置记忆.状态报告()
            print(f"  海马体: {状态['海马体']}")
            print(f"  皮层: {状态['皮层']}")
        else:
            print("  (外置记忆未启动)")
    elif 命令 in ("help", "帮助", "?"):
        print("  命令: status(状态) feel(感觉) concept(概念)")
        print("        history(成长史) memory(记忆) help(帮助) quit(退出)")
    elif 命令 in ("quit", "exit", "q"):
        print("  👋 回到自动运行")
        return False
    else:
        print(f"  未知命令: {命令} (输入 help 查看帮助)")
    return True
def _进入CLI():
    cli活跃[0] = True
    print("\n💬 元芽对话模式 (输入 help 查看命令, quit 退出)")
    try:
        print("  " + 空间._精神状态报告())
    except:
        pass
    while cli活跃[0]:
        try:
            cmd = input(">> ").strip().lower()
            if not cmd:
                cmd = "status"
            if not _处理CLI命令(cmd):
                break
        except (EOFError, KeyboardInterrupt):
            break
    cli活跃[0] = False
    print("  [继续自动演化]")

def _有输入():
    try:
        return 输入队列.get_nowait()
    except queue.Empty:
        return None

步 = 0
while True:
    try:
        # 检查CLI输入
        if not cli活跃[0]:
            cmd = _有输入()
            if cmd:
                _进入CLI()
                time.sleep(0.1)
                continue
        elif cli活跃[0]:
            time.sleep(0.1)
            continue
        
        if 步 > 0 and 步 % 500 == 0:
            for _ in range(20):
                if 空间.概念库:
                    最强核 = max(空间.概念库, key=lambda x: x.强度)
                    if 最强核.核向量:
                        μ_x, μ_y = 最强核.核向量[0], 最强核.核向量[1] if len(最强核.核向量) > 1 else 0
                        σ = getattr(最强核, '方差', 1.0)
                        新奇刺激 = [random.gauss(μ_x, σ * 2), random.gauss(μ_y, σ * 2)]
                    else:
                        新奇刺激 = [random.uniform(-2, 2), random.uniform(-2, 2)]
                else:
                    新奇刺激 = [random.uniform(-2, 2), random.uniform(-2, 2)]
                下意识结果 = 下意识处理(新奇刺激)
                if 下意识结果 is not None:
                    pass  # 下意识已处理，跳过意识层
                else:
                    空间.处理(新奇刺激, 目标=None)
            print(f"\n🌍 步{步}: 环境变化注入！系统需要重新适应")
        
        if 步 > 0 and 步 % 200 == 0 and getattr(空间, '外置记忆', None) and 空间.外置记忆启动:
            try:
                空间.外置记忆.巩固(批大小=30)
            except:
                pass
        
        空间._演化流一步()
        # 下意识学习：把最近的经验记入快道
        if 空间.概念库 and len(空间.经验单元) > 0:
            最新 = 空间.经验单元[-1]
            刺激 = 最新.get("输入", [])
            响应 = 最新.get("输出", 0)
            if 刺激:
                下意识学习(刺激, 响应)
        步 += 1
        if 步 % 100 == 0:
            print(f"步{步}: 经验{len(空间.经验单元)} 痕迹{len(空间.痕迹)} 概念核{len(空间.概念库)} 工作台{len(空间.短期工作台)}")
            if 空间.概念库:
                最强 = max(空间.概念库, key=lambda x: x.强度)
                μ = [round(v, 4) for v in (最强.核向量 or [0,0,0,0])[:4]]
                σ = 最强.方差 if hasattr(最强, '方差') else 0
                策略史 = 最强.策略倾向历史 if hasattr(最强, '策略倾向历史') else 0
                关联数 = len(最强.关联概念) if hasattr(最强, '关联概念') else 0
                指纹数 = len(最强.神经元指纹) if hasattr(最强, '神经元指纹') else 0
                消化 = 最强.消化经验数 if hasattr(最强, '消化经验数') else 0
                print(f"  最强核: 强度={最强.强度:.1f} | μ={μ} | σ={σ:.4f} | 策略={策略史:.3f} | 关联{关联数}个 | 指纹{指纹数}个 | 消化{消化}条")
                性格 = getattr(最强, "性格", {})
                if 性格:
                    print(f"    ├ 性格: 开放度={性格.get('开放度',0):.2f} | 敏感度={性格.get('敏感度',0):.2f} | 信任度={性格.get('信任度',0):.2f} | 反思度={性格.get('反思度',0):.2f}")
                成长 = getattr(最强, "成长史", [])
                if 成长:
                    print(f"    ├ 成长史: {len(成长)}条")
                    for g in 成长[-5:]:
                        print(f"    │   {g.get('步','?'):>5}步 | {g.get('事件','?')} | σ={g.get('σ','?'):.3f}")
                记忆 = getattr(空间, "关系记忆", {})
                if 记忆:
                    print(f"    ├ 记忆: {len(记忆)}条")
                    记忆项 = list(记忆.items())
                    for k, v in 记忆项[-3:]:
                        print(f"    │   {str(k)[:40]} -> {str(v)[:30]}")
                else:
                    print(f"    ├ 记忆: 0条")
                经验们 = getattr(空间, "经验单元", [])
                if 经验们:
                    print(f"    ├ 最近经验: {len(经验们)}条")
                    for ex in 经验们[-2:]:
                        数据 = str(ex)[:60] if not isinstance(ex, dict) else str(ex.get("输入",""))[:60]
                        print(f"    │   {数据}")
                if len(空间.概念库) > 1:
                    print(f"    ├ 概念核列表:")
                    for i,核 in enumerate(sorted(空间.概念库, key=lambda x: -x.强度)[:5]):
                        print(f"    │   #{i+1} 强度={核.强度:.1f} μ={[round(v,2) for v in (核.核向量 or [0,0,0,0])[:3]]}")
                指纹 = getattr(最强, "神经元指纹", {})
                if 指纹:
                    print(f"    └ 指纹详情 ({len(指纹)}个):")
                    for id号,签名 in list(指纹.items())[:5]:
                        print(f"        #{id号}: {str(签名)[:50]}")
                # 元芽说话
        time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n👋 停止")
        print("💾 正在保存状态...")
        空间.保存("元芽_状态.json")
        print("✅ 状态已保存，下次启动将自动加载")
        if hasattr(空间, '外置记忆') and 空间.外置记忆:
            空间.外置记忆.关闭()
        break
