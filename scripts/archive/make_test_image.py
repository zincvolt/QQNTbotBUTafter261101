from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGB", (420, 140), "white")
d = ImageDraw.Draw(img)
try:
    f = ImageFont.truetype("msyh.ttc", 34)
except Exception:
    f = ImageFont.load_default()
d.text((16, 24), "测试图片：今晚八点开会", fill="black", font=f)
d.text((16, 78), "记得带笔记本电脑", fill="black", font=f)
p = r"D:\QQNTBOT\_backup\ocr_test.png"
img.save(p)
print("saved", p)
