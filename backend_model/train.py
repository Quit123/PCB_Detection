import os

from ultralytics import YOLO
from ultralytics.models.yolo.detect import DetectionTrainer
from pre import split_dataset, batch_convert
import itertools

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

annotation_type = 'xml'


def Parameter_settings():
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

    # 'hsv_h': 0.015,
    # 'hsv_s': 0.7,
    # 'hsv_v': 0.4,
    # 'degrees': 10,
    # 'translate': 0.1,
    # 'scale': 0.5,
    # 'shear': 2.0,
    # 'perspective': 0.001
    # 定义参数候选范围

    hsv_h_values = [0.015]
    hsv_s_values = [0.5]
    hsv_v_values = [0.4]
    degrees_values = [15]
    translate_values = [0.1]
    scale_values = [0.5]
    shear_values = [2.5]
    perspective_values = [0.001]
    mosaic_values = [True]
    conf = [0.05]
    iou = [0.5]

    # 所有组合
    all_combinations = itertools.product(
        hsv_h_values,
        hsv_s_values,
        hsv_v_values,
        degrees_values,
        translate_values,
        scale_values,
        shear_values,
        perspective_values,
        mosaic_values,
        conf,
        iou
    )

    # 生成字典列表
    param_list = []
    for combo in all_combinations:
        param = {
            'name': f"exp_h{combo[0]}_s{combo[1]}_v{combo[2]}_d{combo[3]}_t{combo[4]}_sc{combo[5]}_sh{combo[6]}_m{combo[7]}",
            'hsv_h': combo[0],
            'hsv_s': combo[1],
            'hsv_v': combo[2],
            'degrees': combo[3],
            'translate': combo[4],
            'scale': combo[5],
            'shear': combo[6],
            'perspective': combo[7],
            'mosaic': combo[8],
            'conf': combo[9],
            'iou': combo[10]
        }
        param_list.append(param)

    return param_list


if __name__ == '__main__':

    # model = YOLO(model='ultralytics/cfg/models/11/yolo11.yaml')

    # model = YOLO('./yolo11m.pt')
    # model.train(data='./data.yaml', epochs=20, batch=4, device='0', imgsz=640, workers=2, cache=False,
    #             amp=True, mosaic=False, project='runs/train', name='exp')

    if annotation_type == 'xml':
        class_names = ['missing_hole', 'mouse_bite', 'open_circuit', 'short', 'spur', 'spurious_copper']
        xml_root_dir = './datasets/raw/BJ-PCB/Annotations'
        save_root_dir = './datasets/raw/BJ-PCB/labels'
        batch_convert(xml_root_dir, save_root_dir, class_names)

    split_dataset(
        target_data_set='BJ-PCB',
        annotation_name='labels',
        image_name='images',
        train_ratio=0.8
    )

    param_list = Parameter_settings()
    #model = YOLO("./yolo11m.pt")
    #model = YOLO('./yolov8m.pt')
    for param in param_list:

        args = dict(
            model="./yolo11m",
            data="./BJ-PCB-data.yaml",
            epochs=100,
            batch=8,
            project='runs/test',
            name="lack_Missing_hole_20250710_201220",
            hsv_h=param['hsv_h'],
            hsv_s=param['hsv_s'],
            hsv_v=param['hsv_v'],
            degrees=param['degrees'],
            translate=param['translate'],
            scale=param['scale'],
            shear=param['shear'],
            perspective=param['perspective'],
            mosaic=param['mosaic'],
            conf=param['conf'],
            iou=param['iou']
        )
        trainer = DetectionTrainer(overrides=args)
        trainer.train()
