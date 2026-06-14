# Strategy Intelligence V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement enhanced RL (DQN, A2C, PPO, SAC, TD3, DDPG, multi-agent, offline), risk management (VaR, CVaR, stress testing, attribution), and monitoring/alerting system.

**Architecture:** Modular design with independent modules per algorithm, shared network architectures, database-backed storage.

**Tech Stack:** Python, PyTorch, Gymnasium, SQLite, NumPy, Pandas

---

## Stage 2: Reinforcement Learning Enhancement

### Task 2.1: Deep RL Neural Networks

**Files:**
- Create: `core/rl/deep/__init__.py`
- Create: `core/rl/deep/networks.py`
- Create: `core/rl/deep/replay_buffer.py`
- Test: `tests/unit/test_rl_networks.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_rl_networks.py
import pytest
import torch
import numpy as np

def test_dqn_network():
    from core.rl.deep.networks import DQNNetwork
    net = DQNNetwork(state_dim=10, action_dim=5, hidden_dim=64)
    state = torch.randn(1, 10)
    q = net(state)
    assert q.shape == (1, 5)

def test_gaussian_actor():
    from core.rl.deep.networks import GaussianActor
    actor = GaussianActor(state_dim=10, action_dim=5, hidden_dim=64)
    state = torch.randn(1, 10)
    action, log_prob = actor.sample(state)
    assert action.shape == (1, 5)
    assert log_prob.shape == (1, 1)

def test_critic():
    from core.rl.deep.networks import TwinCritic
    critic = TwinCritic(state_dim=10, action_dim=5, hidden_dim=64)
    state = torch.randn(1, 10)
    action = torch.randn(1, 5)
    q = critic(state, action)
    assert q.shape == (1, 1)

def test_replay_buffer():
    from core.rl.deep.replay_buffer import ReplayBuffer
    buf = ReplayBuffer(1000)
    for _ in range(100):
        buf.push(np.random.randn(10), 0, 1.0, np.random.randn(10), False)
    batch = buf.sample(32)
    assert len(batch) == 5
    assert batch[0].shape == (32, 10)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement networks and replay buffer**

```python
# core/rl/deep/__init__.py
from .networks import DQNNetwork, GaussianActor, TwinCritic
from .replay_buffer import ReplayBuffer, PrioritizedReplayBuffer

# core/rl/deep/networks.py
import torch
import torch.nn as nn
import torch.nn.functional as F

class DQNNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    def forward(self, x): return self.net(x)

class GaussianActor(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(state_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim), nn.ReLU())
        self.mean = nn.Linear(hidden_dim, action_dim)
        self.log_std = nn.Linear(hidden_dim, action_dim)
    def forward(self, x):
        h = self.fc(x)
        return self.mean(h), self.log_std(h).clamp(-20, 2)
    def sample(self, x):
        mean, log_std = self.forward(x)
        std = log_std.exp()
        normal = torch.distributions.Normal(mean, std)
        x_t = normal.rsample()
        action = torch.tanh(x_t)
        log_prob = normal.log_prob(x_t) - torch.log(1 - action.pow(2) + 1e-6)
        return action, log_prob.sum(-1, keepdim=True)

