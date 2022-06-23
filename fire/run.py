import torch
import torchvision
#from openvino.inference_engine import IECore, IENetwork
import cv2
import numpy as np
import time
import os

# 推断
def Inference(net, exec_net, image_file):
    # Read image
    img0 = cv2.imread(image_file)
    print("img0 Size:", img0.shape)
    # Padded resize
    img = cv2.resize(img0, (640, 640))
    print("img Size:", img.shape)
    # Convert
    img = img.transpose((2, 0, 1))[::-1] # HWC to CHW, BGR to RGB
    img = np.ascontiguousarray(img)
    img = torch.from_numpy(img)
    img = img.half()
    img = img[None]
    
    '''
    # 模型输入图片，进行推理
    n, c, h, w = net.inputs[input_blob].shape
    frame = cv2.imread(image_file)
    initial_h, initial_w, channels = frame.shape
    # 按照AI模型要求放缩图片
    
    image = cv2.resize(frame, (w, h))
    image = torch.from_numpy(image)
    # 下面这两步特别关键！！！！不这么处理推断结果就会出大错！！
    image = image.half()
    
    image = image[None]
    image = image.transpose(1, 3)
    image = image.transpose(2, 3)
    '''

    print("image shape is: {}".format(img.shape))
    print("Starting inference in synchronous mode")
    start = time.time()
    res = exec_net.infer(inputs={input_blob: img})
    end = time.time()
    print("Infer Time:{}ms".format((end - start) * 1000))
    #return torch.from_numpy(res[out_blob])  # res.shape = [1, 25200, 8]
    return torch.from_numpy(res['output'])
    #return res

def xywh2xyxy(x):
    # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
    y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
    return y

def non_max_suppression(prediction, conf_thres=0.25, iou_thres=0.45, classes=None, agnostic=False, multi_label=False,
                        labels=(), max_det=300):
    """Runs Non-Maximum Suppression (NMS) on inference results

    Returns:
         list of detections, on (n,6) tensor per image [xyxy, conf, cls]
    """

    nc = prediction.shape[2] - 5  # number of classes
    xc = prediction[..., 4] > conf_thres  # candidates

    # Checks
    assert 0 <= conf_thres <= 1, f'Invalid Confidence threshold {conf_thres}, valid values are between 0.0 and 1.0'
    assert 0 <= iou_thres <= 1, f'Invalid IoU {iou_thres}, valid values are between 0.0 and 1.0'

    # Settings
    min_wh, max_wh = 2, 4096  # (pixels) minimum and maximum box width and height
    max_nms = 30000  # maximum number of boxes into torchvision.ops.nms()
    time_limit = 10.0  # seconds to quit after
    redundant = True  # require redundant detections
    multi_label &= nc > 1  # multiple labels per box (adds 0.5ms/img)
    merge = False  # use merge-NMS

    t = time.time()
    output = [torch.zeros((0, 6), device=prediction.device)] * prediction.shape[0]
    for xi, x in enumerate(prediction):  # image index, image inference
        # Apply constraints
        # x[((x[..., 2:4] < min_wh) | (x[..., 2:4] > max_wh)).any(1), 4] = 0  # width-height
        x = x[xc[xi]]  # confidence
        print("---x shape---:", x.shape)
        # Cat apriori labels if autolabelling
        if labels and len(labels[xi]):
            l = labels[xi]
            v = torch.zeros((len(l), nc + 5), device=x.device)
            v[:, :4] = l[:, 1:5]  # box
            v[:, 4] = 1.0  # conf
            v[range(len(l)), l[:, 0].long() + 5] = 1.0  # cls
            x = torch.cat((x, v), 0)

        # If none remain process next image
        if not x.shape[0]:
            continue

        # Compute conf
        x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

        # Box (center x, center y, width, height) to (x1, y1, x2, y2)
        box = xywh2xyxy(x[:, :4])

        # Detections matrix nx6 (xyxy, conf, cls)
        if multi_label:
            i, j = (x[:, 5:] > conf_thres).nonzero(as_tuple=False).T
            x = torch.cat((box[i], x[i, j + 5, None], j[:, None].float()), 1)
        else:  # best class only
            conf, j = x[:, 5:].max(1, keepdim=True)
            x = torch.cat((box, conf, j.float()), 1)[conf.view(-1) > conf_thres]

        # Filter by class
        if classes is not None:
            x = x[(x[:, 5:6] == torch.tensor(classes, device=x.device)).any(1)]

        # Apply finite constraint
        # if not torch.isfinite(x).all():
        #     x = x[torch.isfinite(x).all(1)]

        # Check shape
        n = x.shape[0]  # number of boxes
        if not n:  # no boxes
            continue
        elif n > max_nms:  # excess boxes
            x = x[x[:, 4].argsort(descending=True)[:max_nms]]  # sort by confidence

        # Batched NMS
        c = x[:, 5:6] * (0 if agnostic else max_wh)  # classes
        boxes, scores = x[:, :4] + c, x[:, 4]  # boxes (offset by class), scores
        i = torchvision.ops.nms(boxes, scores, iou_thres)  # NMS
        if i.shape[0] > max_det:  # limit detections
            i = i[:max_det]
        if merge and (1 < n < 3E3):  # Merge NMS (boxes merged using weighted mean)
            # update boxes as boxes(i,4) = weights(i,n) * boxes(n,4)
            iou = box_iou(boxes[i], boxes) > iou_thres  # iou matrix
            weights = iou * scores[None]  # box weights
            x[i, :4] = torch.mm(weights, x[:, :4]).float() / weights.sum(1, keepdim=True)  # merged boxes
            if redundant:
                i = i[iou.sum(1) > 1]  # require redundancy

        output[xi] = x[i]
        if (time.time() - t) > time_limit:
            print(f'WARNING: NMS time limit {time_limit}s exceeded')
            break  # time limit exceeded

    return output

