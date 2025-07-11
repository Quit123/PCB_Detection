from ultralytics.models import YOLO
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

if __name__ == '__main__':
    model = YOLO(model='./runs/train/official_exp/weights/best.pt')
    model.val(data='./data.yaml', split='val', batch=1, device='0', project='run/val', name='exp',
              half=False, )
