"""
Agent CLI 宣传视频生成器 v2
使用 Python + PIL + OpenCV + ffmpeg pipe 合成
素材来自 resources 目录
特性：流式写入 ffmpeg，无需将全部帧加载到内存
"""
import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import subprocess
import tempfile

# 修复 Windows 控制台 Unicode 编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# === 配置 ===
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(PROJECT_DIR, "resources")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
W, H = 1920, 1080
FPS = 30
BG_COLOR = (18, 20, 35)
ACCENT_COLOR = (80, 200, 255)
WHITE = (255, 255, 255)
GRAY = (200, 210, 225)

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "0"

# === 字体 ===
def get_font(size):
    for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
               "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"]:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()

FONT_LARGE = get_font(80)
FONT_MED = get_font(48)
FONT_SMALL = get_font(32)
FONT_TINY = get_font(24)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# === 工具函数 ===

def create_title_frame(text, subtitle="", accent_text=""):
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    # Logo icon
    bbox = draw.textbbox((0, 0), "[=]", font=FONT_LARGE)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, 60), "[=]", font=FONT_LARGE, fill=ACCENT_COLOR)
    # Main title
    font_title = get_font(120)
    bbox = draw.textbbox((0, 0), "Agent CLI", font=font_title)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, 200), "Agent CLI", font=font_title, fill=ACCENT_COLOR)
    # Text line
    bbox = draw.textbbox((0, 0), text, font=FONT_MED)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, 380), text, font=FONT_MED, fill=WHITE)
    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=FONT_SMALL)
        draw.text(((W - (bbox[2] - bbox[0])) // 2, 460), subtitle, font=FONT_SMALL, fill=GRAY)
    if accent_text:
        bbox = draw.textbbox((0, 0), accent_text, font=FONT_TINY)
        draw.text(((W - (bbox[2] - bbox[0])) // 2, 530), accent_text, font=FONT_TINY, fill=ACCENT_COLOR)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def create_text_slide(title, bullets, highlight_idx=-1):
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    title_text = "> " + title
    bbox = draw.textbbox((0, 0), title_text, font=FONT_LARGE)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, 80), title_text, font=FONT_LARGE, fill=ACCENT_COLOR)
    for i, bullet in enumerate(bullets):
        y = 280 + i * 65
        color = ACCENT_COLOR if i == highlight_idx else WHITE
        font = FONT_MED if i == highlight_idx else FONT_SMALL
        bullet_text = "-  " + bullet
        bbox = draw.textbbox((0, 0), bullet_text, font=font)
        draw.text(((W - (bbox[2] - bbox[0])) // 2, y), bullet_text, font=font, fill=color)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def create_cta_frame():
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    font_cta = get_font(100)
    bbox = draw.textbbox((0, 0), "[=] Agent CLI", font=font_cta)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, 200), "[=] Agent CLI", font=font_cta, fill=ACCENT_COLOR)
    lines = [
        "本地下载: github.com/luoaijun/agent-tool/releases",
        "在线体验: luoaijun.github.io/agent-tool",
        "",
        "支持 DeepSeek . 小米 MiMo . 自定义模型",
        "多模型并行 . 智能路由 . 本地语音",
    ]
    for i, line in enumerate(lines):
        color = GRAY if "支持" in line or "多模型" in line else WHITE
        size = FONT_TINY if ("支持" in line or "多模型" in line) else FONT_MED
        bbox = draw.textbbox((0, 0), line, font=size)
        draw.text(((W - (bbox[2] - bbox[0])) // 2, 400 + i * 55), line, font=size, fill=color)
    bbox = draw.textbbox((0, 0), "扫描二维码下载 | 微信小程序: 我和猫猫cli", font=FONT_TINY)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, 900), "扫描二维码下载 | 微信小程序: 我和猫猫cli",
              font=FONT_TINY, fill=GRAY)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def load_image_frame(path):
    img = cv2.imread(path)
    if img is None:
        return np.full((H, W, 3), BG_COLOR, dtype=np.uint8)
    ih, iw = img.shape[:2]
    scale = min(W / iw, H / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    canvas = np.full((H, W, 3), BG_COLOR, dtype=np.uint8)
    x = (W - nw) // 2
    y = (H - nh) // 2
    canvas[y:y+nh, x:x+nw] = resized
    return canvas


def load_video_frames(path, max_frames=300):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"  [警告] 无法打开视频: {path}")
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []
    count = 0
    while count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        fh, fw = frame.shape[:2]
        if fw != W or fh != H:
            scale = min(W / fw, H / fh)
            nw, nh = int(fw * scale), int(fh * scale)
            resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
            canvas = np.full((H, W, 3), BG_COLOR, dtype=np.uint8)
            x = (W - nw) // 2
            y = (H - nh) // 2
            canvas[y:y+nh, x:x+nw] = resized
            frame = canvas
        frames.append(frame)
        count += 1
    cap.release()
    if frames:
        print(f"  读取 {len(frames)} 帧 (原 {total}) 从 {os.path.basename(path)}")
    return frames


def add_label(frame, text):
    result = frame.copy()
    overlay = result.copy()
    cv2.rectangle(overlay, (0, 0), (W, 80), (0, 0, 0), -1)
    result = cv2.addWeighted(overlay, 0.6, result, 0.4, 0)
    pil_img = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    draw.text((30, 15), text, font=FONT_SMALL, fill=(255, 255, 255))
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


# === 流式视频生成器 ===

class VideoStreamer:
    """流式写入 ffmpeg pipe，不累积全部帧到内存"""

    def __init__(self, out_path, fps=FPS):
        self.out_path = out_path
        self.fps = fps
        self.proc = None
        self.count = 0

    def open(self):
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe, "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{W}x{H}",
            "-pix_fmt", "bgr24",
            "-r", str(self.fps),
            "-i", "-",
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            self.out_path
        ]
        stderr_log = os.path.join(tempfile.gettempdir(), "ffmpeg_encode.log")
        self._stderr_f = open(stderr_log, "w")
        self._stderr_path = stderr_log
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=self._stderr_f)
        self.count = 0

    def write_frame(self, frame):
        self.proc.stdin.write(frame.tobytes())
        self.count += 1

    def write_frames(self, frame, repeat):
        """写入同一帧 repeat 次"""
        data = frame.tobytes()
        for _ in range(repeat):
            self.proc.stdin.write(data)
            self.count += 1

    def close(self):
        if self.proc:
            self.proc.stdin.close()
            self.proc.wait()
            self._stderr_f.close()
            if self.proc.returncode != 0:
                with open(self._stderr_path, "r") as f:
                    err = f.read()
                print(f"  [错误] ffmpeg 返回码 {self.proc.returncode}:\n{err[:2000]}")
            else:
                print(f"  编码完成 ({self.count} 帧)")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()


