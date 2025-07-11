import subprocess
import os
import uvicorn
import signal
import sys
import shutil
import zipfile
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from typing import Dict
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket, WebSocketDisconnect

app = FastAPI()
# BASE_DIR = os.path.dirname(__file__)  # server.py 所在目录
# low_conf_dir = os.path.join(BASE_DIR, "active_learning", "low_conf_images")
# app.mount("/active_learning", StaticFiles(directory=low_conf_dir), name="low_conf_images")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 存储训练状态和进程
training_processes: Dict[str, subprocess.Popen] = {}
training_status: Dict[str, Dict] = {}

# active_process: Optional[subprocess.Popen] = None
active_processes: Dict[str, subprocess.Popen] = {}

SAVE_DIR = "./active_learning/low_conf_images/labels"

BASE_DIR = os.path.dirname(__file__)
low_conf_dir = os.path.join(BASE_DIR, "active_learning", "low_conf_images")
app.mount("/static/low_conf_images", StaticFiles(directory=low_conf_dir), name="low_conf_images")


# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/training-status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # 可接收前端心跳消息
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/training-finished")
async def training_finished():
    print("@app.post(\"/api/training-finished\")")
    await manager.broadcast("training_complete")
    return {"status": "notified"}


def handle_shutdown(signum, frame):
    print("\n🚧 正在关闭服务器，停止所有训练进程...")
    for tid, process in training_processes.items():
        print(f"⛔ 终止训练 {tid} (PID: {process.pid})")
        process.terminate()
    sys.exit(0)


# 待实现和完善：前端隔一段时间调用该方法，将raw和marked对应图片传入前端展示，给工人标注用
@app.get("/api/transfer-images")
def get_transfer_images():
    src_dir = os.path.join(BASE_DIR, "active_learning", "low_conf_images", "tmp")
    raw_dir = os.path.join(BASE_DIR, "active_learning", "low_conf_images", "raw")

    if not os.path.exists(src_dir):
        return {"status": "error", "message": f"路径不存在: {src_dir}"}
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir, exist_ok=True)

    files = [f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

    if not files:
        return {"status": "no_image"}

    moved_files = []
    for file in files:
        src_path = os.path.join(src_dir, file)
        dst_path = os.path.join(raw_dir, file)
        shutil.move(src_path, dst_path)
        moved_files.append(f"{file}")

    return {"status": "ok", "files": moved_files}


class StartDetectRequest(BaseModel):
    model_name: str


@app.post("/api/start-detecting")
def start_detecting(req: StartDetectRequest):
    model_name = req.model_name
    process = active_processes.get(model_name)
    if process and process.poll() is None:
        return {"status": "already_running", "pid": process.pid}

    script_path = os.path.join(BASE_DIR, "active_learning", "active_learning.py")
    model_base_dir = os.path.join(BASE_DIR, "runs", "active_learning")

    if not os.path.exists(model_base_dir):
        return {"status": "error", "message": f"模型目录不存在: {model_base_dir}"}

    # 在模型目录下查找匹配的文件夹
    matched_model_path = None
    for d in os.listdir(model_base_dir):  # 所有模型文件
        full_path = os.path.join(model_base_dir, d)
        if os.path.isdir(full_path):  # 检查目录
            parts = d.split("_")
            if len(parts) >= 2:
                last_two = "_".join(parts[-2:])
                if last_two == model_name:  # name匹配
                    matched_model_path = os.path.join(full_path, "weights", "best.pt")
                    break

    if not matched_model_path or not os.path.exists(matched_model_path):
        return {"status": "error", "message": f"未找到匹配模型或权重文件: {model_name}"}

    # 构造启动命令
    cmd = [
        "python", script_path,
        "--model", matched_model_path
    ]

    active_process = subprocess.Popen(cmd)
    active_processes[model_name] = active_process

    print(f"🚀 启动主动学习进程 (PID: {active_process.pid})，模型路径: {matched_model_path}")
    return {"status": "started", "pid": active_process.pid, "model_path": matched_model_path}


@app.post("/api/stop-detecting")
def stop_detecting(req: StartDetectRequest):
    # global active_process
    model_name = req.model_name
    process = active_processes.get(model_name)
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
            print(f"✅ 已停止主动学习进程 (PID: {process.pid})")
            return {"status": "stopped", "pid": process.pid}
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"⚠️ 强制终止主动学习进程 (PID: {process.pid})")
            return {"status": "killed", "pid": process.pid}
    else:
        return {"status": "no_running_process"}


@app.post("/api/managing-data")
def managing_data():
    module_name = "backend_detect.active_learning.management_data_address"
    BASE_DIR_in = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # 设置 PYTHONPATH 环境变量为项目根目录
    env = os.environ.copy()
    env["PYTHONPATH"] = BASE_DIR_in
    cmd = [
        "python", "-m", module_name
    ]
    active_process = subprocess.Popen(cmd, env=env)
    print(f"数据整理进程 (PID: {active_process.pid})")
    return {"status": "start managing", "pid": active_process.pid}


@app.get("/api/return_model")
def return_model_dirs():
    model_base_dir = os.path.join(BASE_DIR, "runs", "active_learning")

    if not os.path.exists(model_base_dir):
        return {"status": "error", "message": f"路径不存在: {model_base_dir}"}

    model_dirs = []
    for d in os.listdir(model_base_dir):
        full_path = os.path.join(model_base_dir, d)
        if os.path.isdir(full_path):
            parts = d.split("_")
            if len(parts) >= 2:
                # 提取最后两个部分组成字符串
                last_two = "_".join(parts[-2:])
                model_dirs.append(last_two)
            else:
                # 如果不满足至少两个部分，原样返回
                model_dirs.append(d)

    # 按时间戳降序排序
    model_dirs.sort(key=lambda x: x[0], reverse=True)

    # 返回完整原始目录名列表
    model_dirs.sort(reverse=True)

    return {
        "status": "success",
        "model_dirs": model_dirs
    }


@app.post("/api/export_data")
async def export_data(request: Request):
    data = await request.json()
    for item in data:
        filename = f"{item['filename']}.txt"
        filepath = os.path.join(SAVE_DIR, filename)
        with open(filepath, "w") as f:
            f.write("\n".join(item["labels"]))
    return {"status": "success"}

@app.post("/upload/")
async def upload_model_zip(file: UploadFile = File(...)):
    model_base_dir = os.path.join(BASE_DIR, "runs", "active_learning")
    try:
        # 保存 zip 文件到临时路径
        zip_path = os.path.join(model_base_dir, file.filename)
        with open(zip_path, "wb") as f:
            f.write(await file.read())

        # 解压到同目录下，以 zip 文件名为目录名
        extract_name = os.path.splitext(file.filename)[0]
        extract_path = os.path.join(model_base_dir, extract_name)

        # 如果目录已存在，可选：先删除旧的
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        os.makedirs(extract_path, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        return {
            "status": "success",
            "unzipped_to": extract_path
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

if __name__ == "__main__":
    print("🚀 启动 PCB 缺陷检测训练服务器...")
    print("🕒 等待前端请求启动训练...")
    uvicorn.run(app, host="0.0.0.0", port=9000)
