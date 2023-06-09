from torchvision import transforms, datasets
import numpy as np
import torch
from torch import nn

np.random.seed(0)

class GaussianBlur(object):
    """blur a single image on CPU"""
    def __init__(self, kernel_size):
        radias = kernel_size // 2
        kernel_size = radias * 2 + 1
        self.blur_h = nn.Conv2d(1, 1, kernel_size=(kernel_size, 1),
                                stride=1, padding=0, bias=False, groups=1)
        self.blur_v = nn.Conv2d(1, 1, kernel_size=(1, kernel_size),
                                stride=1, padding=0, bias=False, groups=1)
        self.k = kernel_size
        self.r = radias

        self.blur = nn.Sequential(
            nn.ReflectionPad2d(radias),
            self.blur_h,
            self.blur_v
        )

    def __call__(self, img):

        sigma = np.random.uniform(0.1, 2.0)
        x = np.arange(-self.r, self.r + 1)
        x = np.exp(-np.power(x, 2) / (2 * sigma * sigma))
        x = x / x.sum()
        x = torch.from_numpy(x).view(1, -1)

        self.blur_h.weight.data.copy_(x.view(1, 1, self.k, 1))
        self.blur_v.weight.data.copy_(x.view(1, 1, 1, self.k))

        with torch.no_grad():
            img = self.blur(img)

        return img

def get_simclr_pipeline_transform(size):
    """Return a set of data augmentation transformations as described in the SimCLR paper."""
    color_jitter = transforms.ColorJitter(brightness=0.8, contrast=0, saturation=0, hue=0.2)   #明亮程度、对比度、饱和色调度、色调偏移程度
    data_transforms = transforms.Compose([transforms.RandomResizedCrop(size=(size, size)),              #将PIL图像裁剪成任意大小和纵横比
                                          transforms.RandomHorizontalFlip(),                        #以0.5的概率水平翻转给定的PIL图像
                                          #transforms.RandomApply([color_jitter], p=0.8),
                                          #transforms.GaussianBlur(kernel_size=int(0.1 * size) if int(0.1 * size) % 2 else int(0.1*size) - 1),                #高斯滤波是应用于图像处理，对图像进行滤波操作（平滑操作、过滤操作，去噪操作
                                          ])
    return data_transforms

def random_crop(imgs, output_size):
    """
    Vectorized way to do random crop using sliding windows
    and picking out random ones

    args:
        imgs, batch images with shape (B,C,H,W)
    """
    # batch size
    n = imgs.shape[0]
    img_size = imgs.shape[-1]
    crop_max = img_size - output_size
    imgs = np.transpose(imgs, (0, 2, 3, 1))
    w1 = np.random.randint(0, crop_max, n)
    h1 = np.random.randint(0, crop_max, n)
    # creates all sliding windows combinations of size (output_size)
    windows = view_as_windows(
        imgs, (1, output_size, output_size, 1))[..., 0,:,:, 0]
    # selects a random window for each batch element
    cropped_imgs = windows[np.arange(n), w1, h1]
    return cropped_imgs

def center_crop_image(image, output_size):
    h, w = image.shape[1:]
    new_h, new_w = output_size, output_size

    top = (h - new_h)//2
    left = (w - new_w)//2

    image = image[:, top:top + new_h, left:left + new_w]
    return image

