---
title: 如何使用PyTorch
date: 2026-08-01
tags: [人工智能, 技术]
excerpt: 入门学习PyTorch框架基础
---

# 入门学习PyTorch框架基础

本文内容来自[PyTorch官方文档](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)、[PyTorch 教程 | 菜鸟教程](https://www.runoob.com/pytorch/pytorch-tutorial.html)，意在详细介绍PyTorch的完整工作流及其附带内容。

本文不会深入的介绍关于深度学习的基础知识，相关内容参见我的另一篇文章[深度学习基础 ](https://ling-nine.github.io/posts/About_deep_learning.html)。

------

## PyToch 基础

PyTorch 是一个开源的深度学习框架，以其灵活性和动态计算图而广受欢迎。

PyTorch 主要有以下几个基础概念：张量（Tensor）、自动求导（Autograd）、神经网络模块（nn.Module）、优化器（optim）等。

- **张量（Tensor）**：PyTorch 的核心数据结构，支持多维数组，并可以在 CPU 或 GPU 上进行加速计算。
- **自动求导（Autograd）**：PyTorch 提供了自动求导功能，可以轻松计算模型的梯度，便于进行反向传播和优化。
- **神经网络（nn.Module）**：PyTorch 提供了简单且强大的 API 来构建神经网络模型，可以方便地进行前向传播和模型定义。
- **优化器（Optimizers）**：使用优化器（如 Adam、SGD 等）来更新模型的参数，使得损失最小化。
- **设备（Device）**：可以将模型和张量移动到 GPU 上以加速计算。

------

## PyTorch 架构总览

PyTorch 采用模块化设计，由多个相互协作的核心组件构成。理解这些组件的作用和相互关系，是掌握 PyTorch 的关键。

### PyTorch 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    PyTorch 生态系统                          │
├─────────────────────────────────────────────────────────────┤
│  torchvision  │  torchtext  │  torchaudio  │  其他专业库     │
├─────────────────────────────────────────────────────────────┤
│                     PyTorch 核心                            │
├───────────────┬─────────────────┬───────────────────────────┤
│   torch.nn    │   torch.optim   │      torch.utils          │
│   (神经网络)   │   (优化器)      │      (工具函数)            │
├───────────────┼─────────────────┼───────────────────────────┤
│   torch 核心  │    autograd     │   torch.utils.data        │
│   (张量计算)   │   (自动微分)    │   (数据加载)               │
└───────────────┴─────────────────┴───────────────────────────┘
```

------

## 张量

张量是一个多维数组，可以是标量、向量、矩阵或更高维度的数据结构。

在 PyTorch 中，张量（Tensor）是数据的核心表示形式，类似于 NumPy 的多维数组，但具有更强大的功能，例如支持 GPU 加速和自动梯度计算。

#### 创建张量

可以通过多种方式初始化张量。

```python
import torch
import numpy as np

# 直接从数据创建
data = [[1, 2],[3, 4]]
x_data = torch.tensor(data)

# 从 NumPy 数组创建
np_array = np.array(data)
x_np = torch.from_numpy(np_array)

# 从另一个张量创建
x_ones = torch.ones_like(x_data) # 保留 x_data 的属性
print(f"Ones Tensor: \n {x_ones} \n")

x_rand = torch.rand_like(x_data, dtype=torch.float) # 覆盖 x_data 的数据类型
print(f"Random Tensor: \n {x_rand} \n")
```
输出
```python
Ones Tensor:
 tensor([[1, 1],
        [1, 1]])
Random Tensor:
 tensor([[0.3789, 0.9786],
        [0.2249, 0.3116]])
```
```python
# 使用随机或常量值创建
shape = (2,3) # 代表张量的维度。在下面的函数中，它决定了输出张量的维度。
rand_tensor = torch.rand(shape)
ones_tensor = torch.ones(shape)
zeros_tensor = torch.zeros(shape)

print(f"Random Tensor: \n {rand_tensor} \n")
print(f"Ones Tensor: \n {ones_tensor} \n")
print(f"Zeros Tensor: \n {zeros_tensor}")
```
输出
```python
Random Tensor:
 tensor([[0.0530, 0.3384, 0.6637],
        [0.8872, 0.5051, 0.0376]])

Ones Tensor:
 tensor([[1., 1., 1.],
        [1., 1., 1.]])

Zeros Tensor:
 tensor([[0., 0., 0.],
        [0., 0., 0.]])
```

张量创建的方式有：

| **方法**                            | **说明**                                               | **示例代码**                                |
| ----------------------------------- | ------------------------------------------------------ | ------------------------------------------- |
| `torch.tensor(data)`                | 从 Python 列表或 NumPy 数组创建张量。                  | `x = torch.tensor([[1, 2], [3, 4]])`        |
| `torch.zeros(size)`                 | 创建一个全为零的张量。                                 | `x = torch.zeros((2, 3))`                   |
| `torch.ones(size)`                  | 创建一个全为 1 的张量。                                | `x = torch.ones((2, 3))`                    |
| `torch.empty(size)`                 | 创建一个未初始化的张量。                               | `x = torch.empty((2, 3))`                   |
| `torch.rand(size)`                  | 创建一个服从均匀分布的随机张量，值在 `[0, 1)`。        | `x = torch.rand((2, 3))`                    |
| `torch.randn(size)`                 | 创建一个服从正态分布的随机张量，均值为 0，标准差为 1。 | `x = torch.randn((2, 3))`                   |
| `torch.arange(start, end, step)`    | 创建一个一维序列张量，类似于 Python 的 `range`。       | `x = torch.arange(0, 10, 2)`                |
| `torch.linspace(start, end, steps)` | 创建一个在指定范围内等间隔的序列张量。                 | `x = torch.linspace(0, 1, 5)`               |
| `torch.eye(size)`                   | 创建一个单位矩阵（对角线为 1，其他为 0）。             | `x = torch.eye(3)`                          |
| `torch.from_numpy(ndarray)`         | 将 NumPy 数组转换为张量。                              | `x = torch.from_numpy(np.array([1, 2, 3]))` |

#### 张量的属性

张量属性描述了其形状、数据类型以及存储它的设备。

```python
tensor = torch.rand(3,4)

print(f"Shape of tensor: {tensor.shape}")
print(f"Datatype of tensor: {tensor.dtype}")
print(f"Device tensor is stored on: {tensor.device}")
```
输出
```python
Shape of tensor: torch.Size([3, 4])
Datatype of tensor: torch.float32
Device tensor is stored on: cpu
```

张量的属性如下表：

| **属性**           | **说明**                         | **示例**                 |
| ------------------ | -------------------------------- | ------------------------ |
| `.shape`           | 获取张量的形状                   | `tensor.shape`           |
| `.size()`          | 获取张量的形状                   | `tensor.size()`          |
| `.dtype`           | 获取张量的数据类型               | `tensor.dtype`           |
| `.device`          | 查看张量所在的设备 (CPU/GPU)     | `tensor.device`          |
| `.dim()`           | 获取张量的维度数                 | `tensor.dim()`           |
| `.requires_grad`   | 是否启用梯度计算                 | `tensor.requires_grad`   |
| `.numel()`         | 获取张量中的元素总数             | `tensor.numel()`         |
| `.is_cuda`         | 检查张量是否在 GPU 上            | `tensor.is_cuda`         |
| `.T`               | 获取张量的转置（适用于 2D 张量） | `tensor.T`               |
| `.item()`          | 获取单元素张量的值               | `tensor.item()`          |
| `.is_contiguous()` | 检查张量是否连续存储             | `tensor.is_contiguous()` |

#### 张量运算

如果你熟悉 NumPy API，你会发现 Tensor API 用起来非常轻松。

```python
# 标准的类似 numpy 的索引和切片
tensor = torch.ones(4, 4)
print(f"First row: {tensor[0]}")
print(f"First column: {tensor[:, 0]}")
print(f"Last column: {tensor[..., -1]}")
tensor[:,1] = 0
print(tensor)
```
输出
```python
First row: tensor([1., 1., 1., 1.])
First column: tensor([1., 1., 1., 1.])
Last column: tensor([1., 1., 1., 1.])
tensor([[1., 0., 1., 1.],
        [1., 0., 1., 1.],
        [1., 0., 1., 1.],
        [1., 0., 1., 1.]])
```

算数运算

```python
# 这计算了两个张量之间的矩阵乘法。y1、y2、y3 将具有相同的值。
y1 = tensor @ tensor.T
y2 = tensor.matmul(tensor.T)

y3 = torch.rand_like(y1)
torch.matmul(tensor, tensor.T, out=y3)


# 这将计算逐元素相乘。z1、z2、z3 的值将相同
z1 = tensor * tensor
z2 = tensor.mul(tensor)

z3 = torch.rand_like(tensor)
torch.mul(tensor, tensor, out=z3)
```

张量操作方法说明如下：

| **操作**                | **说明**                       | **示例代码**                  |
| ----------------------- | ------------------------------ | ----------------------------- |
| `+`, `-`, `*`, `/`      | 元素级加法、减法、乘法、除法。 | `z = x + y`                   |
| `torch.matmul(x, y)`    | 矩阵乘法。                     | `z = torch.matmul(x, y)`      |
| `torch.dot(x, y)`       | 向量点积（仅适用于 1D 张量）。 | `z = torch.dot(x, y)`         |
| `torch.sum(x)`          | 求和。                         | `z = torch.sum(x)`            |
| `torch.mean(x)`         | 求均值。                       | `z = torch.mean(x)`           |
| `torch.max(x)`          | 求最大值。                     | `z = torch.max(x)`            |
| `torch.min(x)`          | 求最小值。                     | `z = torch.min(x)`            |
| `torch.argmax(x, dim)`  | 返回最大值的索引（指定维度）。 | `z = torch.argmax(x, dim=1)`  |
| `torch.softmax(x, dim)` | 计算 softmax（指定维度）。     | `z = torch.softmax(x, dim=1)` |

形状操作：

| **操作**                 | **说明**                       | **示例代码**                   |
| ------------------------ | ------------------------------ | ------------------------------ |
| `x.view(shape)`          | 改变张量的形状（不改变数据）。 | `z = x.view(3, 4)`             |
| `x.reshape(shape)`       | 类似于 `view`，但更灵活。      | `z = x.reshape(3, 4)`          |
| `x.t()`                  | 转置矩阵。                     | `z = x.t()`                    |
| `x.unsqueeze(dim)`       | 在指定维度添加一个维度。       | `z = x.unsqueeze(0)`           |
| `x.squeeze(dim)`         | 去掉指定维度为 1 的维度。      | `z = x.squeeze(0)`             |
| `torch.cat((x, y), dim)` | 按指定维度连接多个张量。       | `z = torch.cat((x, y), dim=1)` |

#### 原地操作 (In-place operations)

将结果存储在操作数中的操作称为“原地”操作。它们以 `_` 后缀表示。例如：`x.copy_(y)` 或 `x.t_()` 将会改变 `x`

```python
print(f"{tensor} \n")
tensor.add_(5)
print(tensor)
```
输出
```python
tensor([[1., 0., 1., 1.],
        [1., 0., 1., 1.],
        [1., 0., 1., 1.],
        [1., 0., 1., 1.]])

tensor([[6., 5., 6., 6.],
        [6., 5., 6., 6.],
        [6., 5., 6., 6.],
        [6., 5., 6., 6.]])
```

#### 与NumPy的交互

张量与 NumPy 的互操作如下表所示：

| **操作**                    | **说明**                                   | **示例代码**                     |
| --------------------------- | ------------------------------------------ | -------------------------------- |
| `torch.from_numpy(ndarray)` | 将 NumPy 数组转换为张量。                  | `x = torch.from_numpy(np_array)` |
| `x.numpy()`                 | 将张量转换为 NumPy 数组（仅限 CPU 张量）。 | `np_array = x.numpy()`           |

------

## 数据集

处理数据样本的代码往往会变得杂乱且难以维护；理想情况下，我们希望将数据集代码与模型训练代码解耦，以获得更好的可读性和模块化。PyTorch 提供了强大的数据加载和处理工具，主要包括：

- **torch.utils.data.Dataset**：数据集的抽象类，需要自定义并实现 `__len__`（数据集大小）和 `__getitem__`（按索引获取样本）。
- **torch.utils.data.TensorDataset**：基于张量的数据集，适合处理数据-标签对，直接支持批处理和迭代。
- **torch.utils.data.DataLoader**：封装 Dataset 的迭代器，提供批处理、数据打乱、多线程加载等功能，便于数据输入模型训练。
- **torchvision.datasets.ImageFolder**：从文件夹加载图像数据，每个子文件夹代表一个类别，适用于图像分类任务。

Dataset 是 PyTorch 中用于数据集抽象的类。

自定义数据集需要继承 torch.utils.data.Dataset 并重写以下两个方法：

- `__len__`：返回数据集的大小。
- `__getitem__`：按索引获取一个数据样本及其标签。

实例

```python
import torch
from torch.utils.data import Dataset

# 自定义数据集
class MyDataset(Dataset):
    def __init__(self, data, labels):
        # 数据初始化
        self.data = data
        self.labels = labels

    def __len__(self):
        # 返回数据集大小
        return len(self.data)

    def __getitem__(self, idx):
        # 按索引返回数据和标签
        sample = self.data[idx]
        label = self.labels[idx]
        return sample, label

# 生成示例数据
data = torch.randn(100, 5)  # 100 个样本，每个样本有 5 个特征
labels = torch.randint(0, 2, (100,))  # 100 个标签，取值为 0 或 1

# 实例化数据集
dataset = MyDataset(data, labels)

# 测试数据集
print("数据集大小:", len(dataset))
print("第 0 个样本:", dataset[0])

```

输出结果如下：

```python
数据集大小: 100
第 0 个样本: (tensor([-0.2006,  0.7304, -1.3911, -0.4408,  1.1447]), tensor(0))
```

#### 数据集类型

PyTorch 支持两种不同类型的数据集：

- 映射式数据，

映射式数据集是上文实现了 `__getitem__()` 和 `__len__()` 协议的数据集，表示从（可能是非整数的）索引/键到数据样本的映射。

例如，当使用 `dataset[idx]` 访问此类数据集时，可以从磁盘上的文件夹中读取第 `idx` 张图像及其对应的标签。类似于python里的列表。

涉及映射式数据集的情况将根据 `DataLoader` 的 `shuffle` 参数自动构造顺序采样器或随机采样器。或者，用户可以使用 `sampler`参数来指定一个自定义 `Sampler`对象，该对象每次产生下一个要获取的索引/键。

- 迭代式数据集。

迭代式数据集是 `IterableDataset` 子类的实例，它实现了 `__iter__()` 协议，表示数据样本上的可迭代对象。这种类型的数据集特别适用于随机读取代价很高甚至无法实现的情况，以及分批大小取决于所获取数据的情况。

例如，当调用 `iter(dataset)` 时，此类数据集可以返回从数据库、远程服务器甚至实时生成的日志中读取的数据流。

对于迭代式数据集，数据加载顺序完全由用户定义的可迭代对象控制。这可以更轻松地实现块读取和动态分批大小（例如，每次产生一个已分批的样本）。

#### 数据处理

`Dataset` 存储样本及其对应的标签，也就是数据集，而 `DataLoader` 则在 `Dataset` 周围封装了一个可迭代对象。`DataLoader`构造函数最重要的参数是 `dataset`，它指定了要从中加载数据的数据集对象。

```python
import torch
from torch.utils.data import DataLoader
```

这些选项通过 `DataLoader`的构造函数参数进行配置，其函数签名如下：

```python
DataLoader(dataset, # 数据集
           batch_size=1, # 每个batch的样本数
           shuffle=False, # 是否随机打乱，防止模型记住样本顺序，RandonSampler
           sampler=None, # 自定义采样策略
           batch_sampler=None, # 自定义 batch 采样策略
           num_workers=0, # 子进程数量
           collate_fn=None, # 如何把一个 batch 的数据拼在一起，一般是堆叠 Tensor
           pin_memory=False, # 是否锁页内存，设为 True 让 CPU→GPU 拷贝更快
           drop_last=False, # 丢弃最后一个不完整的 batch
           timeout=0, # 等待子进程返回的超时时间
           worker_init_fn=None, # 每个子进程初始化函数
           *, # 之后的所有参数必须通过关键字传递，不能用位置传参，出于向后兼容的考量。
           prefetch_factor=2, # 每个子进程预取多少 batch
           persistent_workers=False # 子进程是否常驻
          )
```

实例

```python
# 实例化前面的数据集
dataset = MyDataset(data, labels)

# 实例化 DataLoader
dataloader = DataLoader(dataset, batch_size=10, shuffle=True, num_workers=0)

# 遍历 DataLoader
for batch_idx, (batch_data, batch_labels) in enumerate(dataloader):
    print(f"批次 {batch_idx + 1}")
    print("数据:", batch_data)
    print("标签:", batch_labels)
    if batch_idx == 2:  # 仅显示前 3 个批次
        break
```

输出结果如下：

```python
批次 1
数据: tensor([[ 0.4689,  0.6666, -1.0234,  0.8948,  0.4503],
        [ 0.0273, -0.4684, -0.7762,  0.7963,  0.2168],
        [ 1.0677, -0.3502, -0.9594, -1.1318, -0.2196],
        [-1.4989,  0.0267,  1.0405, -0.7284,  0.2335],
        [-0.5887, -0.4934,  1.6283,  1.4638,  0.0157],
        [-1.1047, -0.6550, -0.0381,  0.3617, -1.2792],
        [ 0.3592, -0.8264,  0.0231, -1.5508,  0.6833],
        [-0.6835,  0.6979,  0.9048, -0.4756,  0.3003],
        [ 1.1562, -0.4516, -1.2415,  0.2859,  0.5837],
        [ 0.7937,  1.5316, -0.6139,  0.7999,  0.5506]])
标签: tensor([0, 1, 1, 1, 1, 0, 1, 1, 0, 0])
批次 2
数据: tensor([[-0.0388, -0.3658,  0.8993, -1.5027,  1.0738],
        [-0.6182,  1.0684, -2.3049,  0.8338,  0.1363],
        [-0.5289,  0.1661, -0.0349,  0.2112,  1.4745],
        [-0.3304, -1.2114, -0.2982, -0.3006,  0.5252],
        [-1.4394, -0.3732,  1.0281,  0.5754,  1.0081],
        [ 0.8714, -0.1945, -0.2451, -0.2879, -2.0520],
        [ 0.0235,  0.4360,  0.1233,  0.0504,  0.5908],
        [ 0.5927,  0.1785, -0.9052, -0.9012,  0.8914],
        [ 0.4693,  0.5533, -0.1903,  0.0267,  0.4077],
        [-1.1683,  1.6699, -0.4846, -0.7404,  0.3370]])
标签: tensor([1, 1, 0, 1, 0, 1, 1, 0, 1, 1])
批次 3
数据: tensor([[ 0.2103, -0.7839,  1.4899,  2.2749, -0.7548],
        [-1.2836,  1.0025, -1.1162, -0.4261,  1.0690],
        [-0.7969,  1.0418, -0.7405,  0.8766,  0.2347],
        [-1.1071,  1.8560, -1.2979, -0.8364, -0.2925],
        [-1.0488,  0.4802, -0.6453,  0.2009,  0.5693],
        [ 0.8883,  0.4619, -0.2087,  0.2189, -0.3708],
        [-1.4578,  0.3629,  1.8282,  0.5353, -1.1783],
        [-1.2813,  0.5129, -0.4598, -0.2131, -1.2804],
        [ 1.7831,  1.1730, -0.2305, -0.6550,  0.1197],
        [-0.9384, -0.0483,  1.9626,  0.3342,  0.1700]])
标签: tensor([0, 0, 0, 1, 0, 1, 1, 1, 0, 1])
```

------

## 数据转换

数据并不总是以机器学习算法训练所需的最终处理形式出现。我们使用 **transforms（变换）** 来对数据进行一些操作，使其适合训练。

所有的 TorchVision 数据集都有两个参数——`transform`（用于修改特征）和 `target_transform`（用于修改标签）——它们接收包含变换逻辑的可调用对象。 ```torchvision.transforms```模块提供了多种开箱即用的常用变换。

对图像数据集应用转换，加载PyTorch自带的 MNIST 数据集，并应用转换。

```python
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

# 定义转换
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

# 加载数据集
train_dataset = datasets.MNIST(root='./data', train=True, transform=transform, download=True)

# 使用 DataLoader
train_loader = DataLoader(dataset=train_dataset, batch_size=32, shuffle=True)

# 查看转换后的数据
for images, labels in train_loader:
    print("图像张量大小:", images.size())  # [batch_size, 1, 128, 128]
    break
    
# 图像张量大小: torch.Size([32, 1, 128, 128])
```

基础变换操作:

| 变换函数名称                      | 描述                                                         | 实例                                                         |
| --------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `transforms.ToTensor()`           | 将PIL图像或NumPy数组转换为PyTorch张量，并自动将像素值归一化到 [0, 1]。 | `transform = transforms.ToTensor()`                          |
| `transforms.Normalize(mean, std)` | 对图像进行标准化，使数据符合零均值和单位方差。               | `transform = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])` |
| `transforms.Resize(size)`         | 调整图像尺寸，确保输入到网络的图像大小一致。                 | `transform = transforms.Resize((256, 256))`                  |
| `transforms.CenterCrop(size)`     | 从图像中心裁剪指定大小的区域。                               | `transform = transforms.CenterCrop(224)`                     |

数据增强操作：

| 变换函数名称                                                 | 描述                                   | 实例                                                         |
| ------------------------------------------------------------ | -------------------------------------- | ------------------------------------------------------------ |
| `transforms.RandomHorizontalFlip(p)`                         | 随机水平翻转图像。                     | `transform = transforms.RandomHorizontalFlip(p=0.5)`         |
| `transforms.RandomRotation(degrees)`                         | 随机旋转图像。                         | `transform = transforms.RandomRotation(degrees=45)`          |
| `transforms.ColorJitter(brightness, contrast, saturation, hue)` | 调整图像的亮度、对比度、饱和度和色调。 | `transform = transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1)` |
| `transforms.RandomCrop(size)`                                | 随机裁剪指定大小的区域。               | `transform = transforms.RandomCrop(224)`                     |
| `transforms.RandomResizedCrop(size)`                         | 随机裁剪图像并调整到指定大小。         | `transform = transforms.RandomResizedCrop(224)`              |

------

## 构建神经网络模型

神经网络由对数据执行操作的层/模块组成。torch.nn命名空间提供了构建神经网络所需的所有构建块。PyTorch 中的每个模块都是 nn.Module 的子类。神经网络本身也是一个模块，由其他模块（层）组成。这种嵌套结构使得构建和管理复杂的架构变得非常容易。

#### 获取训练设备

我们希望能够在 加速器（如 CUDA、MPS、MTIA 或 XPU）上训练模型。如果当前有可用的加速器，我们将使用它；否则，我们将使用 CPU。

```python
device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
print(f"Using {device} device")
# Using cuda device
```

#### 定义类

我们通过继承 `nn.Module` 来定义神经网络，并在 `__init__` 中初始化神经网络层。每个 `nn.Module` 的子类都会在 `forward` 方法中实现对输入数据的操作。

```python
import torch.nn as nn
import torch.nn.functional as F

