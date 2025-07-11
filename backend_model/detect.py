# import torch
# from ultralytics.models import YOLO
# import os
# import numpy as np
# from sklearn.metrics import confusion_matrix
# import glob
#
#
#
# # if __name__ == '__main__':
# #     model = YOLO(model='./runs/train/exp3/weights/best.pt')
# #     results = model.predict(source='./datasets/images/train/0011.jpg', device='0', imgsz=640, project='runs/detect/', name='exp')
# #
# #     for result in results:
# #         boxes = result.boxes
# #         result.show()
# #         result.save(filename="./runs/detect/result.jpg")
#
#
# # 加载模型
# model = YOLO('./runs/train/official_exp/weights/best.pt')
# label_type = ['Missing_hole', 'Mouse_bite', 'Open_circuit', 'Short', 'Spur', 'Spurious_copper']
#
# # 初始化列表存储真实和预测类别
# true_classes = {}
# predicted_classes = {}
#
# # 1. 定义路径
# val_image_dir = './datasets/BJ-PCB/val/images'
# label_dir = './datasets/BJ-PCB/val/labels'
#
# # 2. 获取所有图像路径
# image_paths = []
# for root, dirs, files in os.walk(val_image_dir):
#     for file in files:
#         if file.lower().endswith(('.jpg', '.jpeg', '.png')):
#             image_paths.append(os.path.join(root, file))
#
# print(f"Found {len(image_paths)} images for prediction")
#
# # 3. 获取所有验证集路径
# label_paths = []
# for root, dirs, files in os.walk(label_dir):
#     for file in files:
#         if file.lower().endswith('.txt'):
#             label_paths.append(os.path.join(root, file))
#
# print(f"Found {len(label_paths)} images for prediction")
#
# # 3. 预测所有图像并收集结果
# for i, img_path in enumerate(image_paths):
#     # 预测图像
#     results = model.predict(source=img_path, device='0', imgsz=640, project='runs/detect/', name='exp')
#     # 处理预测结果
#     for result in results:
#         # 收集预测类别
#         for box in result.boxes:
#             # print("int(box.cls.item()):", int(box.cls.item()))
#             predicted_classes[i].append(int(box.cls.item()))
#     print(len(predicted_classes))
#
# # 3. 收集验证集
# for i, label_path in enumerate(label_paths):
#     # 读取标签文件（如果存在）
#     print("label_path:", label_path)
#     if os.path.exists(label_path):
#         with open(label_path, 'r') as f:
#             lines = f.readlines()
#             for line in lines:
#                 parts = line.strip().split()
#                 if len(parts) >= 1:  # 确保至少有一个元素
#                     true_classes[i].append(int(parts[0]))
#     else:
#         print(f"Warning: Label file not found for {label_path}")
#
# # 4. 确保列表长度匹配（如果预测框和标签数量不完全一致）
# min_length = min(len(true_classes), len(predicted_classes))
# true_classes = true_classes[:min_length]
# predicted_classes = predicted_classes[:min_length]
#
# print(f"Total true labels: {len(true_classes)}")
# print(f"Total predictions: {len(predicted_classes)}")
#
# # 5. 计算混淆矩阵
# if true_classes and predicted_classes:
#     # 获取类别数量（从模型中获取）
#     num_classes = len(model.names) if hasattr(model, 'names') else (max(max(true_classes), max(predicted_classes)) + 1)
#
#     # 计算混淆矩阵
#     conf_matrix = confusion_matrix(true_classes, predicted_classes, labels=range(num_classes))
#
#     # 保存混淆矩阵
#     np.savetxt('confusion_matrix.txt', conf_matrix, fmt='%d')
#     print("Confusion matrix saved to confusion_matrix.txt")
#
#     # 打印混淆矩阵（可选）
#     print("\nConfusion Matrix:")
#     print(conf_matrix)
# else:
#     print("Error: No labels or predictions found for comparison")

from ultralytics import YOLO

if __name__ == '__main__':
    # 如果你已经有 yolo11m.pt 权重，直接加载
    model = YOLO('./runs/train-2/exp_h0.015_s0.5_v0.4_d15_t0.05_sc0.5_sh2.5_m0.001/weights/best.pt')  # 或者写绝对路径

    # 验证集路径（假设你的验证集在 data.yaml 配置中已有定义）
    # 可以直接使用验证接口：
    metrics = model.val(data='./BJ-PCB-data.yaml',
                        batch=8,
                        device='0',
                        imgsz=640,
                        conf=0.05,     # 可以按需调整置信度阈值
                        iou=0.5,       # IoU 阈值
                        split='val')   # 显式指定验证集（一般默认就是val）

    # 输出验证集结果
    print(metrics)  # metrics 包含mAP、精度、召回率等信息
