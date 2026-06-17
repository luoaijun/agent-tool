"""
Agent CLI Splash 动画生成器
带动态Logo动画、渐变过渡、能力展示、教程的30秒Splash视频
输出: output/agent-cli-splash.mp4
"""
import os
import sys
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw

# 修复 Windows 控制台 Unicode 编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 从 generate_promo 导入全部工具
from generate_promo import (
    PROJECT_DIR, RESOURCES_DIR, OUTPUT_DIR,
    W, H, FPS, BG_COLOR, ACCENT_COLOR, WHITE, GRAY,
    FONT_LARGE, FONT_MED, FONT_SMALL, FONT_TINY,
    get_font, create_title_frame, create_text_slide, create_cta_frame,
    load_image_frame, load_video_frames, add_label,
    VideoStreamer
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 用于 Logo 动画的色彩
DARK_BG = (15, 18, 35)           # 比 BG_COLOR 更深的底色
LOGO_PRIMARY = (80, 200, 255)     # 主色蓝（提亮）
LOGO_SECONDARY = (120, 220, 255)  # 浅蓝（提亮）
LOGO_GLOW = (60, 180, 240)       # 光晕蓝（提亮）
LOGO_PARTICLE = (220, 235, 255)  # 粒子白蓝（提亮）
LOGO_DIM = (60, 100, 150)         # 暗轨（提亮）

CENTER = (W // 2, H // 2)
LOGO_R = 120  # Logo 核心半径

# ============================================================
# 数学工具
# ============================================================

def pt_on_circle(cx, cy, r, angle_deg):
    """圆心(cx,cy) 半径r 角度(度) → (x, y)"""
    rad = math.radians(angle_deg)
    return (cx + r * math.cos(rad), cy - r * math.sin(rad))

def hexagon_vertices(cx, cy, r, rot_deg=0):
    """六边形6个顶点"""
    verts = []
    for i in range(6):
        angle = 60 * i + rot_deg - 90  # -90使尖角朝上
        verts.append(pt_on_circle(cx, cy, r, angle))
    return verts

def lerp_rgb(c1, c2, t):
    """RGB 线性插值"""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def ease_out_cubic(t):
    """缓出三次方"""
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    """缓入缓出"""
    return t * t * (3 - 2 * t)


# ============================================================
# 动画 Logo 逐帧绘制
# ============================================================

def create_animated_logo(t):
    """
    参数 t: 时间(秒), 0~6
    返回: BGR numpy 帧
    """
    img = Image.new("RGB", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)
    cx, cy = CENTER

    # ---- 阶段划分 ----
    # 0-1s: 核心六边形缩放弹入
    # 1-2s: 轨道环出现
    # 2-4s: 粒子绕行
    # 4-6s: 标题文字淡入 + 稳定

    # 核心六边形缩放（弹入效果）
    if t < 0.8:
        progress = ease_out_cubic(t / 0.8)
        r = LOGO_R * (0.2 + 0.8 * progress)
        alpha = progress
    else:
        r = LOGO_R
        alpha = 1.0

    # 脉冲（持续轻微呼吸）
    pulse = 1.0 + 0.03 * math.sin(t * 3.0)

    # 绘制光晕 — 用多层半透明圆（PIL 限制，用 RGBA overlay 实现）
    glow_r = int(r * 1.6)
    for i in range(3):
        gr = glow_r - i * 20
        if gr <= 0:
            continue
        ga = max(0, min(255, int(30 * alpha * (1 - i * 0.3))))
        if ga <= 0:
            continue
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse(
            [cx - gr, cy - gr, cx + gr, cy + gr],
            fill=(LOGO_GLOW[0], LOGO_GLOW[1], LOGO_GLOW[2], ga)
        )
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # 绘制核心六边形
    if t >= 0.05:
        rot = t * 20  # 缓慢旋转
        verts = hexagon_vertices(cx, cy, int(r * pulse), rot)
        fill_color = LOGO_PRIMARY if t < 4 else LOGO_SECONDARY
        draw.polygon(verts, fill=fill_color, outline=LOGO_SECONDARY)

    # 内六边形（镂空感）
    inner_verts = hexagon_vertices(cx, cy, int(r * 0.45 * pulse), t * 15)
    draw.polygon(inner_verts, fill=DARK_BG, outline=LOGO_DIM)

    # 中央 "A" 字母
    if t > 1.5:
        a_alpha = min(1.0, (t - 1.5) / 0.8)
        a_color = lerp_rgb(DARK_BG, WHITE, a_alpha)
        font_a = get_font(int(r * 1.3))
        bbox = draw.textbbox((0, 0), "A", font=font_a)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx - tw//2, cy - th//2 - int(r*0.05)), "A", font=font_a, fill=a_color)

    # 轨道环
    if t > 0.6:
        for layer in range(3):
            ring_r = int(LOGO_R * (1.8 + layer * 0.45))
            ring_alpha = min(1.0, (t - 0.6 - layer * 0.2) / 0.5)
            ring_rot = t * (25 - layer * 8) * (1 if layer % 2 == 0 else -1)
            ring_color = lerp_rgb(LOGO_DIM, LOGO_SECONDARY, ring_alpha * 0.6)

            # 画弧段（用点近似）
            num_segments = 60
            for seg in range(num_segments):
                a1 = ring_rot + seg * (360 / num_segments)
                a2 = a1 + 3
                p1 = pt_on_circle(cx, cy, ring_r, a1)
                p2 = pt_on_circle(cx, cy, ring_r, a2)
                draw.line([p1, p2], fill=ring_color, width=2)

    # 粒子（6个，围绕轨道）
    if t > 1.2:
        for p in range(6):
            p_orbit = 1.5 + (p % 3) * 0.45
            p_angle = t * (40 - p * 10) + p * 60
            p_speed = 1.0 if p % 2 == 0 else -0.7
            px, py = pt_on_circle(cx, cy, int(LOGO_R * p_orbit), p_angle * p_speed)

            # 闪烁
            flicker = 0.5 + 0.5 * math.sin(t * 8 + p * 2.5)
            pr = int(4 + 3 * flicker)
            p_color = lerp_rgb(LOGO_PARTICLE, WHITE, flicker)
            draw.ellipse([px-pr, py-pr, px+pr, py+pr], fill=p_color)

    # Agent CLI 标题淡入
    if t > 3.5:
        title_alpha = min(1.0, (t - 3.5) / 1.5)
        title_color = lerp_rgb(DARK_BG, ACCENT_COLOR, title_alpha)
        font_title = get_font(56)
        draw.text((cx - 180, cy + LOGO_R + 60), "Agent CLI", font=font_title, fill=title_color)

        sub_color = lerp_rgb(DARK_BG, GRAY, title_alpha)
        font_sub = get_font(24)
        draw.text((cx - 200, cy + LOGO_R + 130), "桌面 AI 多模型任务运行器 · v0.8.19",
                  font=font_sub, fill=sub_color)

    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


# ============================================================
# 场景过渡
# ============================================================

def crossfade(frame1, frame2, progress):
    """两帧之间渐变，progress 0=全frame1, 1=全frame2"""
    if progress <= 0:
        return frame1
    if progress >= 1:
        return frame2
    return cv2.addWeighted(frame1, 1 - progress, frame2, progress, 0)

def create_fade_sequence(frames_a, frames_b, overlap_frames=30):
    """
    将两段帧序列用渐变衔接
    overlap_frames: 渐变帧数
    """
    if not frames_a and not frames_b:
        return []
    if not frames_a:
        return list(frames_b)
    if not frames_b:
        return list(frames_a)

    result = []
    # A 的纯部分（去掉重叠）
    result.extend(frames_a[:-overlap_frames] if len(frames_a) > overlap_frames else [])

    # 渐变的 overlap 区域
    a_tail = frames_a[-overlap_frames:] if len(frames_a) >= overlap_frames else frames_a
    b_head = frames_b[:overlap_frames] if len(frames_b) >= overlap_frames else frames_b
    n = min(len(a_tail), len(b_head))

    for i in range(n):
        progress = i / max(n - 1, 1)
        result.append(crossfade(a_tail[i] if i < len(a_tail) else a_tail[-1],
                                b_head[i], progress))

    # B 的剩余部分
    result.extend(frames_b[n:] if len(frames_b) > n else [])
    return result


# ============================================================
# 逐条弹出文字动画
# ============================================================

def animate_bullet_sequence(title, bullets, duration_sec, highlight_idx=-1):
    """
    生成逐条弹出的能力展示帧序列
    duration_sec: 总时长
    """
    total_frames = int(duration_sec * FPS)
    frames = []
    n = len(bullets)

    # 每条子弹的动画：0.3s 淡入 + 位移
    bullet_duration = duration_sec / (n + 0.5)  # 每条时间
    bullet_frames = int(bullet_duration * FPS)
    enter_frames = int(0.3 * FPS)  # 淡入帧数

    for f_idx in range(total_frames):
        t = f_idx / FPS
        img = Image.new("RGB", (W, H), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # 标题 - 居中，从 30% 亮度淡入避免不可见
        title_alpha = min(1.0, t / 0.5)
        title_start = tuple(int(c * 0.3) for c in ACCENT_COLOR)
        title_color = lerp_rgb(title_start, ACCENT_COLOR, title_alpha)
        title_text = "> " + title
        bbox = draw.textbbox((0, 0), title_text, font=FONT_LARGE)
        draw.text(((W - (bbox[2] - bbox[0])) // 2, 80), title_text, font=FONT_LARGE, fill=title_color)

        # 子弹 - 居中，从 30% 亮度淡入避免不可见
        for i in range(n):
            bullet_start = i * bullet_duration
            local_t = t - bullet_start

            if local_t < 0:
                continue  # 还没到这条

            y = 280 + i * 70

            if local_t < 0.3:
                # 淡入 + 向左位移
                progress = local_t / 0.3
                alpha = progress
                offset_x = int(30 * (1 - progress))
                target = ACCENT_COLOR if i == highlight_idx else WHITE
                start_c = tuple(int(c * 0.3) for c in target)
                color = lerp_rgb(start_c, target, alpha)
            else:
                alpha = 1.0
                offset_x = 0
                color = ACCENT_COLOR if i == highlight_idx else WHITE

            font = FONT_MED if i == highlight_idx else FONT_SMALL
            bullet_text = "-  " + bullets[i]
            bbox = draw.textbbox((0, 0), bullet_text, font=font)
            draw.text(((W - (bbox[2] - bbox[0])) // 2 + offset_x, y), bullet_text, font=font, fill=color)

        frames.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

    return frames


# ============================================================
# 截图渐变轮播
# ============================================================

def screenshot_slideshow(screenshots, duration_per=2.0, fade_frames=15):
    """
    screenshots: [(filename, label), ...]
    返回渐变轮播帧序列
    """
    all_frames = []

    for i, (fname, label) in enumerate(screenshots):
        fpath = os.path.join(RESOURCES_DIR, fname)
        if not os.path.exists(fpath):
            print(f"  [!!] {fname} 不存在，跳过")
            continue

        frame = load_image_frame(fpath)
        frame = add_label(frame, label)
        frames_static = int(duration_per * FPS)
        seg_frames = [frame] * frames_static

        if i > 0 and all_frames:
            # 与前一段渐变
            prev = all_frames[-fade_frames:] if len(all_frames) >= fade_frames else all_frames
            seg_start = seg_frames[:fade_frames]
            n = min(len(prev), len(seg_start))
            for j in range(n):
                progress = j / max(n - 1, 1)
                p_idx = -(n - j) if j < n else None
                idx = len(all_frames) - n + j
                if 0 <= idx < len(all_frames):
                    all_frames[idx] = crossfade(all_frames[idx], seg_start[j], progress)
            all_frames.extend(seg_frames[n:])
        else:
            all_frames.extend(seg_frames)

        print(f"  [OK] {fname} ({frames_static}帧)")

    return all_frames


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("  Agent CLI Splash 动画")
    print("=" * 60)

    out_path = os.path.join(OUTPUT_DIR, "agent-cli-splash.mp4")
    vs = VideoStreamer(out_path)

    with vs:
        # ===== [1/5] Logo 动画 (0-6s) =====
        print("\n[1/5] 动态 Logo 动画 (6秒)...")
        logo_frames = []
        for f in range(6 * FPS):
            t = f / FPS
            logo_frames.append(create_animated_logo(t))
        for f in logo_frames:
            vs.write_frame(f)
        print(f"  生成 {len(logo_frames)} 帧")

        # ===== [2/5] 能力展示 (6-13s, 7秒) =====
        print("\n[2/5] 能力展示动画 (7秒)...")
        bullets = [
            "多模型并行 — 同时运行多个 AI 模型，自动分解任务",
            "智能路由 — 根据任务类型自动选择最佳模型",
            "本地语音 — Windows 原生引擎，说话即交互",
            "文件拖拽 — 拖入图片/文档，AI 自动分析内容",
            "跨设备联动 — 微信小程序扫码，手机端发起任务",
        ]
        cap_frames = animate_bullet_sequence("核心能力", bullets, 7.0)

        # 与 Logo 尾帧渐变衔接
        overlap = 20
        logo_tail = logo_frames[-overlap:]
        cap_head = cap_frames[:overlap]
        for i in range(overlap):
            progress = i / (overlap - 1)
            vs.write_frame(crossfade(logo_tail[i], cap_head[i], progress))
        for f in cap_frames[overlap:]:
            vs.write_frame(f)

        # 技能标签条形码效果（短暂）
        tag_frame = create_text_slide("支持模型", [
            "DeepSeek · 小米 MiMo · 自定义 OpenAI 兼容模型",
        ])
        vs.write_frames(tag_frame, int(1.0 * FPS))

        # ===== [3/5] 截图轮播 (14-20s, 6秒) =====
        print("\n[3/5] 截图渐变轮播 (6秒)...")
        screenshots = [
            ("1.png", "主界面 — 多模型对话"),
            ("2.JPG", "文件拖拽 + Markdown 实时渲染"),
            ("3.JPG", "任务队列 + 项目切换"),
        ]
        ss_frames = screenshot_slideshow(screenshots, duration_per=2.0, fade_frames=15)

        # 衔接：上一段尾帧 渐变到 截图
        recent_size = min(overlap, len(ss_frames))
        # 占位过渡
        transition_frames = ss_frames[:recent_size]  # 直接写
        for f in transition_frames:
            vs.write_frame(f)
        for f in ss_frames[recent_size:]:
            vs.write_frame(f)

        # ===== [4/5] 教程三步 (20-25s, 5秒) =====
        print("\n[4/5] 教程动画 (5秒)...")
        tutorial_bullets = [
            "1. 配置 API Key — 选择模型提供商，填入密钥",
            "2. 新建项目 — 左上角项目选择器，创建独立工作空间",
            "3. 开始对话 — 输入任务，AI 自动路由执行",
        ]
        tut_frames = animate_bullet_sequence("三步上手", tutorial_bullets, 5.0)
        for f in tut_frames:
            vs.write_frame(f)

        # ===== [5/5] CTA 片尾 (25-30s, 5秒) =====
        print("\n[5/5] CTA 片尾 (5秒)...")

        # CTA 帧 + 最后定格
        cta_frame = create_cta_frame()

        # 先渐变过渡 0.5秒
        tut_tail = tut_frames[-15:] if len(tut_frames) >= 15 else tut_frames
        for i in range(15):
            progress = i / 14
            if i < len(tut_tail):
                vs.write_frame(crossfade(tut_tail[i], cta_frame, progress))
            else:
                vs.write_frame(cta_frame)

        # 剩余 CTA 静态
        vs.write_frames(cta_frame, int(4.5 * FPS))

    # 完成
    duration = vs.count / FPS
    print(f"\n{'='*60}")
    print(f"  总帧数: {vs.count} | 时长: {duration:.1f}秒")

    if os.path.exists(out_path):
        size_mb = os.path.getsize(out_path) / 1024 / 1024
        print(f"  文件: {out_path}")
        print(f"  大小: {size_mb:.1f} MB")
    else:
        print(f"  [错误] 输出文件不存在！")

    print(f"{'='*60}")
    return duration


if __name__ == "__main__":
    main()