class Net(nn.Module):
    def __init__(self):
      super(Net, self).__init__()
      # 第一个 2D 卷积层，接收 1 个输入通道 (图像)，输出 32 个卷积特征，卷积核大小为3×3
      self.conv1 = nn.Conv2d(1, 32, 3, 1)
      # 第二个2D卷积层，接收32个输入层，输出64个卷积特征，卷积核大小为3×3
      self.conv2 = nn.Conv2d(32, 64, 3, 1)
      # 设计用于确保相邻像素要么全部为0，要么全部为激活状态，且具有输入概率
      self.dropout1 = nn.Dropout2d(0.25)
      self.dropout2 = nn.Dropout2d(0.5)
      # 第一个全连接层
      self.fc1 = nn.Linear(9216, 128)
      # 第二个全连接层，输出我们的10个标签
      self.fc2 = nn.Linear(128, 10)

    # x 代表我们的数据
    def forward(self, x):
      x = self.conv1(x)
      x = F.relu(x)
      x = self.conv2(x)
      x = F.relu(x)
      x = F.max_pool2d(x, 2)
      x = self.dropout1(x)
      x = torch.flatten(x, 1)
      x = self.fc1(x)
      x = F.relu(x)
      x = self.dropout2(x)
      x = self.fc2(x)

      output = F.log_softmax(x, dim=1)
      return output
