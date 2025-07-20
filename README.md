# PCB Detection

## 环境安装要求

本项目基于 Python 3.10，推荐使用 Conda 创建隔离虚拟环境。

### 1️⃣ 创建并激活 Conda 虚拟环境

```bash
conda create -n yolov11 python=3.10
conda activate yolov11
```

### 2️⃣ 安装 JupyterLab（可选，用于交互式开发）

```bash
conda install jupyterlab
```

### 3️⃣ 安装 PyTorch + CUDA 11.8

请根据你的显卡驱动选择合适的 CUDA 版本，以下为 CUDA 11.8 示例：

```bash
pip install torch==2.0.0+cu118 torchvision==0.15.1+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
```

### 4️⃣ 安装项目依赖

```bash
pip install requirements.txt
```
若缺包请按照报错说明pip install <package_name>

---

## 数据集目录结构

本项目数据集组织结构如下所示，适用于 BJ-PCB 缺陷检测任务：

```plaintext
./
├── backend_detect/                  # 后端：检测服务模块（如主动学习、预测服务）
│   ├── active_learning/            # 主动学习核心逻辑
│   ├── datasets/simulate_ready_push/  # 模拟数据集存放路径
│   ├── runs/active_learning/       # 主动学习过程中的运行日志和模型保存
│   ├── server.py                   # 检测服务入口
│   └── pre.py                      # 数据预处理脚本

├── backend_model/                  # 后端：模型训练模块（基于YOLO/Ultralytics）
│   ├── active_learning/            # 与detect共用的主动学习模块
│   ├── docker/                     # Docker部署相关
│   ├── docs/                       # 项目文档目录
│   ├── examples/                   # 示例脚本与配置
│   ├── runs/active_learning/       # 训练/推理输出结果
│   ├── tests/                      # 单元测试模块
│   ├── ultralytics/                # YOLO模型源码及定制模块
│   ├── *.yaml                      # 数据集配置文件（BJ-PCB、GSD-PCB等）
│   ├── detect.py                   # 推理脚本
│   ├── train.py / val.py / test.py # 训练、验证、测试脚本
│   ├── server.py                   # 训练服务入口
│   └── image_labeler.py           # 图像标注逻辑（推测用于交互式标注）

├── frontend/                       # 前端：基于 Vue + TypeScript 的可视化界面
│   ├── public/                     # 静态资源目录
│   ├── src/                        # 前端源代码
│   │   ├── assets/                # 图像资源等
│   │   ├── components/           # 核心组件区块（如标注区域、结果展示）
│   │   │   ├── ControlPanel.vue
│   │   │   ├── DetectionArea.vue
│   │   │   ├── LabelArea.vue
│   │   │   ├── ResultTable.vue
│   │   │   └── TransfImg.vue
│   │   ├── stores/               # 状态管理模块（Pinia）
│   │   │   ├── manageImg.ts
│   │   │   └── manageModel.ts
│   │   └── main.ts / App.vue     # 项目入口
│   ├── package.json               # 前端依赖管理
│   └── vite.config.ts             # 构建配置文件（Vite）

├── requirements.txt               # Python依赖列表（后端环境）
├── README.md                      # 项目说明文档
```

### 说明

* `Dataset_Name/images/` 和 `Dataset_Name/labels/` 用于训练、验证、测试。
* `raw/Dataset_Name/Annotations/` 为每类缺陷的原始标注文件（如 XML）。
* `raw/Dataset_Name/labels/` 是转换后的 YOLO 格式标注文件，用于训练。
* 建议在数据预处理阶段，将原始数据组织成 YOLO 所需的 `images/` 和 `labels/` 结构。

### 示例标注文件

YOLO 格式标签（`.txt` 文件）：

```
<class_id> <x_center> <y_center> <width> <height>
```

数值均归一化到 0\~1。

如需数据集划分和格式转换脚本，可参考本项目提供的 `pre.py` 或自行编写批处理脚本。

---

### 🧭 使用说明

本项目由两个后端模块与一个前端可视化界面组成。请按以下步骤运行项目：

#### ✅ 安装依赖

```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

#### 🚀 启动服务

```bash
# 启动后端服务 1：检测服务
cd backend_detect
python server.py

# 启动后端服务 2：模型服务
cd backend_model
python server.py

# 启动前端服务（基于 Vue + Vite）
cd frontend
npm run dev
```

#### ⚙️ 配置服务地址（可选）

各模块间的服务通信地址通过 `.env` 文件进行配置：

| 路径                    | 功能说明                                        |
| --------------------- | ------------------------------------------- |
| `backend_detect/.env` | 设置前端访问 backend\_detect 的 IP 和端口             |
| `backend_model/.env`  | 设置 backend\_model 访问 backend\_detect 的地址    |
| `frontend/.env`       | 设置前端访问 backend\_detect 和 backend\_model 的地址 |

示例 `frontend/.env` 配置：

```env
VITE_DETECT_API_URL=http://localhost:8000
VITE_MODEL_API_URL=http://localhost:8001
```

请根据实际运行环境调整 IP 和端口，确保服务正常互通。

---

## 注意事项

* 如果你的显卡驱动版本不支持 CUDA 11.8，请访问 [PyTorch 官网](https://pytorch.org/get-started/locally/) 选择合适版本。
* 本项目支持 Windows、Linux 系统，推荐使用 Conda 管理 Python 环境。
* 安装过程中如遇依赖冲突或安装失败，建议先更新 Conda：

```bash
conda update -n base -c defaults conda
```
