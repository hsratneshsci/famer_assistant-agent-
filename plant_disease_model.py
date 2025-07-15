import torch
import torch.nn as nn
from torchvision import models

class PlantDiseaseResNet18(nn.Module):
    def __init__(self, num_classes, pretrained=True):
        super(PlantDiseaseResNet18, self).__init__()
        self.model = models.resnet18(pretrained=pretrained)
        in_features = self.model.fc.in_features
        self.model.fc = nn.Linear(in_features, num_classes)

    def forward(self, x):
        return self.model(x)

def get_optimizer(model, optimizer_name='adamw', lr=1e-3, weight_decay=1e-4, **kwargs):
    """
    Returns an optimizer for the given model parameters.
    Supported: 'adam', 'adamw', 'rmsprop', 'sgd'
    """
    optimizer_name = optimizer_name.lower()
    if optimizer_name == 'adam':
        return torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay, **kwargs)
    elif optimizer_name == 'adamw':
        return torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay, **kwargs)
    elif optimizer_name == 'rmsprop':
        return torch.optim.RMSprop(model.parameters(), lr=lr, weight_decay=weight_decay, **kwargs)
    elif optimizer_name == 'sgd':
        return torch.optim.SGD(model.parameters(), lr=lr, weight_decay=weight_decay, momentum=0.9, **kwargs)
    else:
        raise ValueError(f"Unsupported optimizer: {optimizer_name}")

# Example usage:
# model = PlantDiseaseResNet18(num_classes=38, pretrained=True)
# optimizer = get_optimizer(model, optimizer_name='adamw', lr=1e-3) 