```

我们创建 `NeuralNetwork` 的实例，将其移动到 `device` 上，并打印其结构。

```python
model = Net().to(device)
print(model)
```

输出

```python
Net(
  (conv1): Conv2d(1, 32, kernel_size=(3, 3), stride=(1, 1))
  (conv2): Conv2d(32, 64, kernel_size=(3, 3), stride=(1, 1))
  (dropout1): Dropout2d(p=0.25, inplace=False)
  (dropout2): Dropout2d(p=0.5, inplace=False)
  (fc1): Linear(in_features=9216, out_features=128, bias=True)
  (fc2): Linear(in_features=128, out_features=10, bias=True)
)
```

要使用模型，我们将输入数据传递给它。这会执行模型的 `forward` 方法，以及一些 [后台操作](https://github.com/pytorch/pytorch/blob/270111b7b611d174967ed204776985cefca9c144/torch/nn/modules/module.py#L866)。请勿直接调用 `model.forward()`！

```python
# 相当于一张随机的28x28图像
random_data = torch.rand((1, 1, 28, 28))

result = model(random_data)
print (result)
```

#### nn.Sequential

nn.Sequential 是一个有序的模块容器。数据按照定义的顺序通过所有模块。你可以使用顺序容器来快速组装像 `model` 这样的网络。

```python
# 创建顺序模型，包含线性层、ReLU激活函数和Sigmoid激活函数
model = nn.Sequential(
   nn.Linear(10, 5),  # 输入层到隐藏层的线性变换
   nn.ReLU(),            # 隐藏层的ReLU激活函数
   nn.Linear(5, 1),  # 隐藏层到输出层的线性变换
   nn.Sigmoid()           # 输出层的Sigmoid激活函数
)

