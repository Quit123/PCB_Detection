"""Load config/active_learning.json from project root (PCB-Detection)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

_DEFAULTS: Dict[str, Any] = {
    "detection": {
        "device": "0",
        "imgsz": 640,
        "predict_conf": 0.25,
        "low_confidence_cutoff": 0.6,
        "listen_interval_sec": 1.0,
        "loop_sleep_sec": 0.05,
    },
    "retrain": {
        "min_labeled_images": 0,
        "min_label_instances": 0,
    },
}

_cfg_cache: Dict[str, Any] | None = None


def project_root() -> Path:
    # .../backend_*/active_learning/policy_config.py -> repo root
    return Path(__file__).resolve().parent.parent.parent


def policy_file_path() -> Path:
    override = os.getenv("ACTIVE_LEARNING_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    return project_root() / "config" / "active_learning.json"


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_active_learning_config(*, force_reload: bool = False) -> Dict[str, Any]:
    global _cfg_cache
    if _cfg_cache is not None and not force_reload:
        return _cfg_cache

    path = policy_file_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"Active learning config not found: {path}. "
            "Add config/active_learning.json at repo root, or set ACTIVE_LEARNING_CONFIG."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Config must be a JSON object: {path}")
    _cfg_cache = _deep_merge(_DEFAULTS, raw)
    return _cfg_cache


def get_detection_settings() -> Dict[str, Any]:
    cfg = load_active_learning_config()
    return dict(cfg["detection"])


def get_retrain_thresholds() -> tuple[int, int]:
    cfg = load_active_learning_config()
    r = cfg["retrain"]
    return max(0, int(r["min_labeled_images"])), max(0, int(r["min_label_instances"]))
