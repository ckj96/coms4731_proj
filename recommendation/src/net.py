"""
Image Similarity using Deep Ranking.

references: https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/42945.pdf

@author: Zhenye Na
"""

import os
import torch
import torchvision
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms

from torch.autograd import Variable

model_urls = {
    'resnet18': 'https://download.pytorch.org/models/resnet18-5c106cde.pth',
    'resnet34': 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
    'resnet50': 'https://download.pytorch.org/models/resnet50-19c8e357.pth',
    'resnet101': 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth',
    'resnet152': 'https://download.pytorch.org/models/resnet152-b121ed2d.pth',
}


def freeze_layer(layer):
    for param in layer.parameters():
        param.requires_grad = False


def resnet18(model_urls, pretrained=True):
    """
    Construct a ResNet-18 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = torchvision.models.resnet.ResNet(
        torchvision.models.resnet.BasicBlock, [2, 2, 2, 2])
    if pretrained:
        model.load_state_dict(torch.utils.model_zoo.load_url(
            model_urls['resnet18'], model_dir='../resnet18'))
    return EmbeddingNet(model)


def resnet101(pretrained=False, **kwargs):
    """
    Construct a ResNet-101 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """

    if pretrained:
        # model.load_state_dict(torch.utils.model_zoo.load_url(
        #     model_urls['resnet101'], model_dir='../resnet101'))
        print('use pretrained data')
        model = models.resnet101(pretrained=True)
    else:
        model = torchvision.models.resnet.ResNet(
            torchvision.models.resnet.BasicBlock, [3, 4, 23, 3])
    return EmbeddingNet(model)


def resnet50(pretrained=True, **kwargs):
    if pretrained:
        model = models.resnet50(num_classes=365)
        model_file = '../checkpoint/res50.pth.tar'
        checkpoint = torch.load(model_file, map_location=lambda storage, loc: storage)
        state_dict = {str.replace(k, 'module.', ''): v for k, v in checkpoint['state_dict'].items()}
        model.load_state_dict(state_dict)
    else:
        model = models.resnet50()

    return EmbeddingNet(model)


class TripletNet(nn.Module):
    """Triplet Network."""

    def __init__(self, embeddingnet):
        """Triplet Network Builder."""
        super(TripletNet, self).__init__()
        self.embeddingnet = embeddingnet
        self.fc2 = nn.Linear(2048, 201)
        self.sm = nn.Softmax()

    def forward(self, a, p, n):
        """Forward pass."""
        # anchor
        embedded_a = self.embeddingnet(a)

        # positive examples
        embedded_p = self.embeddingnet(p)

        # negative examples
        embedded_n = self.embeddingnet(n)

        cat_a = self.sm(self.fc2(embedded_a))
        cat_p = self.sm(self.fc2(embedded_p))
        cat_n = self.sm(self.fc2(embedded_n))
        return embedded_a, embedded_p, embedded_n, cat_a, cat_p, cat_n


class EmbeddingNet(nn.Module):
    """EmbeddingNet using ResNet-101."""

    def __init__(self, resnet, freeze=False):
        """Initialize EmbeddingNet model."""
        super(EmbeddingNet, self).__init__()

        # Everything except the last linear layer
        # print(list(resnet.children()))
        if freeze:
            for child in resnet.children():
                freeze_layer(child)
        self.features = nn.Sequential(*list(resnet.children())[:-1])
        num_ftrs = resnet.fc.in_features
        print('num_features:', num_ftrs)
        # self.fc1 = nn.Linear(num_ftrs, 4096)

    def forward(self, x):
        """Forward pass of EmbeddingNet."""

        out = self.features(x)
        out = out.view(out.size(0), -1)
        # out = self.fc1(out)

        return out
