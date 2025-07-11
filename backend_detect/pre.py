import os
import shutil
import random
import xml.etree.ElementTree as ET

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))  # 项目根目录

def convert_annotation(xml_path, txt_path, class_names):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size_node = root.find('size')
    width = int(size_node.find('width').text)
    height = int(size_node.find('height').text)

    with open(txt_path, 'w') as f:
        for obj in root.iter('object'):
            cls_name = obj.find('name').text
            if cls_name not in class_names:
                print(f"警告: 类别 {cls_name} 不在 class_names 中，跳过")
                continue
            cls_id = class_names.index(cls_name)

            xml_box = obj.find('bndbox')
            xmin = int(xml_box.find('xmin').text)
            ymin = int(xml_box.find('ymin').text)
            xmax = int(xml_box.find('xmax').text)
            ymax = int(xml_box.find('ymax').text)

            # 归一化
            x_center = (xmin + xmax) / 2.0 / width
            y_center = (ymin + ymax) / 2.0 / height
            w = (xmax - xmin) / width
            h = (ymax - ymin) / height

            f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")


def batch_convert(xml_root_dir, save_root_dir, class_names):
    if os.path.exists(save_root_dir):
        pass
    else:
        print(f"路径不存在: {save_root_dir}")
        for subdir, _, files in os.walk(xml_root_dir):
            for file in files:
                if file.endswith('.xml'):
                    xml_path = os.path.join(subdir, file)

                    # 构造对应 save 路径
                    relative_path = os.path.relpath(xml_path, xml_root_dir)
                    txt_path = os.path.join(save_root_dir, relative_path)
                    txt_path = txt_path.replace('.xml', '.txt')

                    # 确保保存目录存在
                    os.makedirs(os.path.dirname(txt_path), exist_ok=True)

                    # 转换
                    convert_annotation(xml_path, txt_path, class_names)

        print(f"全部转换完成！YOLO 标注已保存到: {save_root_dir}")

def split_dataset(
        target_data_set: str = 'BJ-PCB',
        annotation_name: str = 'labels',
        image_name: str = 'images',
        train_ratio: float = 0.8,
        next_train: bool = False,
):
    if next_train is False:
        # 路径信息
        root_dir = os.path.join(BASE_DIR, "datasets", "raw", target_data_set)
        # root_dir = f'./datasets/raw/{target_data_set}'
        annotation_dir = os.path.join(root_dir, annotation_name)
        image_dir = os.path.join(root_dir, image_name)
        output_root = os.path.join(BASE_DIR, "datasets", target_data_set)
        # output_root = f'./datasets/{target_data_set}'
    else:
        root_dir = os.path.join(BASE_DIR, "datasets", "raw", target_data_set)
        # root_dir = f'../datasets/raw/{target_data_set}'
        annotation_dir = os.path.join(root_dir, annotation_name)
        image_dir = os.path.join(root_dir, image_name)
        output_root = os.path.join(BASE_DIR, "datasets", target_data_set)
        # output_root = f'../datasets/{target_data_set}'
        if os.path.exists(output_root):
            shutil.rmtree(output_root)

    if os.path.exists(output_root):
        print('检测到数据集')
        pass
    else:
        # 输出路径
        train_anno_dir = os.path.join(output_root, 'train', annotation_name)
        train_img_dir = os.path.join(output_root, 'train', image_name)
        val_anno_dir = os.path.join(output_root, 'val', annotation_name)
        val_img_dir = os.path.join(output_root, 'val', image_name)

        # 创建输出目录
        for d in [train_anno_dir, train_img_dir, val_anno_dir, val_img_dir]:
            os.makedirs(d, exist_ok=True)

        # 获取缺陷类型
        possible_defects = [f for f in os.listdir(annotation_dir) if os.path.isdir(os.path.join(annotation_dir, f))]

        if possible_defects:
            for defect in possible_defects:
                anno_path = os.path.join(annotation_dir, defect)
                img_path = os.path.join(image_dir, defect)

                annos = os.listdir(anno_path)
                random.shuffle(annos)

                split_idx = int(len(annos) * train_ratio)
                train_annos = annos[:split_idx]
                val_annos = annos[split_idx:]

                # 创建子目录
                os.makedirs(os.path.join(train_anno_dir, defect), exist_ok=True)
                os.makedirs(os.path.join(train_img_dir, defect), exist_ok=True)
                os.makedirs(os.path.join(val_anno_dir, defect), exist_ok=True)
                os.makedirs(os.path.join(val_img_dir, defect), exist_ok=True)

                # 移动文件
                for anno in train_annos:
                    img = anno.replace('.txt', '.jpg')
                    shutil.copy(os.path.join(anno_path, anno), os.path.join(train_anno_dir, defect, anno))
                    shutil.copy(os.path.join(img_path, img), os.path.join(train_img_dir, defect, img))

                for anno in val_annos:
                    img = anno.replace('.txt', '.jpg')
                    shutil.copy(os.path.join(anno_path, anno), os.path.join(val_anno_dir, defect, anno))
                    shutil.copy(os.path.join(img_path, img), os.path.join(val_img_dir, defect, img))

        else:
            # 无缺陷类型子目录
            annos = [f for f in os.listdir(annotation_dir) if f.endswith('.txt')]
            random.shuffle(annos)

            split_idx = int(len(annos) * train_ratio)
            train_annos = annos[:split_idx]
            val_annos = annos[split_idx:]

            # 移动文件
            for anno in train_annos:
                img = anno.replace('.txt', '.jpg')
                shutil.copy(os.path.join(annotation_dir, anno), os.path.join(train_anno_dir, anno))
                shutil.copy(os.path.join(image_dir, img), os.path.join(train_img_dir, img))

            for anno in val_annos:
                img = anno.replace('.txt', '.jpg')
                shutil.copy(os.path.join(annotation_dir, anno), os.path.join(val_anno_dir, anno))
                shutil.copy(os.path.join(image_dir, img), os.path.join(val_img_dir, img))

        print("数据集划分完成")