input_image = torch.randn(10, 10)
pred = model(input_image)
```

------

## 自动微分 (Autograd)

深度学习的训练本质上是一个反复求梯度、更新参数的过程。

在训练神经网络时，最常用的算法是**反向传播 (back propagation)**。在此算法中，参数（模型权重）会根据损失函数相对于给定参数的**梯度 (gradient)** 进行调整。

手动推导每一层的梯度既繁琐又容易出错，PyTorch 的 Autograd（自动微分）引擎正是为了解决这个问题而生——它能够**自动计算任意计算图的梯度**，让你专注于模型设计，而不是微积分推导。

考虑最简单的单层神经网络，具有输入 `x`，参数 `w` 和 `b`，以及某个损失函数。它可以在 PyTorch 中以以下方式定义：

```python
import torch
import torch.nn.functional as F

x = torch.ones(5)  # 输入
y = torch.zeros(3)
w = torch.randn(5, 3, requires_grad=True)
b = torch.randn(3, requires_grad=True)
z = torch.matmul(x, w) + b
loss = F.binary_cross_entropy_with_logits(z, y)
```

这段代码定义了以下**计算图**：

![计算图](https://docs.pytorch.org/tutorials/_images/comp-graph.png)

在该网络中，`w` 和 `b` 是我们需要优化的**参数**。因此，我们需要能够计算损失函数相对于这些变量的梯度。为此，我们设置这些张量的 `requires_grad` 属性。

> 可以在创建张量时设置 `requires_grad`的值，或者稍后使用 `x.requires_grad_(True)`方法进行设置。
>

#### 计算梯度

为了优化神经网络中的参数权重，我们需要计算损失函数相对于参数的导数，即在 `x` 和 `y` 固定值下的 $\frac {∂loss}{∂w}$ 和 $\frac {∂loss}{∂b}$。为了计算这些导数，我们调用 `loss.backward()`，然后从 `w.grad` 和 `b.grad` 中获取值。

```python
loss.backward()
print(w.grad)
print(b.grad)
```

输出

```python
tensor([[0.1918, 0.0777, 0.2000],
        [0.1918, 0.0777, 0.2000],
        [0.1918, 0.0777, 0.2000],
        [0.1918, 0.0777, 0.2000],
        [0.1918, 0.0777, 0.2000]])
