import os
import argparse
import time
from models import AlexNet, VGGNet, MSELoss
import torch.nn as nn
import torch

import torch.optim as optim
from tqdm import tqdm
from utils import init_logger_writer, inform_logger_writer, close_logger_writer, data_loader, AvgMeter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import get_backend

_visualize_save_path = None
_class_accuracy_save_path = None

def preparation(args):
    """
    根据命令行的参数设置相应的模型、损失函数、优化器、是否使用学习率调节器
    Args:
    * args: 从命令行传入的参数
    """
    # 初始化log和tensorboard实例
    logger, writer = init_logger_writer(args)
    # 获取模型
    if args.model == 'alexnet':
        model = AlexNet(dropout_prob=args.prob)
    elif args.model == 'vggnet':
        model = VGGNet(dropout_prob=args.prob)
    else:
        raise NotImplementedError(f"The {args.model} model is not implemented!")
    # 获取损失函数
    if args.criterion == 'cross_entropy':
        criterion = nn.CrossEntropyLoss()  # 交叉熵损失
    elif args.criterion == 'mse':
        criterion = MSELoss()  # 均方误差损失
    else:
        raise NotImplementedError(f"The {args.criterion} criterion isn't implemented!")
    # 根据学习率(learning rate)设置optimizer，SGD优化器额外指定了momentum=0.9
    if args.optimizer == 'sgd':
        optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=0.9)
    elif args.optimizer == 'adam':
        optimizer = optim.Adam(model.parameters(), lr=args.lr)
    else:
        raise NotImplementedError(f"The {args.optimizer} optimizer isn't implemented!")

    # 设置scheduler（学习率调节器）
    # 如果不设置则训练过程中学习率一直为args.lr
    # 如果选择设置，如下给出了一种调节思路：
    # 总共有num_epochs个epoch，第i个epoch（i从0开始）的学习率衰减因子为 (1 - i/epochs)^0.9，
    # 即学习率从初始值逐渐衰减至接近0，使训练后期梯度变化趋于稳定
    scheduler = None
    if args.use_scheduler:
        scheduler = optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=lambda epoch: (1 - epoch / args.epochs) ** 0.9)

    return model, criterion, optimizer, scheduler, logger, writer


def train_process(args, train_loader, val_loader, model, device, criterion, optimizer, scheduler, logger, writer):
    """
    训练模型，并保存在验证集上准确率最高的模型参数用于后续测试
    """
    # 记录最好的验证集准确率
    best_accu= 0.
    # 记录一个epoch里的开始时刻、训练完成时刻、验证完成时刻
    time_list = [0 for _ in range(3)]
    for epoch in range(1, args.epochs+1):
        # train part
        model.train()
        time_list[0] = time.time()
        loss_meter = AvgMeter()
        accu_meter = AvgMeter()
        for data_batch, target_batch in tqdm(train_loader):
            # 将data和target的批量数据也转移到相应的device上
            data_batch, target_batch = data_batch.to(device), target_batch.to(device)
            optimizer.zero_grad()
            output_batch = model(data_batch)
            loss = criterion(output_batch, target_batch)
            loss.backward()
            optimizer.step()
            loss_meter.add(loss.item(), data_batch.size(0))
            pred = output_batch.argmax(dim=1, keepdim=True)
            correct = pred.eq(target_batch.view_as(pred)).sum()
            accu_meter.add(correct.item() / data_batch.size(0), data_batch.size(0))
        if args.use_scheduler:
            scheduler.step()
        # 计算该epoch的训练loss和accuracy均值
        train_loss = loss_meter.avg()
        train_accu = accu_meter.avg()

        # validate part
        time_list[1] = time.time()
        model.eval() 
        loss_meter = AvgMeter()
        accu_meter = AvgMeter()
        # 验证阶段无需反向梯度传播，所以指定torch.no_grad()防止产生梯度
        with torch.no_grad():
            for data_batch, target_batch in tqdm(val_loader):
                data_batch, target_batch = data_batch.to(device), target_batch.to(device)
                output_batch = model(data_batch)
                loss = criterion(output_batch, target_batch)
                loss_meter.add(loss.item(), data_batch.size(0))
                # 根据概率最大原则得到输入的标签预测值
                pred = output_batch.argmax(dim=1, keepdim=True)
                correct = pred.eq(target_batch.view_as(pred)).sum()
                accu_meter.add(correct.item() / data_batch.size(0), data_batch.size(0))

        val_loss = loss_meter.avg()
        val_accu = accu_meter.avg()

        time_list[2] = time.time()
        inform_logger_writer(logger, writer, epoch, train_loss, val_loss, train_accu, val_accu, time_list)

        if accu_meter.avg() > best_accu:
            # 如果超过了当前的最好验证集准确率，则保存该模型参数
            best_accu= accu_meter.avg()
            if not os.path.exists(args.checkpoint_dir):
                os.makedirs(args.checkpoint_dir)
            torch.save(model.state_dict(), os.path.join(args.checkpoint_dir, 'best.pt'))
            print(f'Save best model @ Epoch {epoch}')


