"""build_model disalin persis dari penelitian; adapter selalu pretrained=False."""
from torch import nn
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0


def build_model(pretrained=True):
    model = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None)
    in_features = model.classifier[-1].in_features
    model.classifier = nn.Sequential(nn.Dropout(p=0.2), nn.Linear(in_features, 1))
    model.features.requires_grad_(False)
    return model
