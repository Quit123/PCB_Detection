import os
import gc
import torch
import sys
from ultralytics import YOLO
from ultralytics.models.yolo.detect import DetectionTrainer
from pre import split_dataset, batch_convert
import itertools

# 必须在导入任何PyTorch相关库之前设置
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
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

def init_cuda_memory():
    """初始化CUDA内存设置"""
    # 1. 设置防止碎片的环境变量
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    
    # 2. 预热GPU内存（关键步骤）
    try:
        # 分配一个小张量来初始化CUDA上下文
        x = torch.ones((1024, 1024)).cuda()
        del x
        torch.cuda.empty_cache()
        print("✅ GPU内存预热完成")
    except Exception as e:
        print(f"⚠️ 内存预热失败: {str(e)}")

if __name__ == '__main__':
    init_cuda_memory()  # 在所有操作前调用
    # model = YOLO(model='ultralytics/cfg/models/11/yolo11.yaml')

    # model = YOLO('./yolo11m.pt')
    # model.train(data='./data.yaml', epochs=20, batch=4, device='0', imgsz=640, workers=2, cache=False,
    #             amp=True, mosaic=False, project='runs/train', name='exp')

    

    split_dataset(
        target_data_set='GSD-PCB',
        annotation_name='labels',
        image_name='images',
        train_ratio=0.8
    )

    param_list = Parameter_settings()
    #model = YOLO("./yolo11m.pt")
    #model = YOLO('./yolov8m.pt')
    for param in param_list:
         # 重置CUDA设备
        torch.cuda.empty_cache()
    # 创建一个虚假的tensor来触发内存清理
        x = torch.zeros(1).cuda()
        del x
        torch.cuda.empty_cache()
        args = dict(
            model="./yolo11m.pt",
            data="./GSD-PCB-data.yaml",
            epochs=1,
            batch=4,
            project='runs/test',
            name=param['name'],
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

       