#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import torch
import torch.nn as nn
import torch.nn.functional as F


class DLModel(nn.Module):

    def __init__(self, in_c, in_h, in_w, out_size, conv_kernel=3, max_pool_kernel=2):
        """
        Convolutional Neural Network
        
        Network Structure：

            input(map) ─ CONV ─ CONV ─ MaxPool ─ CONV ─ CONV ─ MaxPool ┬ FC ─ FC ─ output
            input(info) ───────────────────────────────────────────────┘

            # Apply batch normalizetion following MaxPool
        """

        super(DLModel, self).__init__()

        self.block1 = nn.Sequential(
            nn.Conv2d(in_channels=in_c, out_channels=32, kernel_size=conv_kernel, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=conv_kernel, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=max_pool_kernel, stride=1),
            nn.BatchNorm2d(32)
        )
        self.block2 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=conv_kernel, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=conv_kernel, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=max_pool_kernel, stride=1),
            nn.BatchNorm2d(64)
        )
        self.block3 = nn.Sequential(
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=conv_kernel, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=conv_kernel, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=max_pool_kernel, stride=1),
            nn.BatchNorm2d(64)
        )
        self.full_connection = nn.Sequential(
            nn.Linear(in_features=64 * (in_h - 3) * (in_h - 3) + 3, out_features=1024), # '+3' means date, latitude and longitude
            nn.ReLU(),
            nn.Dropout(),
            nn.Linear(in_features=1024, out_features=out_size, bias=False)
        )


    # Define a process of 'Forward'
    def forward(self, maps, infos):

        # Convolutional layers
        x = self.block1(maps)
        x = self.block2(x)
        x = self.block3(x)

        # Change 2-D to 1-D
        x = x.view(x.size(0), 64 * 14 * 14)

        # Full connection layers
        y = self.full_connection(torch.cat([x, infos], dim=1))
        
        return y