def test_process(args, test_loader, model, device, criterion):
    """
    使用验证集上准确率最高的模型在测试集上进行测试

    Args:
    * args: 命令行传入的参数
    * test_loader: 测试数据集

    Returns:
    * test_loss: 测试数据集的平均损失
    * test_accu: 测试数据集的平均准确率
    """
    # 加载之前保存的模型参数
    model.load_state_dict(torch.load(os.path.join(args.checkpoint_dir, 'best.pt'), map_location=device))
    loss_meter = AvgMeter()
    accu_meter = AvgMeter()
    # 每个类别的预测正确数
    class_correct = [0 for _ in range(10)]
    # 每个类别的数量
    class_total   = [0 for _ in range(10)]
    experiment_name = os.path.basename(os.path.normpath(args.checkpoint_dir))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    figures_dir = os.path.join(project_root, 'figures')
    result_dir = os.path.join(project_root, 'result')
    os.makedirs(figures_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)
    global _visualize_save_path, _class_accuracy_save_path
    _visualize_save_path = os.path.join(figures_dir, f'class_accuracy_{experiment_name}.png')
    _class_accuracy_save_path = os.path.join(result_dir, f'class_accuracy_{experiment_name}.csv')
    model.eval()
    with torch.no_grad():
        for data_batch, target_batch in tqdm(test_loader):
            data_batch, target_batch = data_batch.to(device), target_batch.to(device)
            output_batch = model(data_batch)
            loss = criterion(output_batch, target_batch)
            loss_meter.add(loss.item(), data_batch.size(0))
            pred = output_batch.argmax(dim=1, keepdim=True)
            correct = pred.eq(target_batch.view_as(pred)).sum()
            accu_meter.add(correct.item() / data_batch.size(0), data_batch.size(0))
            for i in range(target_batch.size(0)):
                label = target_batch[i].item()
                class_correct[label] += int(pred[i].item() == label)
                class_total[label] += 1

    visualize_results(class_correct, class_total)

    test_loss = loss_meter.avg()
    test_accu = accu_meter.avg()

    return test_loss, test_accu


def visualize_results(class_correct, class_total):
    """
    将测试结果可视化为柱状图

    Args:
    * class_correct: 测试集中每一类时尚单品的预测正确数
    * class_total: 测试集中每一类时尚单品的数量
    """
    classes = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']
    class_accuracy = [100.0 * correct / total if total > 0 else 0.0 for correct, total in zip(class_correct, class_total)]

    plt.figure(figsize=(8, 6))
    plt.bar(classes, class_accuracy, color = (0.3,0.9,0.4,0.6), width=0.5)
    plt.xlabel('Class')
    plt.ylabel('Accuracy (%)')
    plt.title('Classification Accuracy for Each Class')
    plt.ylim(0, 105)

    for i in range(len(classes)):
        plt.text(i, class_accuracy[i] + 2, f'{class_accuracy[i]:.2f}%', ha='center', va='bottom')

    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    if _visualize_save_path is not None:
        plt.savefig(_visualize_save_path, dpi=200)
    if _class_accuracy_save_path is not None:
        with open(_class_accuracy_save_path, 'w', encoding='utf-8') as f:
            f.write('class,correct,total,accuracy\n')
            for class_name, correct, total, accuracy in zip(classes, class_correct, class_total, class_accuracy):
                f.write(f'{class_name},{correct},{total},{accuracy:.4f}\n')
    if get_backend().lower() != 'agg':
        plt.show()
    plt.close()

if __name__ == '__main__':
    # 指定命令行传入参数
    parser = argparse.ArgumentParser(description='train process')
    # 指定模型
    parser.add_argument('--model', default='alexnet', type=str, help='alexnet or vggnet')
    # 指定dropout probability
    parser.add_argument('--prob', default=0.5, type=float, help='dropout probability')
    # 损失函数
    parser.add_argument('--criterion', default='cross_entropy', type=str, help='cross_entropy or mse')
    # 指定初始学习率
    parser.add_argument('--lr', default=1e-2, type=float)
    # 指定优化器
    parser.add_argument('--optimizer', default='sgd', type=str, help='sgd or adam')
    # 是否使用学习率调节器
    parser.add_argument('--use_scheduler', action='store_true', help='decide if use learning rate scheduler')
    parser.add_argument('--batch_size', default=128, type=int)
    parser.add_argument('--epochs', default=10, type=int)
    parser.add_argument('--checkpoint_dir', default='./checkpoint', type=str, help='the directory to save the best checkpoint')
    args = parser.parse_args()

    start_time = time.time()
    train_loader, val_loader, test_loader = data_loader(batch_size=args.batch_size)  # 产生dataloader
    model, criterion, optimizer, scheduler, logger, writer = preparation(args)  # 获取训练所需要的各种实例
    # 设置训练使用的设备（如果检测到CUDA可用就使用GPU进行训练和推理）
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # 将模型转移到指定的设备上去
    model = model.to(device)
    # 开始训练
    train_process(args, train_loader, val_loader, model, device, criterion, optimizer, scheduler, logger, writer)  # 训练和验证
    # 开始测试
    test_loss, test_accu= test_process(args, test_loader, model, device, criterion)
    # 关闭log和tensorboard实例
    close_logger_writer(logger, writer, start_time, test_loss, test_accu)
