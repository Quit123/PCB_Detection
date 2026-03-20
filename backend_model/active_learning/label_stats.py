"""YOLO 标注目录统计与训练前数量门槛（见项目根目录 config/active_learning.json → retrain）。"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

from .policy_config import get_retrain_thresholds, policy_file_path

_IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp")


def get_training_thresholds() -> tuple[int, int]:
    """来自 JSON；阈值为 0 表示不启用该项检查。"""
    return get_retrain_thresholds()


def count_yolo_pairs(labels_root: str, images_root: str) -> tuple[int, int]:
    """
    遍历 labels_root 下所有 .txt：统计非空行（实例数）；若 images_root 同相对路径下
    存在同名图像，则计为一张「已配对」图。
    返回 (paired_image_count, total_label_instances)。
    """
    if not os.path.isdir(labels_root):
        return 0, 0

    paired = 0
    instances = 0

    for dirpath, _, filenames in os.walk(labels_root):
        for fn in filenames:
            if not fn.lower().endswith(".txt"):
                continue
            label_path = os.path.join(dirpath, fn)
            rel_sub = os.path.relpath(dirpath, labels_root)
            stem = fn[:-4]
            if rel_sub in (".", ""):
                img_dir = images_root
            else:
                img_dir = os.path.join(images_root, rel_sub)

            try:
                with open(label_path, encoding="utf-8", errors="ignore") as f:
                    n_lines = sum(1 for ln in f if ln.strip())
            except OSError:
                n_lines = 0
            instances += n_lines

            if os.path.isdir(img_dir) and _image_exists(img_dir, stem):
                paired += 1

    return paired, instances


def _image_exists(img_dir: str, stem: str) -> bool:
    try:
        names = os.listdir(img_dir)
    except OSError:
        return False
    stem_lower = stem.lower()
    for name in names:
        path = os.path.join(img_dir, name)
        if not os.path.isfile(path):
            continue
        base, ext = os.path.splitext(name)
        if base.lower() == stem_lower and ext.lower() in _IMG_EXT:
            return True
    return False


def check_thresholds(
    paired: int, label_instances: int
) -> tuple[bool, Optional[Dict[str, Any]]]:
    min_img, min_inst = get_training_thresholds()
    if min_img <= 0 and min_inst <= 0:
        return True, None

    if min_img > 0 and paired < min_img:
        return False, {
            "paired_labeled_images": paired,
            "label_instances": label_instances,
            "required_min_images": min_img,
            "required_min_instances": min_inst,
            "message": (
                f"Labeled image pairs {paired} < required {min_img} "
                f"(edit retrain.min_labeled_images in {policy_file_path()})."
            ),
        }
    if min_inst > 0 and label_instances < min_inst:
        return False, {
            "paired_labeled_images": paired,
            "label_instances": label_instances,
            "required_min_images": min_img,
            "required_min_instances": min_inst,
            "message": (
                f"Label instances {label_instances} < required {min_inst} "
                f"(edit retrain.min_label_instances in {policy_file_path()})."
            ),
        }
    return True, None
