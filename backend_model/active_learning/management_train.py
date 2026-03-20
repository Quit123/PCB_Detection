import os
import shutil
from pathlib import Path
from datetime import datetime
from ultralytics.models.yolo.detect import DetectionTrainer
from ..pre import split_dataset, batch_convert
import requests
import zipfile
from dotenv import load_dotenv

from .label_stats import check_thresholds, count_yolo_pairs

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

load_dotenv()  # 默认从 .env 读取
SERVER_IP_DETECT = os.getenv("VITE_SERVER_IP_DETECT", "127.0.0.1")
SERVER_PORT_DETECT = os.getenv("VITE_SERVER_PORT_DETECT", "8000")


def find_latest_model_dir(base_dir, prefix='model_'):
    # 获取所有以 prefix 开头的文件夹
    candidates = [
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and d.startswith(prefix)
    ]

    if not candidates:
        raise ValueError(f"No model directories found in {base_dir}")

    # 提取时间戳并排序
    def extract_timestamp(name):
        parts = name.split('_')
        # 最后一个部分和倒数第二个组成时间戳 (YYYYMMDD_HHMMSS)
        timestamp = '_'.join(parts[-2:])
        return timestamp

    candidates.sort(key=lambda x: extract_timestamp(x), reverse=True)

    latest_dir = candidates[0]
    return os.path.join(base_dir, latest_dir, 'weights', 'best.pt')


def train(
        hsv_h_values=0.015,
        hsv_s_values=0.5,
        hsv_v_values=0.4,
        degrees_values=15,
        translate_values=0.1,
        scale_values=0.5,
        shear_values=2.5,
        perspective_values=0.001,
        mosaic_values=True
):
    base_dir = os.path.join(BASE_DIR, "runs", "active_learning")
    with open(os.path.join(BASE_DIR, "active_learning", "next_train.yaml"), "w") as f:
        f.write(yaml_content)
    data_url = os.path.join(BASE_DIR, "active_learning", "next_train.yaml")
    latest_model = find_latest_model_dir(base_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    args = dict(
        model=latest_model,
        data=data_url,
        epochs=5,
        batch=2,
        project=base_dir,
        name=f"model_{hsv_h_values}_{hsv_s_values}_{hsv_v_values}_{degrees_values}_{translate_values}_{scale_values}_{shear_values}_{perspective_values}_{mosaic_values}_{timestamp}",
        hsv_h=hsv_h_values,
        hsv_s=hsv_s_values,
        hsv_v=hsv_v_values,
        degrees=degrees_values,
        translate=translate_values,
        scale=scale_values,
        shear=shear_values,
        perspective=perspective_values,
        mosaic=mosaic_values,
    )


    """
    | 参数           |改进建议                                                          | 备注                         |
    | ------------- | -------------------------------------------------------------   | -------------------------- |
    | `hsv_h`       |可尝试 0.05 \~ 0.1                                               | 太小可能增强效果不明显，对颜色鲁棒性不足       |
    | `hsv_s`       |可尝试 0.5 \~ 0.9                                                | 如果颜色变化对类别区分影响小，可以适当放大      |
    | `hsv_v`       |可尝试 0.2 \~ 0.6                                                | 可增强亮度变化的鲁棒性                |
    | `degrees`     |可尝试 5 \~ 20                                                   | 根据实际缺陷角度分布调整               |
    | `translate`   |可尝试 0.05 \~ 0.2                                               | 缺陷位置分布较集中时，可减小；分散时可增大      |
    | `scale`       |建议 0.5 改为 0.5 ± delta，例如设置 scale=0.5, scale\_range=(0.5, 1.5) | 过大或过小 scale 可能导致特征丢失或形变不合理 |
    | `shear`       |可尝试 0 \~ 5                                                    | 一般对PCB类数据作用较小              |
    | `perspective` |保持小值即可                                                        | 太大会引入不自然形变                 |
    | `mosaic`      |可以试试关闭后看单样本训练效果，特别是缺陷小目标多时                        |                            |
    """

    split_dataset(
        target_data_set='next_train',
        annotation_name='labels',
        image_name='images',
        train_ratio=0.8,
        next_train=True
    )

    trainer = DetectionTrainer(overrides=args)
    trainer.train()

    output_dir = os.path.join(base_dir, args["name"])
    zip_path = output_dir + ".zip"
    zip_directory(output_dir, zip_path)
    upload_zip_to_server(zip_path, f"http://{SERVER_IP_DETECT}:{SERVER_PORT_DETECT}/upload/")

    notify_training_complete()


def zip_directory(source_dir: str, output_zip_path: str):
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    print(f"✅ 模型目录已打包：{output_zip_path}")


def upload_zip_to_server(zip_path: str, target_url: str):
    with open(zip_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(target_url, files=files)
        print("📦 上传结果：", response.status_code, response.text)
        response.raise_for_status()


def notify_training_complete():
    try:
        requests.post(f"http://127.0.0.1:8000/api/training-finished")
        print("✅ 已通知训练完成")
    except Exception as e:
        print("❌ 通知失败：", e)

    # 原 train 函数末尾添加以下内容
    # 假设训练输出目录如下：
    # output_dir = os.path.join(BASE_DIR, args["name"])
    # zip_path = output_dir + ".zip"
    # zip_directory(output_dir, zip_path)
    #
    # # 上传到另一个后端
    # try:
    #     upload_zip_to_server(zip_path, "http://192.168.1.100:8000/upload/")
    #     notify_training_complete()
    # except Exception as e:
    #     print("❌ 上传或通知失败：", e)


if __name__ == '__main__':
    low_conf_dir = os.path.join(BASE_DIR, "active_learning", "low_conf_images")
    next_train_dir = os.path.join(BASE_DIR, "datasets", "raw", "next_train")
    history_dir = os.path.join(BASE_DIR, "datasets", "history")

    # low_conf_dir = BASE_DIR + './low_conf_images'
    # next_train_dir = '../datasets/raw/next_train'
    # history_dir = '../datasets/history'
    # move_labeled_data(low_conf_dir, next_train_dir, history_dir)
    labels_dir = os.path.join(BASE_DIR, "datasets", "raw", "next_train", "labels")
    images_dir = os.path.join(BASE_DIR, "datasets", "raw", "next_train", "images")
    paired, inst = count_yolo_pairs(labels_dir, images_dir)
    ok, detail = check_thresholds(paired, inst)
    if not ok:
        print("❌ 未满足训练数据门槛，已中止:", detail.get("message"))
        raise SystemExit(1)
    print("数据移动与历史备份完成！")
    train()
    print("新数据完成训练！")
    notify_training_complete()
