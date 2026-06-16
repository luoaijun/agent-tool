import sys
print(f"Python: {sys.version}")

# Check Pillow
try:
    from PIL import Image, ImageDraw, ImageFont
    print("Pillow: OK")
except ImportError:
    print("Pillow: NOT INSTALLED")

# Check OpenCV
try:
    import cv2
    print(f"OpenCV: {cv2.__version__}")
except ImportError:
    print("OpenCV: NOT INSTALLED (will install)")

# Check ffmpeg via imageio
try:
    import imageio_ffmpeg
    print(f"imageio-ffmpeg: {imageio_ffmpeg.get_ffmpeg_version()}")
except ImportError:
    print("imageio-ffmpeg: NOT INSTALLED (will install)")
