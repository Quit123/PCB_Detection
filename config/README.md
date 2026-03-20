# `active_learning.json`

- **`detection`**: used by `backend_detect/active_learning/active_learning.py` (listen folder, YOLO `predict`, low-confidence cutoff).
- **`retrain`**: used by both backends before packaging/training (`/api/managing-data`, `/api/managing-training`). Set `min_labeled_images` and/or `min_label_instances` to positive values to require that many **paired** label+image samples and/or total YOLO label lines before retraining.

Override path: environment variable `ACTIVE_LEARNING_CONFIG` (absolute or relative path to your JSON).
