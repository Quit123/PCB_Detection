import os
import time
import shutil
import cv2
import argparse
from ultralytics import YOLO

def main(model_path):
    model = YOLO(model_path)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    source_dir = os.path.join(BASE_DIR, 'target')
    low_conf_raw_dir = os.path.join(BASE_DIR, 'low_conf_images', 'tmp')
    low_conf_marked_dir = os.path.join(BASE_DIR, 'low_conf_images', 'marked')
    os.makedirs(low_conf_raw_dir, exist_ok=True)
    os.makedirs(low_conf_marked_dir, exist_ok=True)

    print("开始监听目标目录...")

    while True:
        img_list = sorted(os.listdir(source_dir))

        if not img_list:
            time.sleep(1)
            continue

        for img_name in img_list:
            img_path = os.path.join(source_dir, img_name)

            start_time = time.time()
            results = model.predict(source=img_path, device='0', imgsz=640, conf=0.25, verbose=False)
            duration = time.time() - start_time
            print(f"检测 {img_name} 耗时: {duration:.3f} 秒")

            low_conf_flag = False
            pass_flag = False
            for result in results:
                if result.boxes is not None and len(result.boxes) > 0:
                    confs = result.boxes.conf.cpu().numpy()
                    print(confs)
                    if (confs < 0.6).any():
                        low_conf_flag = True
                else:
                    pass_flag = True

            if pass_flag:
                print("PASS")
                # ***********************************
                # 流出api接口，向外输出Pass信号
                # ***********************************
            elif low_conf_flag:
                shutil.copy(img_path, os.path.join(low_conf_raw_dir, img_name))
                img_with_boxes = results[0].plot()
                cv2.imwrite(os.path.join(low_conf_marked_dir, img_name), img_with_boxes)
                print(f"**********\n发现低置信度图片!\n低置信度图片已保存: {img_name}\n**********")
            else:
                print("Fail")
                # ***********************************
                # 流出api接口，向外输出Fail信号
                # ***********************************
            os.remove(img_path)

        time.sleep(0.05)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, required=True, help="模型权重路径")
    args = parser.parse_args()

    main(args.model)
