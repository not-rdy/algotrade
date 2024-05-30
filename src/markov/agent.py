import os
import sys
sys.path.append(os.getcwd())
import numpy as np
import scipy as sp
import itertools
from sklearn.neighbors import NearestNeighbors
from typing import Set, Dict, Tuple, NewType

State = NewType('State', tuple)
Action = NewType('Action', Tuple[str, float, float])
Reward = NewType('Reward', float)
StateAction = NewType('StateAction', Tuple[int, int])
MatrixStateReward = NewType('MatrixStateReward', np.array)


class Agent:

    def __init__(
            self,
            states: Set[State], actions: Set[Action], rewards: Set[Reward]) -> None:  # noqa: E501

        self.states: Set[State] = states
        self.actions: Set[Action] = actions
        self.rewards = np.array(rewards)

        self.states_encoder: Dict[State, int] = {
            s: idx for idx, s in enumerate(states)}
        self.states_decoder: Dict[int, State] = {
            idx: s for idx, s in enumerate(states)}
        self.actions_encoder: Dict[Action, int] = {
            a: idx for idx, a in enumerate(actions)}
        self.actions_decoder: Dict[int, Action] = {
            idx: a for idx, a in enumerate(actions)}
        self.rewards_encoder: Dict[Reward, int] = {
            r: idx for idx, r in enumerate(rewards)}
        self.rewards_decoder: Dict[int, Reward] = {
            idx: r for idx, r in enumerate(rewards)}

        self.states_actions = itertools.product(
            self.states_decoder.keys(), self.actions_decoder.keys())
        self.history = []
        self.total_counts = 0
        self.counts: Dict[StateAction, MatrixStateReward] = self.__init_counts()  # noqa: E501
        self.probs: Dict[StateAction, MatrixStateReward] = self.counts.copy()

        # possible agent states: free, long, short
        self.agent_state = 'free'

        self.last_state: State = None
        self.last_action: Action = None
        self.nbrs = NearestNeighbors(n_neighbors=1, algorithm='ball_tree')\
            .fit(np.array(list(self.states_encoder.keys())))

    def release(self) -> None:
        self.agent_state = 'free'
        self.last_state = None
        self.last_action = None

    def __init_counts(self) -> Dict[StateAction, MatrixStateReward]:
        print('init counts...')
        counts = {}
        for sa in self.states_actions:
            sparse_matrix = sp.sparse.coo_array(
                (len(self.states), len(self.rewards)))
            counts.update({sa: sparse_matrix})
        return counts

    def __update(self, state: State, reward: Reward) -> None:
        if reward == 0 or self.last_action is None or self.last_state is None:
            return None
        # update counts
        idx_last_state = self.states_encoder.get(self.last_state)
        idx_last_action = self.actions_encoder.get(self.last_action)
        idx_new_state = self.states_encoder.get(state)
        idx_reward = self.rewards_encoder.get(reward)
        self.counts[(idx_last_state, idx_last_action)]\
            .tolil()[idx_new_state, idx_reward] += 1
        self.total_counts += 1
        # update probs
        self.probs[(idx_last_state, idx_last_action)] =\
            self.counts[(idx_last_state, idx_last_action)] / self.total_counts

    def __get_expected_rewards(self, state: State) -> Dict[Action, Reward]:
        # math expectation
        expected_rewards: Dict[Action, Reward] = {}
        idx_state = self.states_encoder.get(state)
        for action in self.actions:
            idx_action = self.actions_encoder.get(action)
            matrix_states_rewards = self.probs[(idx_state, idx_action)]
            rewards_probas = matrix_states_rewards.sum(axis=0)
            me_reward = (self.rewards * rewards_probas).sum()
            expected_rewards.update({action: me_reward})
        return expected_rewards

    def __choose_action(self, state: State, eps: float) -> Action:
        if self.agent_state != 'free':
            return ('none', 0, 0)
        expected_rewards = self.__get_expected_rewards(state)
        exploitation = np.random.choice(a=[True, False], p=[1 - eps, eps])
        if exploitation:
            return max(expected_rewards)
        else:
            max_action = max(expected_rewards)
            del expected_rewards[max_action]
            idx = np.random.choice(a=range(0, len(expected_rewards)))
            return list(expected_rewards.keys())[idx]

    def __update_agent_state(self, action: Action, reward: Reward) -> None:
        if self.agent_state == 'free':
            if action[0] == 'buy':
                self.agent_state = 'long'
            elif action[0] == 'sell':
                self.agent_state = 'short'
        if self.agent_state != 'free' and reward != 0:
            self.agent_state = 'free'
            return None

    def __get_nearest_state(self, state: State) -> State:
        _, idx_nearest_state = self.nbrs\
            .kneighbors(np.array(state).reshape(1, -1))
        return self.states_decoder.get(idx_nearest_state.item())

    def __append_to_history(
            self, state: State, action: Action, reward: Reward) -> None:
        if state is not None and action is not None:
            self.history.append(
                {
                    'state': state,
                    'action': action,
                    'reward': reward
                })

    def get_action(self, state: State, reward: Reward, eps: float) -> Action:
        state = self.__get_nearest_state(state)
        self.__update(state, reward)
        action = self.__choose_action(state, eps)
        self.__update_agent_state(action, reward)
        self.__append_to_history(state, action, reward)
        self.last_state, self.last_action = state, action
        return action
