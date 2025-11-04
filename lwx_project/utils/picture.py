import platform
import typing

import io


def get_default_tessdata_path():
    if platform.system() == "Darwin":  # 测试mac下是否也可以直接用static的那个path
        return "/opt/homebrew/share/tessdata"
    elif platform.system() == "Windows":
        return r"D:\Programming\Tesseract-OCR\tessdata"
    return "不支持的类型或系统"

def concat_pictures(picture_bytes_list: typing.List[bytes]) -> bytes:
    """
    竖向拼接多张图片
    :param picture_bytes_list: 图片字节列表 (List[bytes])
    :return: 拼接后的图片字节 (bytes)，若输入为空则返回 None
    """
    from PIL import Image

    if not picture_bytes_list:
        raise ValueError("picture_bytes_list must not be empty")

    # 将字节转换为 PIL Image 对象
    images = []
    for img_bytes in picture_bytes_list:
        img = Image.open(io.BytesIO(img_bytes))
        # 确保图片是 RGB 模式（避免 RGBA/P 模式拼接出错）
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        images.append(img)

    if not images:
        raise ValueError("picture_bytes_list must not be empty")

    # 计算拼接后图片的总高度和最大宽度
    max_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)

    # 创建新图像（白底）
    combined = Image.new("RGB", (max_width, total_height), (255, 255, 255))

    # 竖向粘贴每张图片
    y_offset = 0
    for img in images:
        # 如果图片宽度小于最大宽度，居中或左对齐（这里左对齐）
        combined.paste(img, (0, y_offset))
        y_offset += img.height

    # 将结果保存为字节
    output = io.BytesIO()
    combined.save(output, format="PNG")
    return output.getvalue()


def crop_margins(png_bytes, left=0, top=0, right=0, bottom=0) -> bytes:
    """
    裁掉四周指定像素（left=裁掉左边多少像素）
    """
    from PIL import Image

    img = Image.open(io.BytesIO(png_bytes))
    width, height = img.size

    # 计算保留区域
    crop_left = left
    crop_top = top
    crop_right = width - right
    crop_bottom = height - bottom

    if not (0 <= crop_left < crop_right <= width and 0 <= crop_top < crop_bottom <= height):
        raise ValueError("裁剪边距过大")

    cropped_img = img.crop((crop_left, crop_top, crop_right, crop_bottom))

    output = io.BytesIO()
    img_format = img.format or 'PNG'
    cropped_img.save(output, format=img_format)
    return output.getvalue()


def ocr_from_bytes_pil(image_bytes: bytes, lang='chi_sim') -> str:
    from tesserocr import PyTessBaseAPI, PSM, OEM
    import pytesseract

    """
    使用 tesserocr 对图片字节进行 OCR 识别（支持中英文）
    :param image_bytes: 图片字节数据 (bytes)
    :param lang: Tesseract 语言，如 'chi_sim+eng'
    :return: 识别出的文本
    """
    from PIL import Image
    # 1. 从字节加载图像
    img = Image.open(io.BytesIO(image_bytes))

    # 5. 正确初始化语言 + 设置 PSM/OEM
    pytesseract.pytesseract.tesseract_cmd = r'D:\Programming\Tesseract-OCR\tesseract.exe'

    # 使用高精度模型（确保 tessdata_best 已放入 tessdata 目录）
    text = pytesseract.image_to_string(
        img,
        lang=lang,
        config='--oem 1 --psm 3'  # OEM 1 = LSTM only（推荐）
    )
    return text
    tessdata_path = get_default_tessdata_path()

    api = PyTessBaseAPI(path=tessdata_path, lang=lang, oem=1)
    try:
        # 初始化语言（关键！）
        api.SetPageSegMode(PSM.SINGLE_BLOCK)
        api.SetImage(img)
        return api.GetUTF8Text().strip()
    except Exception as e:
        print(e)
        return ""
    finally:
        api.End()


def ocr_from_path(image_path: str, lang='chi_sim', left=0, top=0, right=0, buttom=0) -> str:
    """
    从图片文件路径进行 OCR 识别（支持中英文）
    :param image_path: 图片文件路径（如 'page.png'）
    :param lang: Tesseract 语言，如 'chi_sim+eng'
    :return: 识别出的文本
    """
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        image_bytes = crop_margins(image_bytes, left=left, top=top, right=right, bottom=buttom)
        return ocr_from_bytes_pil(image_bytes, lang=lang)
    except FileNotFoundError:
        print(f"错误：文件未找到 - {image_path}")
        return ""
    except Exception as e:
        print(f"OCR 读取文件时出错: {e}")
        return ""

if __name__ == '__main__':
    p = r"D:\project\lwx_project\data\tmp.png"
    r = ocr_from_path(p, left=50, right=50)
    print(r)