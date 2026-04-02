# 🪙 Duino-Coin GPU Miner (OpenCL)

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![GPU Support](https://img.shields.io/badge/GPU-OpenCL%20Enabled-orange.svg)
![Status](|Status|Active-brightgreen.svg)

**Duino-Coin GPU Miner** is a high-efficiency mining tool for DUCO, optimized for Graphics Cards (NVIDIA, AMD, Intel) using the OpenCL framework. It features a unique **TRUE Power Control** mechanism to protect your hardware and minimize electricity costs.

---

## ✨ Key Features

* **⚡ TRUE Power Control (1-100%):** Unlike fake delay loops, this miner truly throttles the GPU. The card physically rests between work cycles, significantly reducing temperatures.
* **🔑 Auto Mining Key Encoding:** Automatically detects and converts your Mining Key to Base64 format (required by the Duino-Coin server).
* **🔍 Auto Hardware Detection:** Automatically scans and identifies available GPUs and OpenCL platforms on your system.
* **🛡️ Hardware Friendly:** Recommended settings (1-10%) allow you to mine 24/7 while using your PC for work or gaming without lag.
* **📊 Detailed Stats:** Periodic reporting of Hashrate, Accepted Shares, Found Blocks, and Uptime.

---

## 🚀 Getting Started

### 1. Prerequisites
* **Python:** Version 3.7 or higher.
* **GPU Drivers:** Ensure you have the latest drivers with OpenCL support installed (NVIDIA Control Panel, AMD Software, or Intel Graphics).

### 2. Installation
Clone the repository and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration
On the first run, the program will generate a `config.txt` file. You must edit the following:
* `USERNAME`: Your Duino-Coin wallet username.
* `MINING_KEY`: Your mining key (Plain text or Base64).
* `GPU_LOAD_PERCENT`: Power limit (Recommended: **5** for background mining, **20+** for dedicated mining).

---

## 🛠 Usage

Simply run the main script using Python:
```bash
python3 GPU_Miner.py
```

---

## 📊 Recommended Settings

| Mode | GPU_LOAD_PERCENT | Goal |
| :--- | :--- | :--- |
| **Silent** | 1% - 3% | "Invisible" mining, near-zero heat increase. |
| **Balanced** | 5% - 10% | Best balance between rewards and card longevity. |
| **Performance**| 20% - 50% | Maximum Hashrate (Requires good cooling). |

> **Note:** Duino-Coin uses the "Kolka" algorithm to penalize powerful devices. Increasing power to 100% does **not** mean 100x rewards. Prioritize your hardware health!

---

## 🤝 Contributing
Found a bug or have an idea? Feel free to open an **Issue** or submit a **Pull Request**. Contributions are always welcome!

---

## 📄 License
This project is released under the **MIT License**.