tensor([0.1918, 0.0777, 0.2000])
```

> - PyTorch只能获取计算图中叶子节点的 `grad` 属性，且这些节点的 `requires_grad` 属性必须设置为 `True`。对于图中所有其他节点，梯度将不可用。
> - 出于性能考虑，PyTorch只能在给定的图上执行一次 `backward` 计算。如果我们需要在同一个图上多次进行 `backward` 调用，我们需要在调用 `backward` 时传入 `retain_graph=True`。

Autograd 的梯度是**累积**的，不是覆盖。每次调用 `backward()`，梯度会加到 `.grad` 已有的值上。因此，在训练神经网络时，必须在每次 `backward()` 之前调用 `optimizer.zero_grad()` 清零梯度，否则梯度会不断累积，导致参数更新错误。

#### 禁用梯度跟踪

在模型推理（预测）阶段，不需要计算梯度。使用 `torch.no_grad()` 可以跳过计算图的构建，显著节省内存和计算。

```python
# 常见用途：模型评估时包裹整个推理过程
model = torch.nn.Linear(10, 1)
inputs = torch.randn(32, 10)

with torch.no_grad():
    outputs = model(inputs)   # 不构建计算图，速度更快，内存更省
```

------

## 优化模型参数

训练模型是一个迭代的过程；在每一次迭代中，模型会对输出进行猜测，计算猜测的误差（损失），收集误差相对于其参数的导数，并使用梯度下降法**优化**这些参数。有关此过程的更详细讲解，请查看这个关于 [3Blue1Brown 的反向传播](https://www.youtube.com/watch?v=tIeHLnjs5U8) 视频。

```python
# SGD 优化器参数说明
# params: 要优化的参数（通常来自 model.parameters()）
# lr: 学习率，控制参数更新的步长，默认 0.01
# momentum: 动量因子，用于加速收敛和减少震荡，默认 0
# weight_decay: L2 正则化系数，用于防止过拟合，默认 0
# dampening: 动量阻尼，控制动量项的计算，默认 0
# nesterov: 是否使用 Nesterov 动量，默认 False
optimizer = optim.SGD(
    params=model.parameters(),
    lr=0.01,           # 学习率
    momentum=0.9,      # 动量因子
    weight_decay=1e-4, # L2 正则化
    nesterov=True      # 启用 Nesterov 动量
)