# === 主流程 ===

def main():
    print("=" * 60)
    print("  Agent CLI 宣传视频生成器 v2 (流式)")
    print("=" * 60)

    out_path = os.path.join(OUTPUT_DIR, "agent-cli-promo-v2.mp4")
    vs = VideoStreamer(out_path)

    with vs:
        # ========== 片头 ==========
        print("\n[1/7] 生成片头...")
        opener = create_title_frame(
            "桌面 AI 多模型任务运行器",
            "支持 DeepSeek . 小米 MiMo . 自定义模型",
            "v0.8.19"
        )
        vs.write_frames(opener, 3 * FPS)  # 3 秒

        # ========== 核心功能亮点 (9项，分3组) ==========
        print("\n[2/7] 生成功能介绍...")
        features = [
            # ---- 核心能力 ----
            ("多模型并行", [
                "同时运行 DeepSeek + MiMo 等多个 AI 模型",
                "任务自动分解、并行执行、结果汇总",
                "每个模型发挥特长，效率倍增"
            ]),
            ("智能路由", [
                "自动识别任务类型，选择最佳模型",
                "推理任务 -> Pro模型 | 视觉任务 -> 视觉模型",
                "无需手动切换，AI自己知道谁更拿手"
            ]),
            ("工具调用 + Skill插件", [
                "读写文件、执行命令、搜索网络、操作代码",
                "Skill插件扩展，自定义AI能力边界",
                "定时调度任务，AI按时自动执行并通知"
            ]),
            # ---- 交互方式 ----
            ("本地语音 (实验性)", [
                "Windows原生语音引擎，无需联网即可使用",
                "语音输入 -> AI处理 -> 语音播报，完整闭环",
                "5秒停顿自动提交，持续优化中"
            ]),
            ("文件拖拽 + 视觉识别", [
                "拖入图片、PDF、代码文件，AI自动分析",
                "截图直接粘贴，多模态融合交互",
                "Markdown实时渲染 + 代码语法高亮"
            ]),
            ("项目管理 + 任务队列", [
                "多项目独立运行，上下文和记忆隔离",
                "任务排队执行，随时暂停/取消",
                "项目记忆持久化，重启后自动恢复上下文"
            ]),
            # ---- 独特卖点 ----
            ("微信小程序跨设备联动", [
                "微信搜索 '我和猫猫cli' 小程序，扫码登录",
                "手机端发起任务 -> 桌面AI执行 -> 结果推送回手机",
                "微信授权登录，无需记住复杂密码"
            ]),
            ("多模型池 + 自定义API", [
                "支持 DeepSeek / 小米MiMo / 自定义OpenAI兼容接口",
                "推理/视觉/快速三种角色，按需分配模型",
                "自带免费 DeepSeek Flash，开箱即用"
            ]),
            ("AI图片/海报生成", [
                "输入描述 -> AI自动生成图片、海报",
                "布偶猫、风景、设计稿... 随心所欲",
                "本视频即由Agent CLI自主编辑生成"
            ]),
        ]
        for title, bullets in features:
            frame = create_text_slide(title, bullets)
            vs.write_frames(frame, 3 * FPS)

        # ========== 截图展示 ==========
        print("\n[3/7] 生成截图展示...")
        screenshots = [
            ("1.png", "Agent CLI 主界面 - 多模型对话"),
            ("2.JPG", "文件拖拽 + Markdown 实时渲染"),
            ("3.JPG", "项目管理 + 任务队列"),
        ]
        for fname, label in screenshots:
            fpath = os.path.join(RESOURCES_DIR, fname)
            if os.path.exists(fpath):
                frame = load_image_frame(fpath)
                frame = add_label(frame, label)
                vs.write_frames(frame, 4 * FPS)
                print(f"  [OK] {fname}")
            else:
                print(f"  [!!] {fname} 不存在")

        # ========== 录屏展示 ==========
        print("\n[4/7] 生成录屏展示...")
        recordings = [
            ("录屏_20260615_152447.webm", "实操录屏 1 - Agent CLI 工作流"),
            ("录屏_20260615_154515.webm", "实操录屏 2 - Agent CLI 工作流"),
        ]
        for fname, label in recordings:
            fpath = os.path.join(RESOURCES_DIR, fname)
            if os.path.exists(fpath):
                frames = load_video_frames(fpath, max_frames=15 * FPS)
                if frames:
                    frames[0] = add_label(frames[0], label)
                    for f in frames:
                        vs.write_frame(f)
            else:
                print(f"  [!!] {fname} 不存在")

        # ========== 快速上手教程 ==========
        print("\n[5/7] 生成上手教程...")
        tutorial = [
            ("第1步: 配置 API Key", [
                "打开设置 -> 选择模型提供商 -> 填入 API Key",
                "支持 DeepSeek / 小米MiMo / 自定义接口",
                "自带免费 DeepSeek Flash，开箱即用"
            ]),
            ("第2步: 新建项目", [
                "点击左上角项目选择器 -> 新建项目",
                "每个项目独立上下文 + 持久化记忆",
                "多项目同时运行，任务互不干扰"
            ]),
            ("第3步: 发起任务", [
                "输入任务描述 -> AI自动路由最佳模型",
                "拖入图片/文件，AI自动分析内容",
                "点击麦克风按钮，开启语音对话"
            ]),
            ("第4步: 跨设备联动", [
                "微信搜小程序 '我和猫猫cli' -> 扫码登录",
                "手机发任务 -> 桌面执行 -> 结果推送回手机",
                "外出也能让AI干活，回来直接看结果"
            ]),
        ]
        for title, bullets in tutorial:
            frame = create_text_slide(title, bullets)
            vs.write_frames(frame, 3 * FPS)

        # ========== AI 生成展示 ==========
        print("\n[6/7] 生成 AI 生成展示...")

        frame = create_text_slide("AI 图片生成", [
            "输入描述 -> AI 自动生成图片",
            "布偶猫、风景、设计稿... 随心所欲"
        ])
        vs.write_frames(frame, 3 * FPS)

        # AI 图片生成结果
        fpath = os.path.join(RESOURCES_DIR, "cat-ragdoll.jpg")
        if os.path.exists(fpath):
            frame = load_image_frame(fpath)
            frame = add_label(frame, "[=] AI图片生成 - 布偶猫")
            vs.write_frames(frame, 5 * FPS)
            print(f"  [OK] cat-ragdoll.jpg")

        # AI 海报生成结果
        fpath = os.path.join(RESOURCES_DIR, "poster-ragdoll.jpg")
        if os.path.exists(fpath):
            frame = load_image_frame(fpath)
            frame = add_label(frame, "[=] AI海报生成 - 布偶猫")
            vs.write_frames(frame, 5 * FPS)
            print(f"  [OK] poster-ragdoll.jpg")

        # 海报生成录屏
        fpath = os.path.join(RESOURCES_DIR, "海报生成.webm")
        if os.path.exists(fpath):
            frames = load_video_frames(fpath, max_frames=15 * FPS)
            if frames:
                frames[0] = add_label(frames[0], "[=] AI海报生成过程 - 实操录屏")
                for f in frames:
                    vs.write_frame(f)
        else:
            print(f"  [!!] 海报生成.webm 不存在")

        # 自生成标注
        note = create_text_slide("关于本视频", [
            "本视频由 Agent CLI 自主编辑生成",
            "综合 Python + PIL + OpenCV + ffmpeg 工具链",
            "所有素材来自本地 resources 文件夹"
        ])
        vs.write_frames(note, 2 * FPS)

        # ========== 片尾 CTA ==========
        print("\n[7/7] 生成片尾...")
        cta = create_cta_frame()
        vs.write_frames(cta, 6 * FPS)

    # 完成
    print(f"\n{'='*60}")
    print(f"  总帧数: {vs.count} | 时长: {vs.count/FPS:.1f}秒")
    print(f"\n  完成! 视频位于: {out_path}")
    print(f"  文件大小: {os.path.getsize(out_path) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
