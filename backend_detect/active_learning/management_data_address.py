import os
import shutil
from pathlib import Path
from datetime import datetime
import zipfile
import os
from ultralytics.models.yolo.detect import DetectionTrainer
from ..pre import split_dataset, batch_convert
import requests

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

annotation_type = 'xml'

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # 项目根目录

train_path = os.path.join(BASE_DIR, "datasets/next_train/train/images").replace("\\", "/")
val_path = os.path.join(BASE_DIR, "datasets/next_train/val/images").replace("\\", "/")
yaml_content = f"""
train: {train_path}
val: {val_path}
nc: 6
names: ['Missing_hole', 'Mouse_bite', 'Open_circuit', 'Short', 'Spur', 'Spurious_copper']
"""

def clear_directory(dir_path):
    """
    清空目录下所有文件和子文件夹
    """
    dir_path = Path(dir_path)
    if dir_path.exists():
        for item in dir_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)


def move_labeled_data(low_conf_dir, next_train_dir, history_dir):
    labels_src = Path(low_conf_dir) / 'labels'
    images_src = Path(low_conf_dir) / 'raw'
    marked_images_src = Path(low_conf_dir) / 'marked'
    labels_dst = Path(next_train_dir) / 'labels'
    images_dst = Path(next_train_dir) / 'images'

    # 确保目标目录存在
    labels_dst.mkdir(parents=True, exist_ok=True)
    images_dst.mkdir(parents=True, exist_ok=True)

    print(f"清空 {labels_dst} ...")
    clear_directory(labels_dst)
    print(f"清空 {images_dst} ...")
    clear_directory(images_dst)
    clear_directory(marked_images_src)
    # print(f"清空 {images_dst} ...")

    # 创建历史目录（按日期命名）
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    history_subdir = Path(history_dir) / f'batch_{date_str}'
    history_labels = history_subdir / 'labels'
    history_images = history_subdir / 'images'
    history_labels.mkdir(parents=True, exist_ok=True)
    history_images.mkdir(parents=True, exist_ok=True)

    # 移动并备份标签文件
    label_files = list(labels_src.glob('*.txt'))
    for file in label_files:
        dst_path = labels_dst / file.name
        shutil.move(file, dst_path)
        # 复制到历史
        shutil.copy(dst_path, history_labels / file.name)
        print(f"已移动标签: {file} -> {dst_path}，并已备份到历史: {history_labels / file.name}")

    # 移动并备份图片文件
    image_files = list(images_src.glob('*.*'))  # 可指定格式如 '*.jpg'
    for file in image_files:
        dst_path = images_dst / file.name
        shutil.move(file, dst_path)
        # 复制到历史
        shutil.copy(dst_path, history_images / file.name)
        print(f"已移动图片: {file} -> {dst_path}，并已备份到历史: {history_images / file.name}")

# import os
from dotenv import load_dotenv
load_dotenv()  # 默认从 .env 读取
SERVER_IP = os.getenv("VITE_SERVER_IP", "127.0.0.1")
SERVER_PORT = os.getenv("VITE_SERVER_PORT", "8000")

def upload_and_trigger_training(source_dir: str, output_zip_path: str):
    """
    将 source_dir 目录下所有内容打包成 output_zip_path 文件
    """

    source_dir = str(source_dir)
    output_zip_path = str(output_zip_path)

    if os.path.exists(output_zip_path):
        os.remove(output_zip_path)
        print(f"已删除已有 zip 文件：{output_zip_path}")

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(str(file_path), str(arcname))  # 明确转为 str
    print(f"已打包为：{output_zip_path}")
    with open(output_zip_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"http://{SERVER_IP}:{SERVER_PORT}/upload/",
            files=files
        )
        print(response.json())
    # try:
    #     res_json = response.json()
    #     print("📦 上传结果：", res_json)
    #     # 第二步：如果成功上传并解压，触发训练
    #     if res_json.get("status") == "success":
    #         training_response = requests.post(f"http://{SERVER_IP_DETECT}:{SERVER_PORT_DETECT}/api/managing-training")
    #         print("🚀 触发训练结果：", training_response.json())
    #     else:
    #         print("❌ 上传失败，不触发训练")
    # except Exception as e:
    #     print("❌ 请求失败或响应格式错误：", str(e))


if __name__ == '__main__':
    low_conf_dir = os.path.join(BASE_DIR, "active_learning", "low_conf_images")
    next_train_dir = os.path.join(BASE_DIR, "datasets", "raw", "next_train")
    history_dir = os.path.join(BASE_DIR, "datasets", "history")

    # low_conf_dir = BASE_DIR + './low_conf_images'
    # next_train_dir = '../datasets/raw/next_train'
    # history_dir = '../datasets/history'
    move_labeled_data(low_conf_dir, next_train_dir, history_dir)
    zip_output_path = os.path.join(BASE_DIR, "datasets", "next_train.zip")
    upload_and_trigger_training(next_train_dir, zip_output_path)
    print("数据移动与历史备份完成！")