# Adam 优化器参数说明
# params: 要优化的参数
# lr: 学习率，默认 0.001（推荐值）
# betas: 用于计算梯度和梯度平方的移动平均系数 (beta1, beta2)
#         beta1 控制一阶矩估计（动量），默认 0.9
#         beta2 控制二阶矩估计（方差），默认 0.999
# eps: 数值稳定项，防止除零错误，默认 1e-8
# weight_decay: L2 正则化系数，默认 0
# amsgrad: 是否使用 AMSGrad 变体，默认 False
optimizer = optim.Adam(
    params=model.parameters(),
    lr=0.001,                      # 推荐使用较小的学习率
    betas=(0.9, 0.999),            # 常用的动量参数
    eps=1e-8,                      # 数值稳定项
    weight_decay=1e-4,             # L2 正则化
    amsgrad=False                  # 是否使用 AMSGrad
)
```

其他优化器详见[PyTorch torch.optim 优化器模块 | 菜鸟教程](https://www.runoob.com/pytorch/pytorch-torch-optim.html)。

优化器的基本使用流程如下

```python
import torch
import torch.nn as nn
import torch.optim as optim

# 1. 定义一个简单的模型
class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(784, 10)

    def forward(self, x):
        return self.fc(x)

model = SimpleNet()

# 2. 创建优化器实例
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 将模型设置为训练模式——对批归一化和dropout层非常重要，在此情况下并非必需，但出于最佳实践习惯添加
model.train()

# 3. 训练循环
for epoch in range(epochs):
    # 前向传播
    outputs = model(inputs)
    loss = criterion(outputs, labels)

    # 反向传播
    optimizer.zero_grad()  # 清空梯度缓存，避免梯度累积
    loss.backward()        # 计算梯度，自动微分 (Autograd) 在这一步完成

    # 参数更新
    optimizer.step()       # 更新参数
```

不同优化器适用于不同场景，选择合适的优化器可以显著提升训练效果。

| 优化器名称 | 主要特点            | 适用场景                |
| ---------- | ------------------- | ----------------------- |
| SGD        | 简单基础，可带动量  | 基础教学、简单模型、CNN |
| Adam       | 自适应学习率        | 大多数深度学习任务      |
| AdamW      | Adam + 权重衰减分离 | 需要 L2 正则化的任务    |
| RMSprop    | 自适应学习率        | RNN 网络、语音识别      |
| Adagrad    | 参数独立学习率      | 稀疏数据、文本处理      |
| Adadelta   | 自适应学习率        | 长期训练任务            |

*注意：必须在每次反向传播前调用 zero_grad()，否则梯度会累积，导致训练不稳定。建议使用 zero_grad(set_to_none=True) ，此时会将梯度设为 None，比设为 0 更节省显存。*

------

## 保存和加载模型

在深度学习项目中，模型保存和加载是至关重要的环节，主要原因包括：

1. **训练中断恢复**：当训练过程意外中断时，可以从保存点继续训练
2. **模型部署**：将训练好的模型部署到生产环境
3. **模型共享**：方便团队成员之间共享模型成果
4. **迁移学习**：保存预训练模型用于其他任务
5. **性能评估**：保存不同训练阶段的模型进行比较

#### 保存整个模型

这是最简单的方法，保存模型的架构和参数：

```python
import torch
import torchvision.models as models