def classify(image):
    model_xml = '/home/pi/MyCode/MyModel/9.10best.fp16.s255.xml'
    model_bin = '/home/pi/MyCode/MyModel/9.10best.fp16.s255.bin'
    confidence = 0.6
    num_classes = 4
    conf_thres, iou_thres = 0.25, 0.45
    classes = None
    agnostic_nms = False
    max_det = 300
    # 初始化设备
    ie = IECore()
    # 读取IR模型
    net = ie.read_network(model=model_xml, weights=model_bin)
    # 转换输入输出张量
    input_blob = next(iter(net.inputs))
    out_blob = next(iter(net.outputs))
    # 载入模型到CPU
    exec_net = ie.load_network(network=net, num_requests=1, device_name=DEVICE)
    # 推断
    prediction = Inference(net, exec_net, image)
    ans = non_max_suppression(prediction, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
    cls_id = ans[0][:,-1].unique()
    return cls_id

def run():
    DEVICE = 'MYRIAD'
    #model_xml = '/home/pi/MyCode/best.fp16.s255.xml'
    #model_bin = '/home/pi/MyCode/best.fp16.s255.bin'
    model_xml = '/home/pi/MyCode/MyModel/9.10best.fp16.s255.xml'
    model_bin = '/home/pi/MyCode/MyModel/9.10best.fp16.s255.bin'
    #model_xml = '/home/pi/newYolov5/yolov5s.xml'
    #model_bin = '/home/pi/newYolov5/yolov5s.bin'
    image_file = '/home/pi/MyCode/testdata'
    confidence = 0.6
    num_classes = 4
    conf_thres, iou_thres = 0.25, 0.45
    classes = None
    agnostic_nms = False
    max_det = 300
    # 初始化设备
    ie = IECore()
    # 读取IR模型
    net = ie.read_network(model=model_xml, weights=model_bin)
    # 转换输入输出张量
    print("Preparing input blobs")
    input_blob = next(iter(net.inputs))
    out_blob = next(iter(net.outputs))
    # 载入模型到CPU
    print("Loading IR to the plugin...")
    exec_net = ie.load_network(network=net, num_requests=1, device_name=DEVICE)
    # 推断
    print("Start Inference!")
    pic_list = os.listdir(image_file)
    for pic in pic_list:
        prediction = Inference(net, exec_net, image_file+'/'+pic)
        print("****prediction's shape is:******", prediction.shape)
        # print(prediction)
        ans = non_max_suppression(prediction, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
        cls_id = ans[0][:,-1].unique()
        print(pic, "\n", cls_id)
        '''
        with open('9.10ModelTest.txt', 'a') as f:
            if(cls_id.shape[0]==0):
                f.write(pic+": None" + '\n')
            else:
                f.write(pic+": "+str(int(cls_id[0])) + '\n')
        '''    
if __name__ == "__main__":
    video = cv2.VideoCapture("http://127.0.0.1:8080/?action=stream")
    video.set( cv2.CAP_PROP_FRAME_WIDTH, 620 )
    fps = video.get(cv2.CAP_PROP_FPS)
    print(fps)
    size = (int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    print(size)
    while True:
        ret, frame = video.read()
        cv2.imshow("A video", frame)
        c = cv2.waitKey(1)
        if c == 27:
            break
    video.release()
    cv2.destroyAllWindows()