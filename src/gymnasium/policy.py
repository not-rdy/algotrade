import torch
import torch.nn as nn


class Policy_Network(nn.Module):

    def __init__(
            self,
            obs_space_dims: int, action_space_dims: int, device: str):
        super().__init__()

        hidden_space1 = 16  # Nothing special with 16, feel free to change
        hidden_space2 = 32  # Nothing special with 32, feel free to change

        # Shared Network
        self.shared_net = nn.Sequential(
            nn.Linear(obs_space_dims, hidden_space1).to(device),
            nn.Tanh().to(device),
            nn.Linear(hidden_space1, hidden_space2).to(device),
            nn.Tanh().to(device),
            nn.Linear(hidden_space2, action_space_dims).to(device),
            nn.Tanh().to(device)
        )

        # Policy SoftMax Layer
        self.policy_softmax = nn.Sequential(
            nn.Softmax(dim=1).to(device)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shared_features = self.shared_net(x.float())
        return self.policy_softmax(shared_features)