# 创建并训练一个模型
# ResNet 全称 Residual Network（残差网络），由微软研究院于 2015 年提出。它在 ImageNet 比赛上横扫了当年的冠军，是深度学习发展史上的一个分水岭。
model = models.resnet18(weights="IMAGENET1K_V1") # 这里指定了权重，相当于已经完成训练了

# 保存整个模型
torch.save(model, 'model.pth')

# 加载整个模型
loaded_model = torch.load('model.pth')
```

#### 仅保存模型参数（推荐方式）

PyTorch 模型将其学习到的参数存储在内部状态字典中，称为 `state_dict`。这些参数可以通过 `torch.save` 方法进行持久化。

```python
import torch
import torchvision.models as models

# VGG16 是一个非常经典、在深度学习历史上具有里程碑意义的卷积神经网络（CNN）模型，由牛津大学的视觉几何研究组 Visual Geometry Group 提出，主要用于图像分类任务。
model = models.vgg16(weights='IMAGENET1K_V1') # 这里指定了权重，相当于已经完成训练了

torch.save(model.state_dict(), 'model_weights.pth')
```

要加载模型权重，你需要先创建一个相同模型的实例，然后使用 `load_state_dict()` 方法加载参数。

在下面的代码中，我们设置 `weights_only=True`，以将反序列化过程中执行的函数限制为仅加载权重所必需的函数。使用 `weights_only=True` 被认为是加载权重时的最佳实践。

```python
model = models.vgg16() # 这里未指定“权重”，即创建未经训练的模型
model.load_state_dict(torch.load('model_weights.pth', weights_only=True))
model.eval()
# 请务必在进行推理之前调用 model.eval() 方法，将 dropout 层和批归一化（batch normalization）层设置为评估模式。如果不这样做，将会导致推理结果不一致。
```

#### 保存和加载用于推理和/或恢复训练的通用检查点

在保存通用的检查点（用于推理或恢复训练）时，必须保存除模型 `state_dict` 之外的更多信息。保存优化器的 `state_dict` 也非常重要，因为它包含了在模型训练时更新的缓冲区和参数。你可能想要保存的其他项包括：中断时的 epoch、最新记录的训练损失、外部 `torch.nn.Embedding` 层等。因此，这样的检查点通常比单独的模型大 2 到 3 倍。

保存

```python
import torchvision.models as models
import os

model = models.resnet18(weights=None, num_classes=10)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)
epochs_trained = 10
best_accuracy = 0.85
loss = 0.2

checkpoint = {
    'epoch': epochs_trained,                     # 当前训练了多少轮
    'model_state_dict': model.state_dict(),       # 模型参数
    'optimizer_state_dict': optimizer.state_dict(), # 优化器状态
    'scheduler_state_dict': lr_scheduler.state_dict(), # 学习率调度器状态
    'loss': loss,                                 # 当前损失
    'accuracy': best_accuracy,                   # 当前精度
    # 'random_state': torch.get_rng_state(),     # 可选：保存随机种子，确保完全复现
}

checkpoint_path = 'checkpoint_epoch_10.pth'

torch.save(checkpoint, checkpoint_path)
print(f"Checkpoint saved at {checkpoint_path}")
```

加载

```python
# 1. 实例化模型和优化器（结构必须匹配）
model = models.resnet18(weights=None, num_classes=10)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001) # lr在这里不重要，会被覆盖
lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)

# 2. 加载 checkpoint 文件
checkpoint = torch.load('checkpoint_epoch_10.pth', map_location=torch.device('cpu'))

# 3. 恢复各个组件的状态
epoch = checkpoint['epoch']
model.load_state_dict(checkpoint['model_state_dict'])
optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
lr_scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
loss = checkpoint['loss']
accuracy = checkpoint['accuracy']

# 4. 切换到训练模式（继续训练）
model.train() 

print(f"Resuming training from epoch {epoch} with loss {loss:.4f}")

# 继续训练循环
# for epoch in range(start_epoch, total_epochs):
#    ...
```

------

## 神经网络训练全流程

至此，PyTorch的所有基础流程都介绍完毕，一个完整的MINST训练集的工作流程如下。

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import LinearLR

import time

device = torch.device("cuda")
print("使用设备：", device)


transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307, ), (0.3081))
])
"""
# 更多变换相当于扩充数据集
transform = transforms.Compose([
    transforms.RandomRotation(10),  # 随机旋转±10度
    transforms.RandomAffine(0, translate=(0.1, 0.1)),  # 随机平移10%
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
    ])
"""

train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
test_dataset = datasets.MNIST(root='./data', train=False, download=True, transform=transform)

train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=1000, shuffle=False)


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        # 卷积层：提取局部特征，参数量极少
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)  # 16个卷积核=宽度16
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1) # 32个卷积核=宽度32
        self.pool = nn.MaxPool2d(2, 2)  # 下采样，压缩尺寸
        # 全连接层：分类
        self.fc = nn.Linear(64 * 7 * 7, 10)  # 两次池化后尺寸是7x7

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))  # 28x28 → 14x14
        x = self.pool(F.relu(self.conv2(x)))  # 14x14 → 7x7
        x = x.view(-1, 64 * 7 * 7)  # 展平
        x = self.fc(x)
        return x


model = Net().to(device)
"""
# 或者
model = nn.Sequential(
    nn.Conv2d(1, 32, kernel_size=3, padding=1),
    nn.MaxPool2d(2, 2),
    nn.Conv2d(32, 64, kernel_size=3, padding=1),
    nn.MaxPool2d(2, 2),
    nn.Flatten()
    nn.Linear(64 * 7 * 7, 10),
)
"""

model.train()

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

epochs = 1000
fin_epochs = epochs

start = time.time()
for epoch in range(epochs):
    total_loss = 0
    correct = 0
    total = 0

    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)

        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        # 计算准确率
        pred = output.argmax(dim=1, keepdim=True)
        correct += pred.eq(target.view_as(pred)).sum().item()
        total += target.size(0)
    if loss.item() < 0.0003:
        fin_epochs = epoch
        break
    if epoch % 1 == 0:
        avg_loss = total_loss / len(train_loader)
        accuracy = 100. * correct / total
        print(f"Epoch {epoch}: Loss={avg_loss:.4f}, Accuracy={accuracy:.2f}%")

end = time.time()
print("训练用时：", end-start, "秒")
print("训练总轮数：", fin_epochs)

model.eval()
correct = 0
total = 0
with torch.no_grad():
    for data, target in test_loader:
        data, target = data.to(device), target.to(device)
        output = model(data)
        pred = output.argmax(dim=1)
        correct += pred.eq(target).sum().item()
        total += target.size(0)
print(f"Test Accuracy: {100. * correct / total:.2f}%")

torch.save(model.state_dict(), 'my_model_weights.pth')
```

