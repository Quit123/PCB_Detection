# PCB Detection(Model Backend)

## 目录结构

本项目数据集组织结构如下所示，适用于 BJ-PCB 缺陷检测任务：

```plaintext
active_learning/
├── low_conf_images/                   # 存放置信度低的检测图片及相关标注
│   ├── labels/                        # 通过 Label Studio 标注后的标签文件
│   ├── marked/                        # 模型标注好的低置信度图片
│   ├── raw/                           # 原始未经过模型检测的低置信度图片
│   └── temp/                          # 临时文件夹/中转站 
├── target/                            # 存放传送来的 PCB 图片
├── active_learning.py                 # 检测图片并筛选低置信度图片（检测主程序）
├── management.py                      # 数据管理脚本（转移+预处理图片）
├── next_train.yaml                    # 下轮训练配置文件
├── simulate_push.py                   # 模拟推送脚本
└── train.py                           # 模型训练脚本（测试用）

datasets/
├── BJ-PCB/                            # 数据集已划分好的训练/验证/测试目录（测试用）
│   ├── train/                         # 训练集
│   │   ├── images/                    # 图片
│   │   └── labels/                    # 标注信息（yolo格式）
│   └── val/                           # 验证集
│
├── normal/                            # 一般样本数据集（如有，用于扩充数据或对比分析）
│
├── raw/                               # 原始数据文件（标注文件和原始图像）
│    ├── BJ-PCB/                       # 原始数据文件（测试用）
│    │   └── Annotations/              # 原始标注文件（按类别存放）
│    │       ├── Missing_hole/
│    │       ├── Mouse_bite/
│    │       ├── Open_circuit/
│    │       ├── Short/
│    │       ├── Spur/
│    │       └── Spurious_copper/
│    └── next_train                    # 原始下一轮训练集
│            ├── images/               # 原始图像文件
│            └── labels/               # 转换为YOLO格式的标注文件（由脚本生成）
├── next_train/                        # 下一轮训练集
│    ├── train/                    
│    │   ├── images/                   # 图片
│    │   └── labels/                   # 标注信息（yolo格式）
│    └── val/                          # 下一轮验证集

```

## 注意事项

* 如果你的显卡驱动版本不支持 CUDA 11.8，请访问 [PyTorch 官网](https://pytorch.org/get-started/locally/) 选择合适版本。
* 本项目支持 Windows、Linux 系统，推荐使用 Conda 管理 Python 环境。
* 安装过程中如遇依赖冲突或安装失败，建议先更新 Conda：

```bash
conda update -n base -c defaults conda
```
