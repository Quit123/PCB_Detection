import os
import shutil
import time
import argparse
import random
from pathlib import Path


def simulate_push(source_dir, target_dir, interval=1.0, max_push=None, shuffle=False):
    """
    模拟 AOI 数据流，将 source_dir 里的图片按 interval 秒推送到 target_dir。

    :param source_dir: 模拟 AOI 原始图片目录
    :param target_dir: 推送图片的目标目录
    :param interval: 推送间隔（秒）
    :param max_push: 最大推送图片数（None 表示全部推送完）
    :param shuffle: 是否随机打乱图片顺序
    """
    source_path = Path(source)
    target_path = Path(target)


    os.makedirs(target_dir, exist_ok=True)

    image_list = list(source_path.glob('*.*'))

    if shuffle:
        random.shuffle(image_list)

    # pushed_count = 0
    for img_path in image_list:
        # if max_push is not None and pushed_count >= max_push:
        #     break
        dest_path = target_path / img_path.name
        shutil.copy(img_path, dest_path)
        print(f"Pushed {img_path} -> {dest_path}")
        # pushed_count += 1
        time.sleep(random.uniform(0, 1))

    print("模拟推送完成。")


if __name__ == '__main__':
    # 命令行传入
    # parser = argparse.ArgumentParser(description="模拟 AOI 数据流向目标目录推送图片")
    # parser.add_argument('--source', type=str, required=True, help="AOI 图片源目录")
    # parser.add_argument('--target', type=str, required=True, help="图片推送目标目录")
    # parser.add_argument('--interval', type=float, default=1.0, help="推送间隔（秒）")
    # parser.add_argument('--max_push', type=int, default=None, help="最大推送图片数（None 表示全部推送）")
    # parser.add_argument('--shuffle', action='store_true', help="是否打乱图片顺序")
    #
    # args = parser.parse_args()
    #
    # simulate_push(args.source, args.target, args.interval, args.max_push, args.shuffle)

    # 参数传入
    source = '../datasets/simulate_ready_push'
    target = './target'
    interval = 1.0
    max_push = 25
    shuffle = True

    simulate_push(source, target, interval, max_push, shuffle)