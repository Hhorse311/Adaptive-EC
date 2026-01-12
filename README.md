# Adaptive-EC-Simulator: A Byzantine Fault-Tolerant Erasure Coding Simulation

This project provides a Python-based simulation framework for an **Adaptive Erasure Coding (Adaptive-EC)** scheme designed to operate in Byzantine environments. It models a distributed storage network where nodes can fail or act maliciously (Byzantine behavior). The core of this scheme is its ability to dynamically adjust erasure coding parameters (`k` and `n`) to balance storage overhead and data recovery latency as the network state changes.

The simulation evaluates the performance of the Adaptive-EC scheme under various node exit scenarios, measuring key metrics such as:
- **Data Recovery Latency**: The time required to reconstruct the original data block.
- **Storage Overhead**: The total amount of storage used across the network relative to the original block size.
- **Repair Bandwidth**: The network traffic generated to repair the data after nodes exit.

This project was developed to analyze the robustness and efficiency of the adaptive approach compared to static erasure coding schemes.

## Features

- **Dynamic Parameter Optimization**: Automatically calculates the optimal erasure code parameter `k` based on a cost function that considers both storage cost and recovery latency.
- **Byzantine Fault Tolerance**: Simulates a network with a configurable percentage of Byzantine nodes that can disrupt data recovery.
- **Node Churn Simulation**: Models the continuous exit of nodes from the network and triggers the data repair mechanism.
- **Layered Repair Mechanism**: When nodes exit, the system creates new "repair layers" using erasure codes on the lost data, enhancing data durability.
- **Detailed Performance Metrics**: Collects and reports on recovery latency, storage overhead, repair bandwidth, and write/repair latency over the course of the simulation.
- **Configurable Simulation**: All key parameters, such as the number of nodes, block size, network speed, and Byzantine percentage, can be easily configured in `config.py`.

## Project Structure



## Prerequisites

- **Python**: Version 3.6 or higher.

- **Required Packages**:
  - `pandas`
  - `numpy`
  - `tqdm`
  - `matplotlib`

- **Installation**:
  Open your command line or terminal and run the following command to install all dependencies:
  ```bash
  pip install pandas numpy tqdm matplotlib


- **Execution Guide**:
Run the Main Simulation: Navigate to the project's root directory in your terminal and execute the following command. The script will run multiple simulation rounds and print the final averaged results.
   ```bash
  python main.py




HighLight
Research highlight 1

The proposed Adaptive-EC introduces a dynamic Reed-Solomon encoding mechanism that intelligently adjusts coding parameters in response to real-time network conditions, such as node count and block size. This ensures optimal trade-offs between storage efficiency and recovery overhead, while inherently supporting Byzantine fault tolerance without requiring full re-encoding during node churn.

Research highlight 2

To address the challenge of frequent node joins and departures, Adaptive-EC employs a novel tree-shaped erasure coding structure. This design enables lightweight re-encoding of only affected shards, avoiding the prohibitive cost of reprocessing the entire blockchain history while maintaining data availability and integrity.

Research highlight 3
Adaptive-EC leverages the homomorphic properties of Reed-Solomon codes to enable efficient, on-the-fly verification of encoded shards. This mechanism allows nodes to detect and discard malicious or corrupted shards during data recovery, significantly enhancing Byzantine resilience without introducing heavy cryptographic overhead.

Research highlight 4

The experimental evaluation of Adaptive-EC demonstrates its superior performance across multiple dimensions compared to existing distributed storage systems such as Sia, Storj, and Filecoin. In terms of Byzantine fault tolerance, Adaptive-EC maintains a 100\% block retrieval success rate even when up to one-third of the nodes are malicious, thanks to its homomorphic fingerprint-based shard verification mechanism. Storage efficiency is significantly improved, especially for large blocks, where Adaptive-EC consumes the least storage space among all tested systems. Write latency remains consistently low, benefiting from lightweight encoding and fingerprint generation, outperforming both replica-based and traditional erasure-coded systems. Under node churn scenarios, Adaptive-EC exhibits robust data survivability and minimal repair latency due to its tree-structured re-encoding strategy, although retrieval latency increases moderately as more nodes exit. Overall, Adaptive-EC achieves a well-balanced trade-off between storage cost, recovery performance, and fault tolerance, making it highly suitable for dynamic permissioned blockchain environments.
