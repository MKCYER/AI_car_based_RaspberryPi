from utils.torch_utils import select_device, time_sync
from utils.plots import Annotator, colors, save_one_box
from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.dataloaders1 import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from models.common import DetectMultiBackend
import argparse
import os
import sys
from pathlib import Path

import torch
import torch.backends.cudnn as cudnn

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative


class FireDetection:
    def __init__(self):
        self.weights = 'best.onnx'  # model.pt path(s)
        self.source = 'data/images'  # file/dir/URL/glob, 0 for webcam
        self.data = 'data/coco128.yaml'  # dataset.yaml path
        self.imgsz = (640, 640)  # inference size (height, width)
        self.conf_thres = 0.25  # confidence threshold
        self.iou_thres = 0.45  # NMS IOU threshold
        self.max_det = 1000  # maximum detections per image
        self.device = 'cpu'  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        self.view_img = False  # show results
        self.save_txt = False  # save results to *.txt
        self.save_conf = False  # save confidences in --save-txt labels
        self.save_crop = False  # save cropped prediction boxes

        self.nosave = False  # do not save images/videos
        self.classes = None  # filter by class: --class 0, or --class 0 2 3
        self.agnostic_nms = False  # class-agnostic NMS
        self.augment = False  # augmented inference
        self.visualize = False  # visualize features
        self.update = False  # update all models
        self.project = 'runs/detect'  # save results to project/name
        self.name = 'exp'  # save results to project/name
        self.exist_ok = False  # existing project/name ok, do not increment
        self.line_thickness = 3  # bounding box thickness (pixels)
        self.hide_labels = False  # hide labels
        self.hide_conf = False  # hide confidences
        self.half = False  # use FP16 half-precision inference
        self.dnn = False  # use OpenCV DNN for ONNX inference
        self.device = select_device(self.device)
        self.model = DetectMultiBackend(
            self.weights, device=self.device, dnn=self.dnn, data=self.data, fp16=self.half)
        self.stride, self.names, self.pt = self.model.stride, self.model.names, self.model.pt
        self.imgsz = check_img_size(self.imgsz, s=self.stride)

    def detect(self, img):
        path, im, im0s, vid_cap, s = LoadImages(
            img, img_size=self.imgsz, stride=self.stride, auto=self.pt).get(img)
        self.model.warmup(
            imgsz=(1 if self.pt else 1, 3, *self.imgsz))  # warmup
        dt, seen = [0.0, 0.0, 0.0], 0
        t1 = time_sync()
        im = torch.from_numpy(im).to(self.device)
        im = im.half() if self.model.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        t2 = time_sync()
        dt[0] += t2 - t1

        # Inference
        pred = self.model(im, augment=self.augment, visualize=False)
        t3 = time_sync()
        dt[1] += t3 - t2

        # NMS
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres,
                                   self.classes, self.agnostic_nms, max_det=self.max_det)
        dt[2] += time_sync() - t3
        # Second-stage classifier (optional)
        # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

        # Process predictions
        for i, det in enumerate(pred):  # per image
            seen += 1
            im0 = im0s.copy()
            # print(det.shape)
            s += '%gx%g ' % im.shape[2:]  # print string
            # normalization gain whwh
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]
            imc = im0.copy()  # for save_crop
            annotator = Annotator(
                im0, line_width=self.line_thickness, example=str(self.names))
            dt = []
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(
                    im.shape[2:], det[:, :4], im0.shape).round()
                save_img = not self.nosave and not self.source.endswith(
                    '.txt')  # save inference images
                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    # add to string
                    identification = f"{n} {self.names[int(c)]}{'s' * (n > 1)}, "
                    s += identification
                    # if "fire" in identification:
                    #     dt.append(identification)
                # Write results
                for *xyxy, conf, cls in reversed(det):
                    # print(conf, cls)
                    if cls == 0 and conf > 0.55:
                        dt.append(conf)
                    if self.save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)
                                          ) / gn).view(-1).tolist()  # normalized xywh
                        # label format
                        line = (
                            cls, *xywh, conf) if self.save_conf else (cls, *xywh)
                        with open(f'1.txt', 'a') as f:
                            f.write(('%g ' * len(line)).rstrip() % line + '\n')

                    if save_img or self.save_crop or self.view_img:  # Add bbox to image
                        c = int(cls)  # integer class
                        label = None if self.hide_labels else (
                            self.names[c] if self.hide_conf else f'{self.names[c]} {conf:.2f}')
                        annotator.box_label(xyxy, label, color=colors(c, True))
                    # if self.save_crop:
                    #     save_one_box(xyxy, imc, file='run' / 'crops' / self.names[c] / f'{p.stem}.jpg', BGR=True)
        fire = False
        # print(dt)
        if len(dt) >= 1:
            fire = True
        im0 = annotator.result()
        return im0, fire


model = FireDetection()

if __name__ == '__main__':
    img, _ = model.detect(cv2.imread("1.jpg"))
    cv2.imshow("keke", img)
    cv2.waitKey(0)
