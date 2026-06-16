"""
Agent CLI 宣传视频生成器
使用 Python + PIL + OpenCV + imageio 合成
素材来自 resources 目录
"""
import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import imageio.v3 as iio
import subprocess
import tempfile

# 修复 Windows 控制台 Unicode 编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# === 配置 ===
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(PROJECT_DIR, "resources")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
W, H = 1920, 1080  # 输出分辨率
FPS = 30
BG_COLOR = (26, 26, 46)  # 深色背景 #1a1a2e
ACCENT_COLOR = (99, 179, 237)  # 蓝色 #63b3ed
WHITE = (255, 255, 255)
GRAY = (160, 170, 190)

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
    """创建标题页面帧 (PIL -> OpenCV)"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Logo 闪电图标
    draw.text((100, 60), "\u26a1", font=FONT_LARGE, fill=ACCENT_COLOR)

    # Agent CLI
    draw.text((100, 200), "Agent CLI", font=get_font(120), fill=ACCENT_COLOR)

    # 副标题
    draw.text((100, 380), text, font=FONT_MED, fill=WHITE)

    if subtitle:
        draw.text((100, 460), subtitle, font=FONT_SMALL, fill=GRAY)

    if accent_text:
        draw.text((100, 530), accent_text, font=FONT_TINY, fill=ACCENT_COLOR)

    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def create_text_slide(title, bullets, highlight_idx=-1):
    """创建文字幻灯片"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw.text((100, 80), "\u26a1  " + title, font=FONT_LARGE, fill=ACCENT_COLOR)

    for i, bullet in enumerate(bullets):
        y = 280 + i * 65
        color = ACCENT_COLOR if i == highlight_idx else WHITE
        draw.text((120, y), "\u2022  " + bullet, font=FONT_MED if i == highlight_idx else FONT_SMALL, fill=color)

    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def create_cta_frame():
    """片尾 CTA"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw.text((100, 200), "\u26a1 Agent CLI", font=get_font(100), fill=ACCENT_COLOR)

    lines = [
        "\u672c\u5730\u4e0b\u8f7d: github.com/luoaijun/agent-tool/releases",
        "\u5728\u7ebf\u4f53\u9a8c: luoaijun.github.io/agent-tool",
        "",
        "\u652f\u6301 DeepSeek \u00b7 \u5c0f\u7c73 MiMo \u00b7 \u81ea\u5b9a\u4e49\u6a21\u578b",
        "\u591a\u6a21\u578b\u5e76\u884c \u00b7 \u667a\u80fd\u8def\u7531 \u00b7 \u672c\u5730\u8bed\u97f3",
    ]
    for i, line in enumerate(lines):
        color = GRAY if line.startswith("\u652f\u6301") or line.startswith("\u591a\u6a21") else WHITE
        size = FONT_TINY if (line.startswith("\u652f\u6301") or line.startswith("\u591a\u6a21")) else FONT_MED
        draw.text((100, 400 + i * 55), line, font=size, fill=color)

    # 底部
    draw.text((100, 900), "\u626b\u63cf\u4e8c\u7ef4\u7801\u4e0b\u8f7d | \u5fae\u4fe1\u5c0f\u7a0b\u5e8f: \u6211\u548c\u732b\u732bcli",
              font=FONT_TINY, fill=GRAY)

    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def load_image_frame(path):
    """加载图片并适配 1920x1080（pillarbox/letterbox）"""
    img = cv2.imread(path)
    if img is None:
        return np.full((H, W, 3), BG_COLOR, dtype=np.uint8)
    ih, iw = img.shape[:2]
    scale = min(W / iw, H / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    canvas = np.full((H, W, 3), BG_COLOR, dtype=np.uint8)
    x, y = (W - nw) // 2, (H - nh) // 2
    canvas[y:y+nh, x:x+nw] = resized
    return canvas


def add_label(frame, text):
    """在底部添加标题栏（使用 PIL 以支持中文和 emoji）"""
    h, w = frame.shape[:2]
    # 用 PIL 画半透明底栏 + 文字
    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    overlay = Image.new("RGBA", (w, 80), (0, 0, 0, 180))
    pil_img.paste(overlay, (0, h - 80), overlay)
    draw = ImageDraw.Draw(pil_img)
    # 清理 emoji 变体选择器，让 PIL 尽量渲染
    clean_text = text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    draw.text((40, h - 60), clean_text, font=FONT_SMALL, fill=ACCENT_COLOR)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def load_video_frames(path, max_frames=None, target_fps=FPS):
    """使用 imageio 读取视频帧"""
    try:
        reader = iio.imiter(path, plugin="pyav")
        fps = iio.immeta(path, plugin="pyav").get("fps", 30)
    except Exception:
        try:
            reader = iio.imiter(path)
            fps = iio.immeta(path).get("fps", 30)
        except Exception as e:
            print(f"  \u26a0\ufe0f \u65e0\u6cd5\u8bfb\u53d6 {os.path.basename(path)}: {e}")
            return []

    frames = []
    step = max(1, int(fps / target_fps)) if fps > target_fps else 1

    for i, frame in enumerate(reader):
        if max_frames and len(frames) >= max_frames:
            break
        if i % step != 0:
            continue
        # 转为 BGR (OpenCV 格式)
        if frame.shape[-1] == 3:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            frame_bgr = frame
        # 适配 1920x1080
        fh, fw = frame_bgr.shape[:2]
        scale = min(W / fw, H / fh)
        nw, nh = int(fw * scale), int(fh * scale)
        resized = cv2.resize(frame_bgr, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((H, W, 3), BG_COLOR, dtype=np.uint8)
        x, y = (W - nw) // 2, (H - nh) // 2
        canvas[y:y+nh, x:x+nw] = resized
        frames.append(canvas)

    print(f"  读取 {len(frames)} \u5e27 (原 {i+1}) \u4ece {os.path.basename(path)}")
    return frames


def dissolve(prev, next_frame, progress):
    """Crossfade 过渡"""
    return cv2.addWeighted(prev, 1 - progress, next_frame, progress, 0)


def write_video(frames, out_path, skip_final_transition=False):
    """写入 MP4 视频"""
    if not frames:
        return
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用内置 MPEG-4 编码，无需外部库
    writer = cv2.VideoWriter(out_path, fourcc, FPS, (W, H))
    for f in frames:
        writer.write(f)
    writer.release()
    print(f"\n\u2705 \u89c6\u9891\u5df2\u4fdd\u5b58: {out_path}")


# === 主流程 ===

def main():
    print("=" * 60)
    print("  Agent CLI \u5ba3\u4f20\u89c6\u9891\u751f\u6210\u5668")
    print("=" * 60)

    all_frames = []

    # ========== 片头 ==========
    print("\n\ud83c\udfac \u751f\u6210\u7247\u5934...")
    opener = create_title_frame(
        "\u684c\u9762 AI \u591a\u6a21\u578b\u4efb\u52a1\u8fd0\u884c\u5668",
        "\u652f\u6301 DeepSeek \u00b7 \u5c0f\u7c73 MiMo \u00b7 \u81ea\u5b9a\u4e49\u6a21\u578b",
        "v0.8.19"
    )
    all_frames.extend([opener] * (3 * FPS))  # 3 秒

    # ========== 核心功能亮点（快速轮播） ==========
    print("\n\ud83c\udfaf \u751f\u6210\u529f\u80fd\u4ecb\u7ecd...")
    features = [
        ("\u591a\u6a21\u578b\u5e76\u884c", [
            "\u540c\u65f6\u8fd0\u884c DeepSeek + MiMo \u7b49\u591a\u4e2a AI \u6a21\u578b",
            "\u4efb\u52a1\u81ea\u52a8\u5206\u89e3\u3001\u5e76\u884c\u6267\u884c\u3001\u7ed3\u679c\u6c47\u603b",
            "\u6bcf\u4e2a\u6a21\u578b\u53d1\u6325\u7279\u957f\uff0c\u6548\u7387\u500d\u589e"
        ]),
        ("\u667a\u80fd\u8def\u7531", [
            "\u81ea\u52a8\u8bc6\u522b\u4efb\u52a1\u7c7b\u578b\uff0c\u9009\u62e9\u6700\u4f73\u6a21\u578b",
            "\u63a8\u7406\u4efb\u52a1 \u2192 Pro \u6a21\u578b | \u89c6\u89c9\u4efb\u52a1 \u2192 \u89c6\u89c9\u6a21\u578b",
            "\u65e0\u9700\u624b\u52a8\u5207\u6362\uff0cAI \u81ea\u5df1\u77e5\u9053\u8c01\u66f4\u62ff\u624b"
        ]),
        ("\u672c\u5730\u8bed\u97f3", [
            "Windows \u539f\u751f\u8bed\u97f3\u5f15\u64ce\uff0c\u65e0\u9700\u8054\u7f51",
            "\u8bed\u97f3\u8f93\u5165 \u2192 AI \u5904\u7406 \u2192 \u8bed\u97f3\u64ad\u62a5",
            "\u6301\u7eed\u4f18\u5316\u4e2d\uff0c\u66f4\u81ea\u7136\u7684\u4ea4\u4e92\u65b9\u5f0f"
        ]),
        ("\u5de5\u5177\u8c03\u7528 + \u63d2\u4ef6", [
            "AI \u53ef\u76f4\u63a5\u8bfb\u5199\u6587\u4ef6\u3001\u6267\u884c\u547d\u4ee4\u3001\u641c\u7d22\u7f51\u7edc",
            "Skill \u63d2\u4ef6\u6269\u5c55\uff0c\u81ea\u5b9a\u4e49 AI \u80fd\u529b\u8fb9\u754c",
            "\u5fae\u4fe1\u5c0f\u7a0b\u5e8f\u6388\u6743\uff0c\u4efb\u52a1\u63a8\u9001\u81f3\u624b\u673a\u5ba1\u6279"
        ]),
    ]
    for title, bullets in features:
        frame = create_text_slide(title, bullets)
        all_frames.extend([frame] * (3 * FPS))  # 每页 3 秒

    # ========== 截图展示（带标签和过渡） ==========
    print("\n\ud83d\udcf7 \u751f\u6210\u622a\u56fe\u5c55\u793a...")
    screenshots = [
        ("1.png", "Agent CLI \u4e3b\u754c\u9762 - \u591a\u6a21\u578b\u5bf9\u8bdd"),
        ("2.JPG", "\u6587\u4ef6\u62d6\u62fd + Markdown \u5b9e\u65f6\u6e32\u67d3"),
        ("3.JPG", "\u9879\u76ee\u7ba1\u7406 + \u4efb\u52a1\u961f\u5217"),
    ]
    for fname, label in screenshots:
        fpath = os.path.join(RESOURCES_DIR, fname)
        if os.path.exists(fpath):
            frame = load_image_frame(fpath)
            frame = add_label(frame, label)
            all_frames.extend([frame] * (4 * FPS))  # 每张 4 秒
            print(f"  \u2705 {fname}")
        else:
            print(f"  \u26a0\ufe0f {fname} \u4e0d\u5b58\u5728")

    # ========== 录屏展示 ==========
    print("\n\ud83c\udfa5 \u751f\u6210\u5f55\u5c4f\u5c55\u793a...")
    recordings = [
        ("\u5f55\u5c4f_20260615_152447.webm", "\u5b9e\u9645\u64cd\u4f5c\u5f55\u5c4f 1"),
        ("\u5f55\u5c4f_20260615_154515.webm", "\u5b9e\u9645\u64cd\u4f5c\u5f55\u5c4f 2"),
    ]
    for fname, label in recordings:
        fpath = os.path.join(RESOURCES_DIR, fname)
        if os.path.exists(fpath):
            frames = load_video_frames(fpath, max_frames=10 * FPS)
            # 给第一帧加标签
            if frames:
                frames[0] = add_label(frames[0], label)
            all_frames.extend(frames)
        else:
            print(f"  \u26a0\ufe0f {fname} \u4e0d\u5b58\u5728")

    # ========== AI 生成展示 ==========
    print("\n\ud83e\udd16 \u751f\u6210 AI \u751f\u6210\u5c55\u793a...")

    frame = create_text_slide("AI \u56fe\u7247\u751f\u6210", [
        "\u8f93\u5165\u63cf\u8ff0 \u2192 AI \u81ea\u52a8\u751f\u6210\u56fe\u7247",
        "\u5e03\u5076\u732b\u3001\u98ce\u666f\u3001\u8bbe\u8ba1\u7a3f... \u968f\u5fc3\u6240\u6b32"
    ])
    all_frames.extend([frame] * (3 * FPS))

    # AI 图片生成结果
    fpath = os.path.join(RESOURCES_DIR, "cat-ragdoll.jpg")
    if os.path.exists(fpath):
        frame = load_image_frame(fpath)
        frame = add_label(frame, "\ud83d\udc31 AI \u56fe\u7247\u751f\u6210\u793a\u4f8b - \u5e03\u5076\u732b")
        all_frames.extend([frame] * (5 * FPS))
        print(f"  \u2705 cat-ragdoll.jpg")

    # AI 海报生成结果
    fpath = os.path.join(RESOURCES_DIR, "poster-ragdoll.jpg")
    if os.path.exists(fpath):
        frame = load_image_frame(fpath)
        frame = add_label(frame, "\ud83c\udfa8 AI \u6d77\u62a5\u751f\u6210\u793a\u4f8b")
        all_frames.extend([frame] * (5 * FPS))
        print(f"  \u2705 poster-ragdoll.jpg")

    # 海报生成录屏
    fpath = os.path.join(RESOURCES_DIR, "\u6d77\u62a5\u751f\u6210.webm")
    if os.path.exists(fpath):
        frames = load_video_frames(fpath, max_frames=8 * FPS)
        if frames:
            frames[0] = add_label(frames[0], "\ud83c\udfa8 AI \u6d77\u62a5\u751f\u6210\u8fc7\u7a0b\u5f55\u5c4f")
        all_frames.extend(frames)
    else:
        print(f"  \u26a0\ufe0f \u6d77\u62a5\u751f\u6210.webm \u4e0d\u5b58\u5728")

    # ========== 片尾 CTA ==========
    print("\n\ud83c\udf1f \u751f\u6210\u7247\u5c3e...")
    cta = create_cta_frame()
    all_frames.extend([cta] * (5 * FPS))

    # ========== 写入视频 ==========
    print(f"\n\ud83d\udcca \u603b\u5e27\u6570: {len(all_frames)} | \u65f6\u957f: {len(all_frames)/FPS:.1f}\u79d2")
    out_path = os.path.join(OUTPUT_DIR, "agent-cli-promo.mp4")
    write_video(all_frames, out_path)

    print(f"\n\ud83c\udf89 \u5b8c\u6210! \u89c6\u9891\u4f4d\u4e8e: {out_path}")
    print(f"   \u6587\u4ef6\u5927\u5c0f: {os.path.getsize(out_path) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
