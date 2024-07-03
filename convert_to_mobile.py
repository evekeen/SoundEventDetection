import os
import re
import torch
from torch.utils.mobile_optimizer import optimize_for_mobile, MobileOptimizerType

from models.DcaseNet import DcaseNet_v3

epoch_regex = re.compile(r'.*_(\d+)\.pth(\.tar)?')


def save_no_quantization(model):
    torchscript_model = torch.jit.script(model)
    torchscript_model_optimized = optimize_for_mobile(torchscript_model, optimization_blocklist={MobileOptimizerType.INSERT_FOLD_PREPACK_OPS})
    torchscript_model_optimized._save_for_lite_interpreter("model-no-quantization.ptl")
    
def get_epoch(path):
    matches = epoch_regex.match(path)
    if matches is not None:
        return int(matches.group(1))
    return 0
    
def load_checkpoints(path):
    checkpoints = list(filter(lambda p: epoch_regex.match(p), os.listdir(path)))
    checkpoints.sort(key=get_epoch)
    return checkpoints

def load_and_evaluate_model():
    model = DcaseNet_v3(1)
    model_home = os.path.join('networks', 'dcasenet_v3')
    checkpoints = load_checkpoints(model_home)
    last_checkpoint = checkpoints[-1]
    checkpoint_path = os.path.join(model_home, last_checkpoint)
    print('loading checkpoint', checkpoint_path)
    checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))
    model.load_state_dict(checkpoint['model'])
    model.eval()
    return model

    
if __name__ == '__main__':
    model = load_and_evaluate_model()
    save_no_quantization(model)
