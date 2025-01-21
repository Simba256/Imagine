# Decentralized Matrix Multiplication Prototype

This project is a **blockchain-based** prototype that distributes matrix multiplication tasks across a network of participating “worker” nodes. The **master** node coordinates tasks, the **data server** provides basic services and data storage, and each **worker** runs a Flask app to receive tasks, compute results, and return them to the master. A **Solidity** smart contract on the Sepolia testnet rewards worker nodes with tokens via an airdrop mechanism.

> **Note**: This is a **local-network prototype** with hardcoded IP addresses. While it demonstrates core functionality, additional production-level features (e.g., security, dynamic peer discovery, etc.) are left for future development.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Folder & File Structure](#folder--file-structure)
3. [Prerequisites](#prerequisites)
4. [Setup & Running](#setup--running)
5. [How It Works](#how-it-works)
6. [Modifying the Smart Contract](#modifying-the-smart-contract)
7. [Future Improvements](#future-improvements)
8. [License](#license)

---

## Project Overview

- **Objective**: Distribute matrix multiplication workloads among multiple worker nodes, each earning “points” redeemable for **crypto tokens** on a testnet.
- **Blockchain Layer**: Uses a Solidity smart contract deployed on the **Sepolia** testnet.  
- **Architecture**:  
  1. **Data Server**: Provides a central data reference and is the first component to run.  
  2. **Master Node**: Breaks matrix multiplications into sub-tasks and distributes them to the workers.  
  3. **Worker Nodes**: Connect to the master node’s IP to receive tasks and submit solutions.

---

## Folder & File Structure

```
.
├── static/
│   └── contractABI.json       # ABI for the Solidity contract
├── templates/
│   └── dashboard.html         # Basic frontend; references contractAddress
├── airdrop_preparer.py        # Script to handle airdrop logic (output is passed as parameters to smart contract on remix)
├── check.py                   # Utility checks or debugging
├── data_server.py             # Run this first; hosts data for the master/worker
├── helper.py                  # Helper functions for matrix ops, etc.
├── master.py                  # Main controller; breaks tasks into smaller jobs
├── ml.py                      # ML framework testing
├── singleSystem.py            # Possibly a test script for single-node systems
├── token.sol                  # Solidity smart contract for token creation & airdrop
├── user_points.json           # Local JSON for storing user (worker) points
├── user_points.py             # Code to manipulate user_points.json
└── worker_flask_app.py        # Worker node Flask app
```

---

## Prerequisites

- **Python 3.x**
- **Flask** (for the worker apps, and possibly for the master/data server)
- **Web3.py** (if you plan to interact with Ethereum from Python)
- **Remix IDE** (optional) for editing/deploying `token.sol`
- **Local Network**: All nodes (master, data server, workers) should be on the same network or have routable IP addresses.

Install any Python dependencies (if you have a `requirements.txt` file):
```bash
pip install -r requirements.txt
```

---

## Setup & Running

1. **Deploy or Verify the Smart Contract (Optional)**
   - The contract `token.sol` is **already deployed** on **Sepolia** at:
     ```
     0xC0f455Bb75eAE39D4508Cf1DAfA106317bfC902D
     ```
   - If you wish to deploy your own version, see [Modifying the Smart Contract](#modifying-the-smart-contract).

2. **Start the Data Server**
   - Run:
     ```bash
     python data_server.py
     ```
   - This service is referenced in `master.py` via a **hardcoded IP**. Update that IP if needed.

3. **Start the Master Node**
   - Run:
     ```bash
     python master.py
     ```
   - The **master** will look for the data server’s IP as well as its own IP. Update these IPs in the code if necessary.

4. **Start Worker Nodes**
   - Each participant (or your own local machine in separate terminals) runs:
     ```bash
     python worker_flask_app.py
     ```
   - This Flask app **connects** to the master via hardcoded IP addresses. Update them in the file if your setup differs.

5. **Airdrop Preparation (Optional)**
   - You can run `airdrop_preparer.py` to simulate token distribution logic. This script may connect to the deployed contract using the **Web3** library.

---

## How It Works

1. **Task Generation**
   - The master node (`master.py`) creates random matrix multiplication tasks or obtains them from `data_server.py`.

2. **Distribution to Workers**
   - Workers (running `worker_flask_app.py`) periodically request tasks from the master node and compute solutions locally.

3. **Results Aggregation**
   - The master node collects results from workers and consolidates the final matrix multiplication product.

4. **Point Allocation**
   - Each worker node accrues “points” for completed tasks, stored in `user_points.json`.

5. **Token Redemption**
   - A **Solidity** contract (`token.sol`) manages token distribution. Workers can redeem accumulated points for tokens during an airdrop event, orchestrated by scripts like `airdrop_preparer.py`.

---

## Modifying the Smart Contract

1. **Contract Address**
   - The deployed address is hardcoded in `templates/dashboard.html` (line 41):
     ```javascript
     const contractAddress = '0xC0f455Bb75eAE39D4508Cf1DAfA106317bfC902D';
     ```
   - Update this if you **redeploy** the contract on Sepolia or another network.

2. **ABI Updates**
   - If you change the contract’s methods or structure, **recompile** `token.sol` and update the **ABI** in `static/contractABI.json`.
   - The system relies on this ABI to interact with the contract for airdrops, minting, etc.

3. **Deployment**
   - You can deploy the contract via [Remix IDE](https://remix.ethereum.org/), using the “Injected Provider” for Sepolia or a custom provider.
   - Update environment variables or code to point to your new contract address if needed.

---

## Future Improvements

- **Dynamic IP Discovery**: Remove hardcoded IPs in favor of a discovery mechanism or distributed registry.
- **Load Balancing**: Implement more sophisticated job scheduling, especially for large matrix operations.
- **Security**: Add authentication and secure communication between master and worker nodes.
- **Fault Tolerance**: Gracefully handle worker node disconnects or partial computations.
- **Production Deployment**: Use Docker, Kubernetes, or similar tools for scaling and automated deployment.

---

## License

**MIT License** © 2025 Simba256.  

---

### Contact / Credits

- **Author**: [Your Name (Syed Basim Mehmood)](mailto:syedbasimmehmood@gmail.com)  
- **GitHub**: [Simba256](https://github.com/Simba256)

Feel free to open issues or submit pull requests for improvements. Enjoy exploring decentralized compute!