class TwinCritic(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super().__init__()
        self.q1 = nn.Sequential(nn.Linear(state_dim+action_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, 1))
        self.q2 = nn.Sequential(nn.Linear(state_dim+action_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, 1))
    def forward(self, state, action):
        sa = torch.cat([state, action], -1)
        return torch.min(self.q1(sa), self.q2(sa))

# core/rl/deep/replay_buffer.py
import random, numpy as np

class ReplayBuffer:
    def __init__(self, capacity):
        self.buf = []; self.pos = 0; self.cap = capacity
    def push(self, s, a, r, ns, d):
        if len(self.buf) < self.cap: self.buf.append(None)
        self.buf[self.pos] = (s,a,r,ns,d); self.pos = (self.pos+1)%self.cap
    def sample(self, n):
        batch = random.sample(self.buf, n)
        s,a,r,ns,d = zip(*batch)
        return np.array(s),np.array(a),np.array(r),np.array(ns),np.array(d)
    def __len__(self): return len(self.buf)

class PrioritizedReplayBuffer:
    def __init__(self, capacity, alpha=0.6):
        self.buf=[]; self.priorities=[]; self.pos=0; self.cap=capacity; self.alpha=alpha
    def push(self, s, a, r, ns, d):
        mx = max(self.priorities) if self.priorities else 1.0
        if len(self.buf)<self.cap: self.buf.append(None); self.priorities.append(None)
        self.buf[self.pos]=(s,a,r,ns,d); self.priorities[self.pos]=mx; self.pos=(self.pos+1)%self.cap
    def sample(self, n, beta=0.4):
        p = np.array(self.priorities[:len(self.buf)])**self.alpha; p/=p.sum()
        idx = np.random.choice(len(self.buf), n, p=p)
        w = (len(self.buf)*p[idx])**(-beta); w/=w.max()
        batch = [self.buf[i] for i in idx]
        s,a,r,ns,d = zip(*batch)
        return np.array(s),np.array(a),np.array(r),np.array(ns),np.array(d),idx,w
    def update_priorities(self, idx, pri):
        for i,p in zip(idx,pri): self.priorities[i]=p+1e-5
    def __len__(self): return len(self.buf)
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 2.2: DQN and Actor-Critic Trainers

**Files:**
- Create: `core/rl/deep/trainers.py`
- Test: `tests/unit/test_trainers.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_trainers.py
import pytest
import numpy as np

def test_dqn_trainer():
    from core.rl.deep.trainers import DQNTrainer
    from core.rl.deep.networks import DQNNetwork
    from core.rl.deep.replay_buffer import ReplayBuffer

    class DummyEnv:
        observation_space = type('S', (), {'shape': (10,)})()
        action_space = type('A', (), {'n': 5, 'sample': lambda self: np.random.randint(5)})()
        def reset(self): return np.random.randn(10), {}
        def step(self, a): return np.random.randn(10), 1.0, False, False, {}

    env = DummyEnv()
    net = DQNNetwork(10, 5, 32)
    buf = ReplayBuffer(100)
    trainer = DQNTrainer(env, net, buf, gamma=0.99)
    rewards = trainer.train(num_episodes=2, max_steps=10)
    assert len(rewards) == 2

def test_sac():
    from core.rl.advanced.sac import SAC
    sac = SAC(state_dim=10, action_dim=2, hidden_dim=32)
    action = sac.select_action(np.random.randn(10))
    assert action.shape == (2,)

def test_td3():
    from core.rl.advanced.td3 import TD3
    td3 = TD3(state_dim=10, action_dim=2, hidden_dim=32)
    action = td3.select_action(np.random.randn(10))
    assert action.shape == (2,)

def test_ddpg():
    from core.rl.advanced.ddpg import DDPG
    ddpg = DDPG(state_dim=10, action_dim=2, hidden_dim=32)
    action = ddpg.select_action(np.random.randn(10))
    assert action.shape == (2,)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement trainers**

```python
# core/rl/deep/trainers.py
import copy, random, numpy as np, torch, torch.nn.functional as F

class DQNTrainer:
    def __init__(self, env, network, replay_buffer, gamma=0.99, eps_start=1.0, eps_end=0.01, eps_decay=1000, target_update=100, lr=1e-3, batch_size=32):
        self.env=env; self.net=network; self.target=copy.deepcopy(network); self.buf=replay_buffer
        self.gamma=gamma; self.eps_start=eps_start; self.eps_end=eps_end; self.eps_decay=eps_decay
        self.target_update=target_update; self.batch_size=batch_size; self.steps=0
        self.opt=torch.optim.Adam(network.parameters(), lr=lr)

    def train(self, num_episodes=1000, max_steps=200):
        rewards=[]
        for ep in range(num_episodes):
            s,_ = self.env.reset(); R=0
            for _ in range(max_steps):
                a = self._select_action(s)
                ns,r,term,trunc,_ = self.env.step(a)
                self.buf.push(s,a,r,ns,term or trunc)
                if len(self.buf)>=self.batch_size: self._update()
                if self.steps%self.target_update==0: self.target.load_state_dict(self.net.state_dict())
                s=ns; R+=r; self.steps+=1
                if term or trunc: break
            rewards.append(R)
        return rewards

    def _select_action(self, s):
        eps = self.eps_end+(self.eps_start-self.eps_end)*np.exp(-self.steps/self.eps_decay)
        if random.random()>eps:
            with torch.no_grad(): return self.net(torch.FloatTensor(s).unsqueeze(0)).argmax().item()
        return self.env.action_space.sample()

    def _update(self):
        s,a,r,ns,d = self.buf.sample(self.batch_size)
        s,a,r,ns,d = torch.FloatTensor(s),torch.LongTensor(a),torch.FloatTensor(r),torch.FloatTensor(ns),torch.FloatTensor(d)
        q = self.net(s).gather(1,a.unsqueeze(1)).squeeze()
        with torch.no_grad(): tq = r+self.gamma*self.target(ns).max(1)[0]*(1-d)
        loss = F.mse_loss(q,tq)
        self.opt.zero_grad(); loss.backward(); self.opt.step()

# core/rl/deep/__init__.py (updated)
from .networks import DQNNetwork, GaussianActor, TwinCritic
from .replay_buffer import ReplayBuffer, PrioritizedReplayBuffer
from .trainers import DQNTrainer
```

```python
# core/rl/advanced/__init__.py
from .sac import SAC
from .td3 import TD3
from .ddpg import DDPG

# core/rl/advanced/sac.py
import copy, numpy as np, torch, torch.nn.functional as F
from ..deep.networks import GaussianActor, TwinCritic

class SAC:
    def __init__(self, state_dim, action_dim, hidden_dim=256, gamma=0.99, tau=0.005, alpha=0.2, lr=3e-4):
        self.gamma=gamma; self.tau=tau; self.alpha=alpha
        self.actor = GaussianActor(state_dim, action_dim, hidden_dim)
        self.critic = TwinCritic(state_dim, action_dim, hidden_dim)
        self.target_critic = copy.deepcopy(self.critic)
        self.a_opt = torch.optim.Adam(self.actor.parameters(), lr=lr)
        self.c_opt = torch.optim.Adam(self.critic.parameters(), lr=lr)
        self.target_entropy = -action_dim
        self.log_alpha = torch.zeros(1, requires_grad=True)
        self.alpha_opt = torch.optim.Adam([self.log_alpha], lr=lr)

    def select_action(self, state, deterministic=False):
        with torch.no_grad():
            a,_ = self.actor.sample(torch.FloatTensor(state).unsqueeze(0))
        return a.numpy()[0]

    def update(self, batch):
        s,a,r,ns,d = [torch.FloatTensor(x) for x in batch]
        r,d = r.unsqueeze(1), d.unsqueeze(1)
        with torch.no_grad():
            na,lp = self.actor.sample(ns)
            q = torch.min(self.critic(ns,na), self.critic(ns,na))
            tq = r+self.gamma*(1-d)*(q-self.alpha*lp)
        cq = self.critic(s,a)
        c_loss = F.mse_loss(cq, tq)
        self.c_opt.zero_grad(); c_loss.backward(); self.c_opt.step()
        na2,lp2 = self.actor.sample(s)
        a_loss = -(self.critic(s,na2).mean() + self.alpha*lp2.mean())
        self.a_opt.zero_grad(); a_loss.backward(); self.a_opt.step()
        al = -(self.log_alpha*(lp2+self.target_entropy).detach()).mean()
        self.alpha_opt.zero_grad(); al.backward(); self.alpha_opt.step()
        self.alpha = self.log_alpha.exp().item()
        for p,tp in zip(self.critic.parameters(),self.target_critic.parameters()):
            tp.data.copy_(self.tau*p.data+(1-self.tau)*tp.data)

# core/rl/advanced/td3.py
import copy, numpy as np, torch, torch.nn.functional as F
from ..deep.networks import GaussianActor, TwinCritic

class TD3:
    def __init__(self, state_dim, action_dim, hidden_dim=256, gamma=0.99, tau=0.005, policy_noise=0.2, noise_clip=0.5, policy_delay=2, lr=3e-4):
        self.gamma=gamma; self.tau=tau; self.pn=policy_noise; self.nc=noise_clip; self.pd=policy_delay; self.updates=0
        self.actor=GaussianActor(state_dim,action_dim,hidden_dim); self.t_actor=copy.deepcopy(self.actor)
        self.critic=TwinCritic(state_dim,action_dim,hidden_dim); self.t_critic=copy.deepcopy(self.critic)
        self.a_opt=torch.optim.Adam(self.actor.parameters(),lr=lr); self.c_opt=torch.optim.Adam(self.critic.parameters(),lr=lr)

    def select_action(self, state, noise=0.1):
        with torch.no_grad(): a,_=self.actor.sample(torch.FloatTensor(state).unsqueeze(0))
        a=a.numpy()[0]
        if noise>0: a+=np.random.randn(*a.shape)*noise
        return np.clip(a,-1,1)

    def update(self, batch):
        self.updates+=1; s,a,r,ns,d=[torch.FloatTensor(x) for x in batch]; r,d=r.unsqueeze(1),d.unsqueeze(1)
        with torch.no_grad():
            n=(torch.randn_like(a)*self.pn).clamp(-self.nc,self.nc)
            na=(self.t_actor(ns)[0]+n).clamp(-1,1)
            tq=r+self.gamma*(1-d)*torch.min(self.t_critic(ns,na),self.t_critic(ns,na))
        cl=F.mse_loss(self.critic(s,a),tq); self.c_opt.zero_grad(); cl.backward(); self.c_opt.step()
        if self.updates%self.pd==0:
            al=-self.critic(s,self.actor(s)[0]).mean(); self.a_opt.zero_grad(); al.backward(); self.a_opt.step()
            for p,tp in zip(self.actor.parameters(),self.t_actor.parameters()): tp.data.copy_(self.tau*p.data+(1-self.tau)*tp.data)
            for p,tp in zip(self.critic.parameters(),self.t_critic.parameters()): tp.data.copy_(self.tau*p.data+(1-self.tau)*tp.data)

# core/rl/advanced/ddpg.py
import copy, numpy as np, torch, torch.nn.functional as F
from ..deep.networks import GaussianActor, TwinCritic

class DDPG:
    def __init__(self, state_dim, action_dim, hidden_dim=256, gamma=0.99, tau=0.005, lr=3e-4):
        self.gamma=gamma; self.tau=tau
        self.actor=GaussianActor(state_dim,action_dim,hidden_dim); self.t_actor=copy.deepcopy(self.actor)
        self.critic=TwinCritic(state_dim,action_dim,hidden_dim); self.t_critic=copy.deepcopy(self.critic)
        self.a_opt=torch.optim.Adam(self.actor.parameters(),lr=lr); self.c_opt=torch.optim.Adam(self.critic.parameters(),lr=lr)

    def select_action(self, state, noise=0.1):
        with torch.no_grad(): a,_=self.actor.sample(torch.FloatTensor(state).unsqueeze(0))
        a=a.numpy()[0]
        if noise>0: a+=np.random.randn(*a.shape)*noise
        return np.clip(a,-1,1)

    def update(self, batch):
        s,a,r,ns,d=[torch.FloatTensor(x) for x in batch]; r,d=r.unsqueeze(1),d.unsqueeze(1)
        with torch.no_grad():
            tq=r+self.gamma*(1-d)*self.t_critic(ns,self.t_actor(ns)[0])
        cl=F.mse_loss(self.critic(s,a),tq); self.c_opt.zero_grad(); cl.backward(); self.c_opt.step()
        al=-self.critic(s,self.actor(s)[0]).mean(); self.a_opt.zero_grad(); al.backward(); self.a_opt.step()
        for p,tp in zip(self.actor.parameters(),self.t_actor.parameters()): tp.data.copy_(self.tau*p.data+(1-self.tau)*tp.data)
        for p,tp in zip(self.critic.parameters(),self.t_critic.parameters()): tp.data.copy_(self.tau*p.data+(1-self.tau)*tp.data)
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 2.3: Multi-Agent RL (MADDPG)

**Files:**
- Create: `core/rl/multi_agent/__init__.py`
- Create: `core/rl/multi_agent/algorithms/__init__.py`
- Create: `core/rl/multi_agent/algorithms/maddpg.py`
- Test: `tests/unit/test_maddpg.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_maddpg.py
import numpy as np

def test_maddpg_init():
    from core.rl.multi_agent.algorithms.maddpg import MADDPG
    m = MADDPG(num_agents=2, state_dims=[10,10], action_dims=[5,5], hidden_dim=32)
    assert m.num_agents == 2
    assert len(m.actors) == 2

def test_maddpg_select():
    from core.rl.multi_agent.algorithms.maddpg import MADDPG
    m = MADDPG(num_agents=2, state_dims=[10,10], action_dims=[5,5], hidden_dim=32)
    actions = m.select_actions([np.random.randn(10), np.random.randn(10)])
    assert len(actions) == 2
    assert actions[0].shape == (5,)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement MADDPG**

```python
# core/rl/multi_agent/__init__.py
from .algorithms.maddpg import MADDPG

# core/rl/multi_agent/algorithms/__init__.py
from .maddpg import MADDPG

# core/rl/multi_agent/algorithms/maddpg.py
import copy, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from ...deep.networks import GaussianActor, TwinCritic

class MADDPG:
    def __init__(self, num_agents, state_dims, action_dims, hidden_dim=256, gamma=0.95, tau=0.01, lr=1e-4):
        self.num_agents=num_agents; self.gamma=gamma; self.tau=tau
        self.actors=[GaussianActor(sd,ad,hidden_dim) for sd,ad in zip(state_dims,action_dims)]
        self.t_actors=[copy.deepcopy(a) for a in self.actors]
        total_sd=sum(state_dims); total_ad=sum(action_dims)
        self.critics=[TwinCritic(total_sd,total_ad,hidden_dim) for _ in range(num_agents)]
        self.t_critics=[copy.deepcopy(c) for c in self.critics]
        self.a_opts=[torch.optim.Adam(a.parameters(),lr=lr) for a in self.actors]
        self.c_opts=[torch.optim.Adam(c.parameters(),lr=lr) for c in self.critics]

    def select_actions(self, states):
        actions=[]
        for i,(a,s) in enumerate(zip(self.actors,states)):
            with torch.no_grad(): act,_=a.sample(torch.FloatTensor(s).unsqueeze(0))
            actions.append(act.numpy()[0])
        return actions

    def update(self, batch):
        states,actions,rewards,next_states,dones=batch
        s=[torch.FloatTensor(x) for x in states]
        a=[torch.FloatTensor(x) for x in actions]
        r=[torch.FloatTensor(x).unsqueeze(1) for x in rewards]
        ns=[torch.FloatTensor(x) for x in next_states]
        d=[torch.FloatTensor(x).unsqueeze(1) for x in dones]
        all_s=torch.cat(s,1); all_a=torch.cat(a,1); all_ns=torch.cat(ns,1)
        for i in range(self.num_agents):
            with torch.no_grad():
                na=[self.t_actors[j](ns[j])[0] for j in range(self.num_agents)]
                tq=r[i]+self.gamma*(1-d[i])*self.t_critics[i](all_ns,torch.cat(na,1))
            cl=F.mse_loss(self.critics[i](all_s,all_a),tq)
            self.c_opts[i].zero_grad(); cl.backward(); self.c_opts[i].step()
            al=-self.critics[i](all_s,torch.cat([self.actors[j](s[j])[0] if j==i else a[j].detach() for j in range(self.num_agents)],1)).mean()
            self.a_opts[i].zero_grad(); al.backward(); self.a_opts[i].step()
            for p,tp in zip(self.actors[i].parameters(),self.t_actors[i].parameters()): tp.data.copy_(self.tau*p.data+(1-self.tau)*tp.data)
            for p,tp in zip(self.critics[i].parameters(),self.t_critics[i].parameters()): tp.data.copy_(self.tau*p.data+(1-self.tau)*tp.data)
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 2.4: Offline RL (CQL)

**Files:**
- Create: `core/rl/offline/__init__.py`
- Create: `core/rl/offline/conservative.py`
- Test: `tests/unit/test_offline_rl.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_offline_rl.py
import numpy as np

def test_cql_init():
    from core.rl.offline.conservative import CQL
    cql = CQL(state_dim=10, action_dim=2, hidden_dim=32)
    assert cql.alpha == 1.0

def test_cql_select():
    from core.rl.offline.conservative import CQL
    cql = CQL(state_dim=10, action_dim=2, hidden_dim=32)
    a = cql.select_action(np.random.randn(10))
    assert a.shape == (2,)

def test_offline_dataset():
    from core.rl.offline.dataset import OfflineDataset
    import tempfile, os
    d = tempfile.mkdtemp()
    data = {'states':np.random.randn(100,10),'actions':np.random.randn(100,2),'rewards':np.random.randn(100),'next_states':np.random.randn(100,10),'dones':np.zeros(100)}
    np.savez(os.path.join(d,'data.npz'),**data)
    ds = OfflineDataset(os.path.join(d,'data.npz'))
    batch = ds.sample(32)
    assert batch[0].shape == (32,10)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement offline RL**

```python
# core/rl/offline/__init__.py
from .conservative import CQL
from .dataset import OfflineDataset

# core/rl/offline/dataset.py
import numpy as np

class OfflineDataset:
    def __init__(self, path):
        data = np.load(path)
        self.states=data['states']; self.actions=data['actions']
        self.rewards=data['rewards']; self.next_states=data['next_states']
        self.dones=data['dones']; self.size=len(self.rewards)
    def sample(self, n):
        idx=np.random.choice(self.size,n)
        return self.states[idx],self.actions[idx],self.rewards[idx],self.next_states[idx],self.dones[idx]

# core/rl/offline/conservative.py
import copy, numpy as np, torch, torch.nn.functional as F
from ..deep.networks import GaussianActor, TwinCritic

class CQL:
    def __init__(self, state_dim, action_dim, hidden_dim=256, gamma=0.99, tau=0.005, alpha=1.0, lr=3e-4):
        self.gamma=gamma; self.tau=tau; self.alpha=alpha
        self.actor=GaussianActor(state_dim,action_dim,hidden_dim)
        self.critic=TwinCritic(state_dim,action_dim,hidden_dim)
        self.t_critic=copy.deepcopy(self.critic)
        self.a_opt=torch.optim.Adam(self.actor.parameters(),lr=lr)
        self.c_opt=torch.optim.Adam(self.critic.parameters(),lr=lr)

    def select_action(self, state):
        with torch.no_grad(): a,_=self.actor.sample(torch.FloatTensor(state).unsqueeze(0))
        return a.numpy()[0]

    def update(self, batch):
        s,a,r,ns,d=[torch.FloatTensor(x) for x in batch]; r,d=r.unsqueeze(1),d.unsqueeze(1)
        with torch.no_grad():
            na,lp=self.actor.sample(ns)
            tq=r+self.gamma*(1-d)*(self.t_critic(ns,na)-self.alpha*lp)
        q=self.critic(s,a)
        # CQL penalty
        with torch.no_grad(): ra=torch.randn_like(a)
        q_rand=torch.min(self.critic(s,ra),self.critic(s,ra))
        cql_loss=(q_rand.logsumexp(0)-q.mean())*self.alpha
        cl=F.mse_loss(q,tq)+cql_loss
        self.c_opt.zero_grad(); cl.backward(); self.c_opt.step()
        na2,lp2=self.actor.sample(s)
        al=-(self.critic(s,na2).mean()+self.alpha*lp2.mean())
        self.a_opt.zero_grad(); al.backward(); self.a_opt.step()
        for p,tp in zip(self.critic.parameters(),self.t_critic.parameters()): tp.data.copy_(self.tau*p.data+(1-self.tau)*tp.data)
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

## Stage 3: Risk Management Upgrade

### Task 3.1: VaR and CVaR Calculators

**Files:**
- Create: `core/risk/monitoring/__init__.py`
- Create: `core/risk/monitoring/var_calculator.py`
- Create: `core/risk/monitoring/cvar_calculator.py`
- Test: `tests/unit/test_risk_monitoring.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_risk_monitoring.py
import numpy as np
import pandas as pd

def test_var_historical():
    from core.risk.monitoring.var_calculator import VaRCalculator
    returns = pd.Series(np.random.randn(1000)*0.01)
    calc = VaRCalculator(confidence=0.95)
    var = calc.historical(returns)
    assert var > 0

def test_var_parametric():
    from core.risk.monitoring.var_calculator import VaRCalculator
    returns = pd.Series(np.random.randn(1000)*0.01)
    calc = VaRCalculator(confidence=0.95)
    var = calc.parametric(returns)
    assert var > 0

def test_cvar():
    from core.risk.monitoring.cvar_calculator import CVaRCalculator
    returns = pd.Series(np.random.randn(1000)*0.01)
    calc = CVaRCalculator(confidence=0.95)
    cvar = calc.calculate(returns)
    assert cvar > 0

def test_stress_testing():
    from core.risk.monitoring.stress_testing import StressTesting
    portfolio = {'AAPL': {'value': 100000, 'beta': 1.2}, 'GOOG': {'value': 50000, 'beta': 0.8}}
    st = StressTesting(portfolio)
    scenarios = st.hypothetical_scenarios()
    assert len(scenarios) > 0

def test_risk_attribution():
    from core.risk.monitoring.risk_attribution import RiskAttribution
    ra = RiskAttribution()
    result = ra.factor_attribution({'market': 0.5, 'size': 0.3}, {'market': 0.02, 'size': 0.01})
    assert 'total' in result
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement risk monitoring**

```python
# core/risk/monitoring/__init__.py
from .var_calculator import VaRCalculator
from .cvar_calculator import CVaRCalculator
from .stress_testing import StressTesting
from .risk_attribution import RiskAttribution

# core/risk/monitoring/var_calculator.py
import numpy as np, pandas as pd
from scipy.stats import norm

class VaRCalculator:
    def __init__(self, confidence=0.95): self.conf=confidence
    def historical(self, returns, period=1):
        return -np.percentile(returns, (1-self.conf)*100)*np.sqrt(period)
    def parametric(self, returns, period=1):
        mu, sigma = returns.mean(), returns.std()
        return -(mu-norm.ppf(self.conf)*sigma)*np.sqrt(period)
    def monte_carlo(self, returns, period=1, n_sims=10000):
        mu, sigma = returns.mean(), returns.std()
        sims = np.random.normal(mu, sigma, (n_sims, period))
        return -np.percentile(sims.sum(axis=1), (1-self.conf)*100)

# core/risk/monitoring/cvar_calculator.py
import numpy as np

class CVaRCalculator:
    def __init__(self, confidence=0.95): self.conf=confidence
    def calculate(self, returns):
        sorted_r = np.sort(returns)
        cutoff = int((1-self.conf)*len(sorted_r))
        return -sorted_r[:cutoff].mean() if cutoff>0 else -sorted_r[0]

# core/risk/monitoring/stress_testing.py
class StressTesting:
    def __init__(self, portfolio): self.portfolio=portfolio
    def hypothetical_scenarios(self):
        return [
            {'name':'Market Drop 10%','shock':-0.10,'impact':self._impact(-0.10)},
            {'name':'Market Drop 20%','shock':-0.20,'impact':self._impact(-0.20)},
            {'name':'Volatility 2x','vol_mult':2.0},
            {'name':'Rate Rise 200bp','rate_shock':0.02},
        ]
    def _impact(self, shock):
        total=sum(p['value'] for p in self.portfolio.values())
        return sum(p['value']*shock*p.get('beta',1.0) for p in self.portfolio.values())/total

# core/risk/monitoring/risk_attribution.py
class RiskAttribution:
    def factor_attribution(self, exposures, factor_returns):
        total = sum(exposures.get(f,0)*factor_returns.get(f,0) for f in set(list(exposures.keys())+list(factor_returns.keys())))
        return {'factors':{f: exposures.get(f,0)*factor_returns.get(f,0) for f in set(list(exposures.keys())+list(factor_returns.keys()))},'total':total}
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 3.2: Dynamic Position Management

**Files:**
- Create: `core/risk/position/__init__.py`
- Create: `core/risk/position/kelly_criterion.py`
- Create: `core/risk/position/volatility_targeting.py`
- Test: `tests/unit/test_position.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_position.py
import numpy as np

def test_kelly():
    from core.risk.position.kelly_criterion import KellyCriterion
    k = KellyCriterion()
    f = k.calculate(win_rate=0.6, win_loss_ratio=2.0)
    assert 0 < f <= 0.5

def test_fractional_kelly():
    from core.risk.position.kelly_criterion import KellyCriterion
    k = KellyCriterion()
    f = k.fractional(win_rate=0.6, win_loss_ratio=2.0, fraction=0.5)
    assert 0 < f <= 0.25

def test_volatility_targeting():
    from core.risk.position.volatility_targeting import VolatilityTargeting
    vt = VolatilityTargeting(target_vol=0.15)
    returns = np.random.randn(100)*0.01
    size = vt.calculate_position_size(returns)
    assert 0.1 <= size <= 2.0

def test_regime_based():
    from core.risk.position.regime_based import RegimeBasedPosition
    rb = RegimeBasedPosition()
    size = rb.get_position_size('TRENDING')
    assert size > 0
    size = rb.get_position_size('CRISIS')
    assert size < 1.0
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement position management**

```python
# core/risk/position/__init__.py
from .kelly_criterion import KellyCriterion
from .volatility_targeting import VolatilityTargeting
from .regime_based import RegimeBasedPosition

# core/risk/position/kelly_criterion.py
class KellyCriterion:
    def __init__(self, risk_free=0.02): self.rf=risk_free
    def calculate(self, win_rate, win_loss_ratio):
        f = (win_rate*win_loss_ratio-(1-win_rate))/win_loss_ratio
        return max(0, min(f, 0.5))
    def fractional(self, win_rate, win_loss_ratio, fraction=0.5):
        return self.calculate(win_rate, win_loss_ratio)*fraction

# core/risk/position/volatility_targeting.py
import numpy as np

class VolatilityTargeting:
    def __init__(self, target_vol=0.15, lookback=20): self.tv=target_vol; self.lb=lookback
    def calculate_position_size(self, returns):
        vol = np.std(returns[-self.lb:])*np.sqrt(252)
        if vol==0: return 1.0
        size = self.tv/vol
        return max(0.1, min(size, 2.0))

# core/risk/position/regime_based.py
class RegimeBasedPosition:
    REGIMES = {'QUIET':1.0, 'TRENDING':1.2, 'VOLATILE':0.6, 'CRISIS':0.2}
    def get_position_size(self, regime): return self.REGIMES.get(regime, 1.0)
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

## Stage 4: Monitoring & Alerting System

### Task 4.1: Metrics Collection and Time Series DB

**Files:**
- Create: `monitoring/__init__.py`
- Create: `monitoring/dashboard/__init__.py`
- Create: `monitoring/dashboard/metrics_collector.py`
- Create: `monitoring/dashboard/time_series_db.py`
- Test: `tests/unit/test_monitoring.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_monitoring.py
import time

def test_metrics_collector():
    from monitoring.dashboard.metrics_collector import MetricsCollector
    mc = MetricsCollector()
    mc.register('cpu', lambda: 45.0)
    mc.collect()
    assert mc.get('cpu') == 45.0

def test_time_series_db():
    from monitoring.dashboard.time_series_db import TimeSeriesDB
    import tempfile, os
    db = TimeSeriesDB(os.path.join(tempfile.mkdtemp(), 'test.db'))
    db.insert('cpu', 45.0, {'host':'vps1'})
    db.insert('cpu', 46.0, {'host':'vps1'})
    rows = db.query('cpu', limit=10)
    assert len(rows) == 2

def test_anomaly_detection():
    from monitoring.alerting.anomaly_detection import AnomalyDetection
    import numpy as np
    ad = AnomalyDetection(method='zscore')
    data = np.concatenate([np.random.randn(100), [100]])
    anomalies = ad.detect(data)
    assert len(anomalies) > 0

def test_threshold_rules():
    from monitoring.alerting.threshold_rules import ThresholdRules
    tr = ThresholdRules()
    tr.add_rule('high_cpu', 'cpu', 80, 'above', 'warning')
    alerts = tr.evaluate({'cpu': 90})
    assert len(alerts) == 1
    alerts = tr.evaluate({'cpu': 50})
    assert len(alerts) == 0

def test_alert_manager():
    from monitoring.alerting.alert_manager import AlertManager
    am = AlertManager()
    am.create_alert('test', 'cpu', 90, 80, 'warning')
    active = am.get_active()
    assert len(active) == 1
    am.resolve(active[0]['id'])
    assert len(am.get_active()) == 0

def test_feishu_channel():
    from monitoring.channels.feishu import FeishuChannel
    fc = FeishuChannel('https://test.webhook')
    assert fc.webhook_url == 'https://test.webhook'
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement monitoring system**

```python
# monitoring/__init__.py
from .dashboard.metrics_collector import MetricsCollector
from .dashboard.time_series_db import TimeSeriesDB
from .alerting.anomaly_detection import AnomalyDetection
from .alerting.threshold_rules import ThresholdRules
from .alerting.alert_manager import AlertManager

# monitoring/dashboard/__init__.py
from .metrics_collector import MetricsCollector
from .time_series_db import TimeSeriesDB

# monitoring/dashboard/metrics_collector.py
from typing import Callable, Dict, Any

class MetricsCollector:
    def __init__(self): self.metrics={}; self.collectors={}
    def register(self, name: str, fn: Callable): self.collectors[name]=fn
    def collect(self):
        for name,fn in self.collectors.items():
            try: self.metrics[name]=fn()
            except: self.metrics[name]=None
    def get(self, name): return self.metrics.get(name)
    def get_all(self): return self.metrics.copy()

# monitoring/dashboard/time_series_db.py
import sqlite3, json
from datetime import datetime

class TimeSeriesDB:
    def __init__(self, path):
        self.conn=sqlite3.connect(path)
        self.conn.execute('CREATE TABLE IF NOT EXISTS metrics (ts TEXT, name TEXT, value REAL, tags TEXT)')
        self.conn.commit()
    def insert(self, name, value, tags=None):
        self.conn.execute('INSERT INTO metrics VALUES (?,?,?,?)',(datetime.now().isoformat(),name,value,json.dumps(tags) if tags else None))
        self.conn.commit()
    def query(self, name, limit=100):
        cur=self.conn.execute('SELECT ts,value,tags FROM metrics WHERE name=? ORDER BY ts DESC LIMIT ?',(name,limit))
        return [{'timestamp':r[0],'value':r[1],'tags':json.loads(r[2]) if r[2] else None} for r in cur.fetchall()]

# monitoring/alerting/__init__.py
from .anomaly_detection import AnomalyDetection
from .threshold_rules import ThresholdRules
from .alert_manager import AlertManager

# monitoring/alerting/anomaly_detection.py
import numpy as np

class AnomalyDetection:
    def __init__(self, method='zscore', threshold=3.0): self.method=method; self.threshold=threshold
    def detect(self, data):
        if self.method=='zscore':
            mu,sig = np.mean(data),np.std(data)
            if sig==0: return []
            z = np.abs((data-mu)/sig)
            return np.where(z>self.threshold)[0].tolist()
        return []

# monitoring/alerting/threshold_rules.py
from typing import List, Dict

class ThresholdRules:
    def __init__(self): self.rules=[]
    def add_rule(self, name, metric, threshold, direction='above', severity='warning'):
        self.rules.append({'name':name,'metric':metric,'threshold':threshold,'direction':direction,'severity':severity})
    def evaluate(self, metrics: Dict) -> List[Dict]:
        alerts=[]
        for r in self.rules:
            v=metrics.get(r['metric'])
            if v is None: continue
            if (r['direction']=='above' and v>r['threshold']) or (r['direction']=='below' and v<r['threshold']):
                alerts.append({'rule':r['name'],'metric':r['metric'],'value':v,'threshold':r['threshold'],'severity':r['severity']})
        return alerts

# monitoring/alerting/alert_manager.py
import uuid
from datetime import datetime

class AlertManager:
    def __init__(self): self.alerts=[]; self.history=[]
    def create_alert(self, rule, metric, value, threshold, severity):
        a={'id':str(uuid.uuid4()),'rule':rule,'metric':metric,'value':value,'threshold':threshold,'severity':severity,'timestamp':datetime.now().isoformat(),'status':'active'}
        self.alerts.append(a); self.history.append(a); return a
    def resolve(self, alert_id):
        for a in self.alerts:
            if a['id']==alert_id: a['status']='resolved'; a['resolved_at']=datetime.now().isoformat()
    def get_active(self): return [a for a in self.alerts if a['status']=='active']
    def get_history(self): return self.history.copy()

# monitoring/channels/__init__.py
from .feishu import FeishuChannel
from .email import EmailChannel

# monitoring/channels/feishu.py
class FeishuChannel:
    def __init__(self, webhook_url): self.webhook_url=webhook_url
    def send(self, title, content):
        import requests
        payload={"msg_type":"interactive","card":{"header":{"title":{"tag":"plain_text","content":title}},"elements":[{"tag":"div","text":{"tag":"lark_md","content":content}}]}}
        try: return requests.post(self.webhook_url,json=payload,timeout=10).status_code==200
        except: return False

# monitoring/channels/email.py
class EmailChannel:
    def __init__(self, smtp_host, smtp_port, username, password):
        self.host=smtp_host; self.port=smtp_port; self.user=username; self.passwd=password
    def send(self, subject, body, recipients):
        import smtplib
        from email.mime.text import MIMEText
        msg=MIMEText(body); msg['Subject']=subject; msg['From']=self.user; msg['To']=','.join(recipients)
        try:
            with smtplib.SMTP(self.host,self.port) as s: s.starttls(); s.login(self.user,self.passwd); s.send_message(msg)
            return True
        except: return False
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 4.2: Performance Attribution and Reporting

**Files:**
- Create: `monitoring/performance/__init__.py`
- Create: `monitoring/performance/return_attribution.py`
- Create: `monitoring/performance/performance_report.py`
- Test: `tests/unit/test_performance.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_performance.py
import numpy as np

def test_brinson_attribution():
    from monitoring.performance.return_attribution import ReturnAttribution
    ra = ReturnAttribution()
    result = ra.brinson(
        port_weights={'A':0.6,'B':0.4}, bench_weights={'A':0.5,'B':0.5},
        port_returns={'A':0.1,'B':0.05}, bench_returns={'A':0.08,'B':0.04}
    )
    assert 'allocation' in result
    assert 'selection' in result
    assert 'interaction' in result

def test_performance_report():
    from monitoring.performance.performance_report import PerformanceReport
    pr = PerformanceReport()
    report = pr.daily({
        'date':'2026-01-01','pnl':1000,'sharpe':1.5,'max_drawdown':0.05,
        'positions':[{'symbol':'AAPL','pnl':600},{'symbol':'GOOG','pnl':400}]
    })
    assert 'date' in report
    assert 'summary' in report
    assert 'positions' in report
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement performance module**

```python
# monitoring/performance/__init__.py
from .return_attribution import ReturnAttribution
from .performance_report import PerformanceReport

# monitoring/performance/return_attribution.py
class ReturnAttribution:
    def brinson(self, port_weights, bench_weights, port_returns, bench_returns):
        alloc = sum((port_weights.get(a,0)-bench_weights.get(a,0))*bench_returns.get(a,0) for a in set(list(port_weights.keys())+list(bench_weights.keys())))
        sel = sum(bench_weights.get(a,0)*(port_returns.get(a,0)-bench_returns.get(a,0)) for a in set(list(port_weights.keys())+list(bench_weights.keys())))
        inter = sum((port_weights.get(a,0)-bench_weights.get(a,0))*(port_returns.get(a,0)-bench_returns.get(a,0)) for a in set(list(port_weights.keys())+list(bench_weights.keys())))
        return {'allocation':alloc,'selection':sel,'interaction':inter,'total_active':alloc+sel+inter}

# monitoring/performance/performance_report.py
class PerformanceReport:
    def daily(self, data):
        return {
            'date':data.get('date'),
            'summary':{'pnl':data.get('pnl',0),'sharpe':data.get('sharpe',0),'max_drawdown':data.get('max_drawdown',0)},
            'positions':data.get('positions',[]),
        }
    def weekly(self, data):
        return {
            'period':data.get('period'),
            'performance':{'total_return':data.get('total_return',0),'sharpe':data.get('sharpe',0)},
            'risk':{'max_drawdown':data.get('max_drawdown',0),'var_95':data.get('var_95',0)},
        }
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

## Completion Checklist

### Stage 2: RL Enhancement
- [ ] Deep RL networks (DQN, GaussianActor, TwinCritic)
- [ ] Replay buffer (standard + prioritized)
- [ ] DQN trainer
- [ ] SAC algorithm
- [ ] TD3 algorithm
- [ ] DDPG algorithm
- [ ] Multi-agent RL (MADDPG)
- [ ] Offline RL (CQL)
- [ ] Offline dataset manager

### Stage 3: Risk Management
- [ ] VaR calculator (historical, parametric, Monte Carlo)
- [ ] CVaR calculator
- [ ] Stress testing
- [ ] Risk attribution
- [ ] Kelly criterion
- [ ] Volatility targeting
- [ ] Regime-based positioning

### Stage 4: Monitoring & Alerting
- [ ] Metrics collector
- [ ] Time series database
- [ ] Anomaly detection
- [ ] Threshold rules engine
- [ ] Alert manager
- [ ] Feishu channel
- [ ] Email channel
- [ ] Performance attribution
- [ ] Performance reporting

**All stages complete after tests pass and documentation is written.**
