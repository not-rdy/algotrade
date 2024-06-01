import torch
import numpy as np
from policy import Policy_Network


class REINFORCE:

    def __init__(self, obs_space_dims: int, action_space_dims: int):

        # Hyperparameters
        self.learning_rate = 1e-3  # Learning rate for policy optimization
        self.gamma = 0.99  # Discount factor
        self.eps = 1e-6  # small number for mathematical stability

        self.probs = []  # Stores probability values of the sampled action
        self.rewards = []  # Stores the corresponding rewards

        self.net = Policy_Network(obs_space_dims, action_space_dims)
        self.optimizer = torch.optim.Adam(
            self.net.parameters(), lr=self.learning_rate)

    def sample_action(self, state: np.ndarray) -> int:
        state = torch.tensor(np.array([state]))
        actions_distrib = self.net(state)
        argmax = torch.argmax(actions_distrib)
        self.probs.append(actions_distrib[0][argmax])
        return actions_distrib[0][argmax]

    def update(self):
        """Updates the policy network's weights."""
        running_g = 0
        gs = []

        # Discounted return (backwards) - [::-1] will return an array in reverse  # noqa: E501
        for R in self.rewards[::-1]:
            running_g = R + self.gamma * running_g
            gs.insert(0, running_g)

        deltas = torch.tensor(gs)

        loss = 0
        # minimize -1 * prob * reward obtained
        for prob, delta in zip(self.probs, deltas):
            loss += prob * delta * -1

        # Update the policy network
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Empty / zero out all episode-centric/related variables
        self.probs = []
        self.rewards = []
