from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from agent import DQNAgent
from env import StudentEnv


BASE_DIR = Path(__file__).resolve().parent
REWARD_CURVE_PATH = BASE_DIR / "reward_curve.png"
MODEL_PATH = BASE_DIR / "dqn_best.pt"


def train(num_episodes=500):
    env = StudentEnv(seed=42)
    agent = DQNAgent(device="cpu")
    rewards = []
    best_avg_reward = -float("inf")

    for episode in range(1, num_episodes + 1):
        state = env.reset()
        total_reward = 0.0
        done = False

        while not done:
            action = agent.select_action(state)
            next_state, reward, done, _ = env.step(action)
            agent.store_transition(state, action, reward, next_state, done)
            agent.train_step()
            state = next_state
            total_reward += reward

        rewards.append(total_reward)
        print(f"Episode {episode:03d} | Reward: {total_reward:.3f} | Epsilon: {agent.epsilon:.3f}")

        if episode % 50 == 0:
            avg_reward = float(np.mean(rewards[-50:]))
            print(f"Average reward over last 50 episodes: {avg_reward:.3f}")
            agent.update_target_network()
            if avg_reward > best_avg_reward:
                best_avg_reward = avg_reward
                torch.save(agent.online_net.state_dict(), MODEL_PATH)
                print(f"Saved best DQN weights to {MODEL_PATH}")

    if not MODEL_PATH.exists():
        torch.save(agent.online_net.state_dict(), MODEL_PATH)
        print(f"Saved DQN weights to {MODEL_PATH}")

    plt.figure(figsize=(8, 5))
    plt.plot(rewards, linewidth=1.2)
    if len(rewards) >= 20:
        moving_avg = np.convolve(rewards, np.ones(20) / 20, mode="valid")
        plt.plot(range(19, len(rewards)), moving_avg, linewidth=2.0, label="20-episode average")
        plt.legend()
    plt.title("DQN Training Reward")
    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    plt.tight_layout()
    plt.savefig(REWARD_CURVE_PATH, dpi=150)
    print(f"Saved reward curve to {REWARD_CURVE_PATH}")
    return rewards


if __name__ == "__main__":
    train()
