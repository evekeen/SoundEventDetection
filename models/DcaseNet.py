import pdb

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from models.model_utilities import ConvBlock, init_gru, init_layer, interpolate
from utils.common import count_parameters, human_format

class DcaseNet_v3(nn.Module):
    def __init__(self, pool_type='avg', pool_size=(2,2)):
        super().__init__()

        #####
        # Common
        #####
        self.pool_type = pool_type
        self.pool_size = pool_size
        
        self.conv_block1 = ConvBlock(in_channels=1, out_channels=64)
        self.conv_block2 = ConvBlock(in_channels=64, out_channels=128)
        self.conv_block3 = ConvBlock(in_channels=128, out_channels=256)
        self.conv_block4_1 = ConvBlock(in_channels=256, out_channels=256)
        self.conv_block4_2 = ConvBlock(in_channels=256, out_channels=256)

        self.gru_1 = nn.GRU(input_size=512, hidden_size=128, 
            num_layers=1, batch_first=True, bidirectional=True)
        self.gru_2 = nn.GRU(input_size=512, hidden_size=128, 
            num_layers=1, batch_first=True, bidirectional=True)
        self.event_fc = nn.Linear(256, 14, bias=True)

        #####
        # Initialize
        #####
        self.init_weights()

    def init_weights(self):

        init_gru(self.gru_1)
        init_gru(self.gru_2)
        init_layer(self.event_fc)

    def forward(self, x):
        d_return = {}   # dictionary to return

        #x: (#bs, #ch, #mel, #seq)
        #forward frame-level
        x = self.conv_block1(x, self.pool_type, pool_size=self.pool_size)
        x = self.conv_block2(x, self.pool_type, pool_size=self.pool_size)
        x = self.conv_block3(x, self.pool_type, pool_size=self.pool_size)
        x_1 = self.conv_block4_1(x, self.pool_type, pool_size=(2, 5))   #common branch
        x_2 = self.conv_block4_2(x, self.pool_type, pool_size=(2, 5))   #task specific branch
        #x: (#bs, #filt, #mel, #seq)

        x = torch.cat([x_1, x_2], dim=1)    #x: (#bs, #filt, #mel, #seq)
        if self.pool_type == 'avg':
            x = torch.mean(x, dim=2)
        elif self.pool_type == 'max':
            (x, _) = torch.max(x, dim=2)
        #x: (#bs, #filt,#seq)
        x = x.transpose(1,2)
        #x: (#bs, #seq, #filt)
        (x_1, _) = self.gru_1(x)
        (x_2, _) = self.gru_2(x)
        

        out_SED = x_2
        #out_SED = self.layer_SED(x)
        out_SED = torch.sigmoid(self.event_fc(out_SED))
        out_SED = out_SED.repeat_interleave(repeats=8, dim=1)
        return out_SED
    
    def model_description(self):
        print(f"\DcaseNet_v3 has {human_format(count_parameters(self))} parameters")


if __name__ == '__main__':
    pass