------

## 批归一化（Batch Normalization）与 Dropout

#### 批归一化（Batch Normalization）

深层网络在训练时，前一层参数的微小变化会随层数加深而被不断放大，导致后续层的输入分布持续变化——这一现象称为**内部协变量偏移（Internal Covariate Shift）**。批归一化通过在每一层的输出上做标准化，强制将激活值拉回稳定的分布，从而解决这一问题。[批量归一化 (Batch Normalization) 论文](https://arxiv.org/abs/1502.03167)。

PyTorch 根据输入维度提供三个版本，使用方式完全一致，只是处理的数据形状不同。

```python
import torch
import torch.nn as nn

# 输入形状：(N, C) 或 (N, C, L)
# N=batch_size, C=特征数/通道数, L=序列长度
bn1d = nn.BatchNorm1d(
    num_features=128,    # 特征/通道数
    eps=1e-5,            # 防止除零的小常数（默认 1e-5）
    momentum=0.1,        # 滑动平均的动量（默认 0.1）
    affine=True,         # 是否学习 gamma 和 beta（默认 True）
    track_running_stats=True,  # 是否追踪运行时均值/方差（默认 True）
)

# 2D
# bn2d = nn.BatchNorm2d(num_features=64)

# 3D
# bn3d = nn.BatchNorm3d(num_features=32)

# 全连接层后使用
x = torch.randn(32, 128)     # (batch=32, features=128)
out = bn1d(x)
print(out.shape)              # torch.Size([32, 128])

# 序列数据（如 1D 卷积后）
x_seq = torch.randn(32, 128, 50)   # (batch, channels, seq_len)
out_seq = bn1d(x_seq)
print(out_seq.shape)               # torch.Size([32, 128, 50])
```

各归一化方法对比

| 方法           | 归一化维度               | batch 依赖 | 适用场景                 |
| -------------- | ------------------------ | ---------- | ------------------------ |
| `BatchNorm`    | 跨 batch（同通道）       | 强依赖     | CNN 图像分类（大 batch） |
| `LayerNorm`    | 跨特征（同样本）         | 无依赖     | Transformer、NLP、RNN    |
| `GroupNorm`    | 组内通道（同样本）       | 无依赖     | 小 batch 目标检测、分割  |
| `InstanceNorm` | 空间维度（同样本同通道） | 无依赖     | 图像风格迁移、生成模型   |

#### Dropout

Dropout 在训练时随机将某些神经元的输出置为 0（概率为 `p`），强迫网络不能依赖任何单一神经元，从而学习更鲁棒、分散的特征表示，有效防止过拟合。

Dropout：用于全连接层

```python
import torch
import torch.nn as nn

dropout = nn.Dropout(p=0.5)   # p：置零的概率

x = torch.ones(2, 10)
print("训练模式:")
dropout.train()
print(dropout(x))    # 约 50% 的值为 0，保留的值为 2.0

print("\n评估模式:")
dropout.eval()
print(dropout(x))    # 全为 1.0，Dropout 关闭
```

输出

```python
训练模式:
tensor([[2., 0., 2., 0., 2., 0., 0., 2., 2., 0.],
        [0., 2., 0., 2., 0., 2., 2., 0., 0., 2.]])

评估模式:
tensor([[1., 1., 1., 1., 1., 1., 1., 1., 1., 1.],
        [1., 1., 1., 1., 1., 1., 1., 1., 1., 1.]])
```

Dropout2d：用于 CNN 特征图（整通道丢弃）

`Dropout2d` 以通道为单位随机丢弃，即整个通道的所有空间位置一起被置零。这比逐点 Dropout 更适合卷积特征，因为相邻像素的激活值高度相关，逐点丢弃效果较弱。

Dropout3d：用于 3D 卷积

#### 训练模式与评估模式

BatchNorm 和 Dropout 的行为在训练和评估时**完全不同**，必须正确切换，这是初学者最常见的错误之一。

| 组件      | `model.train()`                                           | `model.eval()`                         |
| --------- | --------------------------------------------------------- | -------------------------------------- |
| BatchNorm | 用当前 batch 的均值/方差归一化；**更新** running_mean/var | 用 running_mean/var 归一化；**不更新** |
| Dropout   | 随机置零（按概率 p）                                      | 关闭，所有神经元正常输出               |

------

## 结语

本文内容来自[PyTorch官方文档](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)、[PyTorch 教程 | 菜鸟教程](https://www.runoob.com/pytorch/pytorch-tutorial.html)。

感谢你阅读这篇文章！如果你有任何问题或建议，欢迎通过 [GitHub Issues](https://github.com/Ling-Nine/Ling-nine.github.io/issues) 与我交流。

---

*本文使用 Markdown 编写，最后更新于 2026年8月1日*