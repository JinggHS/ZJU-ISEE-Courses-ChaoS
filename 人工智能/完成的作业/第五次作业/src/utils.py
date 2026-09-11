import os
import logging
import time
import torch
import torchvision.transforms as transforms
import torchvision.datasets as datasets
from torch.utils.data import DataLoader
import torch.utils.data as data

from tensorboardX import SummaryWriter

# Define the transformations for the dataset
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

def data_loader(dataset_dir='./dataset', train_ratio=0.8, batch_size=128):
    """
    加载训练数据集、验证数据集和测试数据集
    (如果数据集不存在)

    Args:
    * dataset_dir: 存储FashionMNIST数据集的根目录
    * train_ratio: train_set在train_val_dataset中所占的比例
    * batch_size: 在训练过程中使用的batch_size，即把多个输入合成一个batch进行训练

    Returns:
    train_loader: 训练数据集
    val_loader: 验证数据集
    test_loader: 测试数据集
    """
    # 为PyTorch设置随机种子，保证每次打乱数据集时的随机性一致
    torch.manual_seed(42)
    # download the specified datasets to the dataset_dir
    train_val_dataset = datasets.FashionMNIST(
        root=dataset_dir,
        train=True,
        transform=transform,
        download=True
    )
    test_dataset = datasets.FashionMNIST(
        root=dataset_dir,
        train=False,
        transform=transform,
        download=True
    )

    # split the train_val_dataset by the train_ratio
    total_len = len(train_val_dataset)
    train_len = int(total_len * train_ratio)
    val_len = total_len - train_len
    train_dataset, val_dataset = data.random_split(train_val_dataset, lengths=[train_len, val_len])
    print(f'Size of train_dataset: {len(train_dataset)}')
    print(f'Size of val_dataset: {len(val_dataset)}')
    print(f'Size of test_dataset: {len(test_dataset)}')

    # generate loaders
    # use shuffle=True to introduce randomness for training
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader   = DataLoader(val_dataset,   batch_size=batch_size, shuffle=False)
    test_loader  = DataLoader(test_dataset,  batch_size=batch_size, shuffle=False)

    return train_loader, val_loader, test_loader


def print_and_logger(string, logger):
    print(string)
    logger.info(string)


def init_logger(args):
    """
    初始化logger
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    experiment_name = os.path.basename(os.path.normpath(args.checkpoint_dir))
    log_dir = os.path.join(project_root, 'result', 'logs', experiment_name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    f = logging.FileHandler(os.path.join(log_dir, 'log.txt'), mode='w+')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    f.setFormatter(formatter)
    logger.addHandler(f)

    l_str = '> Arguments:'
    print_and_logger(l_str, logger)
    for key in args.__dict__.keys():
        l_str = '\t{}: {}'.format(key, args.__dict__[key])
        print_and_logger(l_str, logger)

    return logger, log_dir

class DictTable(dict):
    # Overridden dict class which takes a dict in the form {'a': 2, 'b': 3},
    # and renders an HTML Table in IPython Notebook.
    def _repr_html_(self):
        html = ["<table width=100%>"]
        for key, value in self.items():
            html.append("<tr>")
            html.append("<td>{0}</td>".format(key))
            html.append("<td>{0}</td>".format(value))
            html.append("</tr>")
        html.append("</table>")
        return ''.join(html)

def init_logger_writer(args):
    """
    初始化logger（用于文字记录训练过程）和writer（用于可视化loss、acc等关注的值）
    """
    logger, log_dir = init_logger(args)
    writer = SummaryWriter(log_dir)
    writer.add_text('args', DictTable(args.__dict__)._repr_html_(), 0)  # record the training configurations

    return logger, writer

def inform_logger_writer(logger, writer, epoch, train_loss, val_loss, train_acc, val_acc, time_list):
    l_str = '[epoch {}] elapsed time: {:1.4f}s, train time: {:1.4f}s, val time: {:1.4f}s'. \
        format(epoch, time_list[2] - time_list[0], time_list[1] - time_list[0], time_list[2] - time_list[1])
    print_and_logger(l_str, logger)
    l_str = '***** Train_dataset result ***** loss: {:1.4f}, accuracy {:1.2f}%'.format(train_loss, train_acc * 100)
    print_and_logger(l_str, logger)
    l_str = '***** Val_dataset   result ***** loss: {:1.4f}, accuracy {:1.2f}%'.format(val_loss, val_acc * 100)
    print_and_logger(l_str, logger)

    writer.add_scalar('train/loss', train_loss, epoch)
    writer.add_scalar('train/accuracy', train_acc * 100, epoch)
    writer.add_scalar('val/loss', val_loss, epoch)
    writer.add_scalar('val/accuracy', val_acc * 100, epoch)

def close_logger_writer(logger, writer, start_time, test_loss, test_acc):
    print_and_logger(' ', logger)
    l_str = 'Elapsed time {}'.format(time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time)))
    print_and_logger(l_str, logger)
    l_str = '***** Test_dataset result ***** loss: {:1.4f}, accuracy {:1.2f}%'.format(test_loss, test_acc * 100)
    print_and_logger(l_str, logger)

    loggers = list(logger.handlers)
    for i in loggers:
        logger.removeHandler(i)
        i.flush()
        i.close()
    writer.close()

class AvgMeter(object):
    def __init__(self):
        self.cnt = 0
        self.sum = 0

    def add(self, aver, cnt=1):
        self.sum += aver * cnt
        self.cnt += cnt

    def avg(self):
        assert self.cnt != 0
        return self.sum / self.cnt
