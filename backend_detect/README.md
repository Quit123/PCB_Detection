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

```
