"""
Neural network models for federated learning simulation.

Provides simple CNN and MLP architectures suitable for IoT device simulation,
along with utility functions for weight serialization/deserialization.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import copy
from collections import OrderedDict


class SimpleCNN(nn.Module):
    """
    Simple CNN for CIFAR-10 classification.
    Architecture: 2 Conv layers + 2 FC layers.
    Designed to be lightweight for IoT simulation.
    """

    def __init__(self, num_classes=10):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 8 * 8, 256)
        self.fc2 = nn.Linear(256, num_classes)
        self.dropout = nn.Dropout(0.25)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)
        x = self.dropout(F.relu(self.fc1(x)))
        x = self.fc2(x)
        return x


class SimpleMLP(nn.Module):
    """
    Simple MLP for MNIST classification.
    Architecture: 2 FC layers.
    Fastest option for initial experiments.
    """

    def __init__(self, input_dim=784, hidden_dim=200, num_classes=10):
        super(SimpleMLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x


class HARMLPModel(nn.Module):
    """
    MLP for UCI HAR (Human Activity Recognition) — 561 hand-crafted
    smartphone-sensor features → 6 activity classes.
    Architecture: 561 → 128 → 64 → 6 with ReLU + Dropout.
    """

    def __init__(self, input_dim=561, num_classes=6):
        super(HARMLPModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, num_classes)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def get_model(dataset_name, device='cpu'):
    """
    Factory function to get the appropriate model for a dataset.

    Args:
        dataset_name: one of 'cifar10', 'mnist', 'fashion_mnist', 'har'
        device: torch device

    Returns:
        nn.Module on the specified device
    """
    if dataset_name == 'cifar10':
        model = SimpleCNN(num_classes=10)
    elif dataset_name in ('mnist', 'fashion_mnist'):
        model = SimpleMLP(input_dim=784, hidden_dim=200, num_classes=10)
    elif dataset_name == 'har':
        model = HARMLPModel(input_dim=561, num_classes=6)
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    return model.to(device)


def get_model_weights(model):
    """
    Extract model weights as a flat 1D numpy array.
    Used for gradient space clustering (MDBSCAN etc.).

    Args:
        model: nn.Module

    Returns:
        numpy array of all parameters concatenated
    """
    weights = []
    for param in model.parameters():
        weights.append(param.data.cpu().numpy().flatten())
    import numpy as np
    return np.concatenate(weights)


def set_model_weights(model, flat_weights):
    """
    Load a flat weight vector back into a model.

    Args:
        model: nn.Module
        flat_weights: numpy array of concatenated parameters
    """
    import numpy as np
    offset = 0
    for param in model.parameters():
        param_length = param.numel()
        param_shape = param.shape
        param_data = flat_weights[offset:offset + param_length]
        param.data = torch.tensor(
            param_data.reshape(param_shape),
            dtype=param.dtype,
            device=param.device
        )
        offset += param_length


def get_state_dict_flat(state_dict):
    """
    Convert an OrderedDict state_dict to a flat numpy array.

    Args:
        state_dict: model.state_dict()

    Returns:
        numpy array
    """
    import numpy as np
    return np.concatenate([v.cpu().numpy().flatten() for v in state_dict.values()])


def set_state_dict_from_flat(model, flat_weights):
    """
    Set model state_dict from a flat numpy array.

    Args:
        model: nn.Module
        flat_weights: numpy array
    """
    import numpy as np
    new_state_dict = OrderedDict()
    offset = 0
    for key, param in model.state_dict().items():
        param_length = param.numel()
        param_shape = param.shape
        param_data = flat_weights[offset:offset + param_length]
        new_state_dict[key] = torch.tensor(
            param_data.reshape(param_shape),
            dtype=param.dtype
        )
        offset += param_length
    model.load_state_dict(new_state_dict)
