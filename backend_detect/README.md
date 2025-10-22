## Directory Structure

The dataset organization for this project is shown below, designed for the **BJ-PCB defect detection** task：

```plaintext
active_learning/
├── low_conf_images/                   # Stores low-confidence detection images and related annotations
│   ├── labels/                        # Label files annotated via Label Studio
│   ├── marked/                        # Low-confidence images annotated by the model
│   ├── raw/                           # Original low-confidence images (before model detection)
│   └── temp/                          # Temporary folder / staging area
├── target/                            # Stores incoming PCB images
├── active_learning.py                 # Main script for detection and filtering of low-confidence samples
├── management.py                      # Data management script (image transfer and preprocessing)
├── next_train.yaml                    # Configuration file for the next training iteration
├── simulate_push.py                   # Script for simulating data push
└── train.py                           # Model training script (for testing purposes)


```
