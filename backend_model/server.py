import subprocess
import os
import uvicorn
import signal
import sys
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi import FastAPI, UploadFile, File, Request
import shutil
import zipfile

app = FastAPI()
# app.mount("/active_learning", StaticFiles(directory="low_conf_images"), name="low_conf_images")

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
# active_processes: Dict[str, subprocess.Popen] = {}

SAVE_DIR = "./active_learning/low_conf_images/labels"

BASE_DIR = os.path.dirname(__file__)
low_conf_dir = os.path.join(BASE_DIR, "active_learning", "low_conf_images")
# app.mount("/static/low_conf_images", StaticFiles(directory=low_conf_dir), name="low_conf_images")


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
    print("starting listening on websocket...")
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


@app.post("/api/managing-training")
def managing_training():
    module_name = "backend_model.active_learning.management_train"
    BASE_DIR_in = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # 设置 PYTHONPATH 环境变量为项目根目录
    env = os.environ.copy()
    env["PYTHONPATH"] = BASE_DIR_in

    cmd = [
        "python", "-m", module_name
    ]
    active_process = subprocess.Popen(cmd, env=env)
    # training_processes[active_process.pid] = active_process
    print(f"训练进程 (PID: {active_process.pid})")

    return {"status": "start training", "pid": active_process.pid}


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

UPLOAD_STATUS = {"done": False}

@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    UPLOAD_STATUS["done"] = False  # 上传开始，标记未完成
    model_base_dir = os.path.join(BASE_DIR, "datasets", "raw")
    os.makedirs(model_base_dir, exist_ok=True)

    # 保存 zip 文件
    zip_save_path = os.path.join(model_base_dir, file.filename)
    with open(zip_save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 解压 zip 文件到指定目录（与 zip 同名的子目录）
    extract_dir = os.path.join(model_base_dir, os.path.splitext(file.filename)[0])
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    print(f"📦 ZIP文件保存至: {zip_save_path}")
    print(f"📁 解压目标目录: {extract_dir}")
    with zipfile.ZipFile(zip_save_path, 'r') as zip_ref:
        print(f"📄 ZIP包含文件: {zip_ref.namelist()}")
        zip_ref.extractall(extract_dir)

    UPLOAD_STATUS["done"] = True  # 解压完成

    return {
        "status": "success",
        "filename": file.filename,
        "unzipped_to": extract_dir
    }

@app.get("/upload-status/")
def get_upload_status():
    return {"done": UPLOAD_STATUS["done"]}


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

if __name__ == "__main__":
    print("🚀 启动 PCB 缺陷检测训练服务器...")
    print("🕒 等待前端请求启动训练...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
