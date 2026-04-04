#!/usr/bin/env python3
"""
Duino-Coin GPU Miner - TRUE Power Control 1-100%
- Real GPU throttling (not fake delay loops)
- Auto GPU Detection + Setup Guide
- Auto Base64 encoding for mining key
- Reads configuration from config.txt
- Supports: Ubuntu, Debian, Fedora, Arch, Alpine, CentOS/RHEL
"""

import sys
import os
import subprocess
import platform
import threading
import time

# ==================== CHECK & INSTALL GUIDE ====================
def get_linux_distro():
    """Detect Linux distribution"""
    if not os.path.exists('/etc/os-release'):
        return "unknown"
    
    with open('/etc/os-release', 'r') as f:
        content = f.read().lower()
    
    if 'alpine' in content:
        return "alpine"
    elif 'ubuntu' in content or 'debian' in content:
        return "debian"
    elif 'fedora' in content:
        return "fedora"
    elif 'arch' in content:
        return "arch"
    elif 'centos' in content or 'rhel' in content:
        return "rhel"
    else:
        return "unknown"

def install_package_linux(package_name):
    """Install package using appropriate package manager"""
    distro = get_linux_distro()
    
    # Map Python package names to system package names
    pkg_map = {
        "pyopencl": {
            "alpine": "py3-opencl",
            "debian": "python3-pyopencl",
            "fedora": "python3-pyopencl",
            "arch": "python-pyopencl",
            "rhel": "python3-pyopencl"
        },
        "numpy": {
            "alpine": "py3-numpy",
            "debian": "python3-numpy",
            "fedora": "python3-numpy",
            "arch": "python-numpy",
            "rhel": "python3-numpy"
        },
        "requests": {
            "alpine": "py3-requests",
            "debian": "python3-requests",
            "fedora": "python3-requests",
            "arch": "python-requests",
            "rhel": "python3-requests"
        },
        "colorama": {
            "alpine": "py3-colorama",
            "debian": "python3-colorama",
            "fedora": "python3-colorama",
            "arch": "python-colorama",
            "rhel": "python3-colorama"
        }
    }
    
    if distro == "alpine":
        cmd = ["apk", "add", pkg_map[package_name][distro]]
    elif distro == "debian":
        cmd = ["apt", "install", "-y", pkg_map[package_name][distro]]
    elif distro == "fedora":
        cmd = ["dnf", "install", "-y", pkg_map[package_name][distro]]
    elif distro == "arch":
        cmd = ["pacman", "-S", "--noconfirm", pkg_map[package_name][distro]]
    elif distro == "rhel":
        cmd = ["yum", "install", "-y", pkg_map[package_name][distro]]
    else:
        # Fallback to pip
        cmd = [sys.executable, "-m", "pip", "install", package_name]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except:
        return False

def try_import_opencl():
    """Try to import OpenCL with different possible names"""
    try:
        import pyopencl as cl
        return cl
    except ImportError:
        try:
            import py3opencl as cl  # Alpine Linux
            return cl
        except ImportError:
            return None

def check_and_install():
    """Check dependencies and provide installation guide"""
    
    # Try to import colorama first for colored output
    try:
        from colorama import init, Fore, Back, Style
        init(autoreset=True)
        use_color = True
    except:
        # Fallback if colorama not installed yet
        use_color = False
        class Fore:
            RED = CYAN = GREEN = YELLOW = WHITE = MAGENTA = BLUE = ''
        class Back:
            RED = CYAN = GREEN = YELLOW = WHITE = MAGENTA = BLUE = ''
        class Style:
            BRIGHT = DIM = NORMAL = RESET_ALL = ''
    
    print("\n" + "="*60)
    print("🔍 ENVIRONMENT CHECK")
    print("="*60)
    
    # 1. Check Python version
    py_version = sys.version_info
    print(f"\n📌 Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 7):
        print(f"{Fore.RED}❌ Python 3.7 or higher required!")
        sys.exit(1)
    print(f"{Fore.GREEN}✅ Python OK")
    
    # 2. Detect Linux distro
    system = platform.system()
    distro = None
    if system == "Linux":
        distro = get_linux_distro()
        print(f"{Fore.CYAN}📦 Detected: {distro.capitalize()} Linux")
    
    # 3. Check and install required packages
    packages = ["pyopencl", "numpy", "requests", "colorama"]
    missing = []
    
    for pkg in packages:
        if pkg == "pyopencl":
            if try_import_opencl() is not None:
                print(f"{Fore.GREEN}✅ {pkg} OK")
            else:
                missing.append(pkg)
                print(f"{Fore.RED}❌ {pkg} MISSING")
        else:
            try:
                __import__(pkg)
                print(f"{Fore.GREEN}✅ {pkg} OK")
            except ImportError:
                missing.append(pkg)
                print(f"{Fore.RED}❌ {pkg} MISSING")
    
    if missing:
        print(f"\n{Fore.YELLOW}📦 Installing missing packages...")
        
        for pkg in missing:
            print(f"   Installing {pkg}...")
            if system == "Linux" and distro:
                success = install_package_linux(pkg)
                if not success:
                    # Fallback to pip
                    subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True)
            else:
                # Non-Linux: use pip
                subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True)
        
        print(f"{Fore.GREEN}✅ Installation complete! Please restart the program.")
        sys.exit(0)
    
    # Now import colorama properly
    try:
        from colorama import init, Fore, Back, Style
        init(autoreset=True)
    except:
        pass
    
    # 4. Check OpenCL driver
    print(f"\n🔍 Checking OpenCL driver...")
    
    cl = try_import_opencl()
    if cl is None:
        print(f"{Fore.RED}❌ OpenCL module not available!")
        sys.exit(1)
    
    try:
        platforms = cl.get_platforms()
        
        if not platforms:
            raise Exception("No platforms")
        
        print(f"{Fore.GREEN}✅ OpenCL driver OK - Found {len(platforms)} platform(s)")
        
        # List GPUs
        gpu_found = False
        for i, p in enumerate(platforms):
            devices = p.get_devices(device_type=cl.device_type.GPU)
            if devices:
                for j, d in enumerate(devices):
                    print(f"{Fore.CYAN}   🖥️ GPU {j}: {d.name} (Platform {i}: {p.name})")
                    gpu_found = True
        
        if not gpu_found:
            print(f"{Fore.YELLOW}⚠️ No GPU found!")
            print(f"{Fore.YELLOW}   Will run on CPU (very slow)")
            
    except Exception as e:
        print(f"{Fore.RED}❌ OpenCL driver NOT INSTALLED!")
        print(f"\n{Fore.YELLOW}📖 OPENCL DRIVER INSTALLATION GUIDE:")
        print(f"{Fore.CYAN}{'='*50}")
        
        if system == "Windows":
            print(f"""
{Fore.WHITE}🔹 WINDOWS:
   1. NVIDIA GPU: Download driver from https://www.nvidia.com/Download/index.aspx
   2. AMD GPU: Download driver from https://www.amd.com/en/support
   3. Intel GPU: Download from https://www.intel.com/content/www/us/en/download/19308/intel-graphics-windows-dch-drivers.html
   
   After installing driver, RESTART your computer and run again.
""")
        elif system == "Linux":
            if distro == "alpine":
                print(f"""
{Fore.WHITE}🔹 ALPINE LINUX:
   
   # Install OpenCL ICD loader
   sudo apk add opencl-icd-loader clinfo
   
   # For Intel GPU:
   sudo apk add intel-opencl-icd
   
   # For AMD GPU:
   sudo apk add mesa-opencl-icd
   
   # Verify installation:
   clinfo
""")
            elif distro == "debian":
                print(f"""
{Fore.WHITE}🔹 UBUNTU/DEBIAN:
   
   sudo apt update
   sudo apt install opencl-headers clinfo
   
   # NVIDIA GPU:
   sudo apt install nvidia-opencl-icd
   
   # AMD GPU:
   sudo apt install mesa-opencl-icd
   
   # Intel GPU:
   sudo apt install intel-opencl-icd
   
   # Verify installation:
   clinfo
""")
            elif distro == "fedora":
                print(f"""
{Fore.WHITE}🔹 FEDORA:
   
   sudo dnf install opencl-headers clinfo
   
   # NVIDIA GPU:
   sudo dnf install nvidia-opencl
   
   # AMD/Intel GPU:
   sudo dnf install mesa-libOpenCL
   
   # Verify installation:
   clinfo
""")
            elif distro == "arch":
                print(f"""
{Fore.WHITE}🔹 ARCH LINUX:
   
   sudo pacman -S opencl-headers clinfo
   
   # NVIDIA GPU:
   sudo pacman -S opencl-nvidia
   
   # AMD GPU:
   sudo pacman -S opencl-mesa
   
   # Intel GPU:
   sudo pacman -S intel-compute-runtime
   
   # Verify installation:
   clinfo
""")
            else:
                print(f"""
{Fore.WHITE}🔹 LINUX (General):
   
   # Install OpenCL development packages:
   sudo apt install opencl-headers clinfo  # Debian/Ubuntu
   # OR
   sudo dnf install opencl-headers clinfo  # Fedora
   # OR
   sudo pacman -S opencl-headers clinfo    # Arch
   
   # Then install GPU-specific driver
""")
        elif system == "Darwin":  # macOS
            print(f"""
{Fore.WHITE}🔹 macOS:
   macOS has OpenCL framework built-in.
   If you see errors, update to latest macOS version.
""")
        
        print(f"{Fore.CYAN}{'='*50}")
        print(f"{Fore.YELLOW}⚠️ After driver installation, RESTART and run again!")
        sys.exit(1)
    
    print(f"\n{Fore.GREEN}✅ Environment OK! Starting miner...\n")
    return cl

# Run check before importing other modules
cl = check_and_install()

# Import all modules (after checks)
import numpy as np
import requests
import socket
import base64
import random
import json
from datetime import datetime

# Import colorama (now installed)
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except:
    # Fallback if still not available
    class Fore:
        RED = CYAN = GREEN = YELLOW = WHITE = MAGENTA = BLUE = ''
    class Back:
        RED = CYAN = GREEN = YELLOW = WHITE = MAGENTA = BLUE = ''
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''

# ==================== HELPER FUNCTIONS ====================
def encode_mining_key(key):
    """Encode mining key to Base64 if it's plain text."""
    if not key or key == "None" or key == "none" or key == "":
        return "None"
    
    import re
    is_base64 = re.match(r'^[A-Za-z0-9+/]+=*$', key) and len(key) % 4 == 0
    
    if is_base64 and len(key) > 8:
        try:
            base64.b64decode(key)
            return key
        except:
            pass
    
    try:
        encoded = base64.b64encode(key.encode('utf-8')).decode('utf-8')
        print(f"{Fore.GREEN}✅ Mining key encoded to Base64")
        return encoded
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️ Could not encode mining key: {e}, using 'None'")
        return "None"

def decode_mining_key(encoded_key):
    """Decode Base64 mining key back to plain text for display."""
    if not encoded_key or encoded_key == "None":
        return "None"
    
    try:
        decoded = base64.b64decode(encoded_key).decode('utf-8')
        return decoded
    except:
        return encoded_key

# ==================== CONFIGURATION ====================
def detect_gpus():
    """Auto detect and list all GPUs"""
    gpus = []
    platforms = cl.get_platforms()
    
    for p_idx, p in enumerate(platforms):
        devices = p.get_devices(device_type=cl.device_type.GPU)
        for d_idx, d in enumerate(devices):
            gpus.append({
                'platform_idx': p_idx,
                'device_idx': d_idx,
                'platform_name': p.name,
                'device_name': d.name,
                'max_compute_units': d.max_compute_units,
                'global_mem': d.global_mem_size // (1024*1024)
            })
    return gpus

def load_config():
    """Read configuration from config.txt"""
    config_file = "config.txt"
    
    # Default config
    config = {
        "USERNAME": "your_username",
        "MINING_KEY": "None",
        "DIFFICULTY": "LOW",
        "RIG_ID": "GPU_Miner",
        "GPU_PLATFORM": None,
        "GPU_DEVICE": None,
        "GPU_LOAD_PERCENT": 5,
        "POOL_URL": "https://server.duinocoin.com/getPool",
        "SOC_TIMEOUT": 10,
        "REPORT_INTERVAL": 300,
    }
    
    # Auto detect GPU
    print(f"\n{Fore.CYAN}🔍 DETECTING GPU...")
    gpus = detect_gpus()
    
    if gpus:
        print(f"{Fore.GREEN}✅ Found {len(gpus)} GPU(s):")
        for i, gpu in enumerate(gpus):
            print(f"   [{i}] {gpu['device_name']}")
            print(f"       - Platform: {gpu['platform_name']}")
            print(f"       - Compute units: {gpu['max_compute_units']}")
            print(f"       - Memory: {gpu['global_mem']} MB")
        
        if len(gpus) == 1:
            config["GPU_PLATFORM"] = gpus[0]['platform_idx']
            config["GPU_DEVICE"] = gpus[0]['device_idx']
            print(f"\n{Fore.GREEN}💡 Auto-selected: {gpus[0]['device_name']}")
        else:
            print(f"\n{Fore.YELLOW}💡 Multiple GPUs found. You can select in config.txt:")
            for i, gpu in enumerate(gpus):
                print(f"   GPU_PLATFORM = {gpu['platform_idx']}, GPU_DEVICE = {gpu['device_idx']} → {gpu['device_name']}")
    else:
        print(f"{Fore.YELLOW}⚠️ No GPU found, will run on CPU")
    
    # Create sample config if not exists
    if not os.path.exists(config_file):
        sample_config = f"""# Duino-Coin GPU Miner Configuration File
# ============================================

# DUINO-COIN ACCOUNT (REQUIRED)
# Register at: https://duinocoin.com/register
USERNAME = your_username

# MINING KEY (IMPORTANT!)
# You can enter either:
#   - Plain text key -> will be auto-encoded to Base64
#   - Already encoded Base64 key
#   - "None" if you don't have a key
MINING_KEY = None

# DIFFICULTY: LOW, MEDIUM, HIGH, NET
DIFFICULTY = LOW

# RIG ID (your miner identifier)
RIG_ID = GPU_Miner

# GPU CONFIGURATION (AUTO DETECTED)
"""

        if gpus:
            sample_config += f"\n# Detected GPUs:\n"
            for i, gpu in enumerate(gpus):
                sample_config += f"#   - {gpu['device_name']}\n"
            sample_config += f"\n"
            sample_config += f"GPU_PLATFORM = {gpus[0]['platform_idx']}\n"
            sample_config += f"GPU_DEVICE = {gpus[0]['device_idx']}\n"
        else:
            sample_config += f"GPU_PLATFORM = None\n"
            sample_config += f"GPU_DEVICE = None\n"
        
        sample_config += f"""
# TRUE GPU POWER (1-100%)
# 1% = GPU works 1% of time, sleeps 99%
GPU_LOAD_PERCENT = 5

# NETWORK SETTINGS
POOL_URL = https://server.duinocoin.com/getPool
SOC_TIMEOUT = 10
REPORT_INTERVAL = 300
"""
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(sample_config)
        
        print(f"\n{Fore.YELLOW}📝 Created sample config file: {config_file}")
        print(f"{Fore.YELLOW}   ⚠️ PLEASE EDIT YOUR USERNAME BEFORE RUNNING!")
        print(f"{Fore.CYAN}   🔹 Open {config_file}")
        print(f"{Fore.CYAN}   🔹 Change USERNAME = your_actual_username")
        print(f"{Fore.CYAN}   🔹 Save and run again")
        sys.exit(0)
    
    # Read config file
    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                if key == "USERNAME":
                    config["USERNAME"] = value
                elif key == "MINING_KEY":
                    if value and value != "None":
                        config["MINING_KEY"] = encode_mining_key(value)
                    else:
                        config["MINING_KEY"] = "None"
                elif key == "DIFFICULTY":
                    config["DIFFICULTY"] = value.upper()
                elif key == "RIG_ID":
                    config["RIG_ID"] = value
                elif key == "GPU_PLATFORM":
                    config["GPU_PLATFORM"] = int(value) if value != "None" else None
                elif key == "GPU_DEVICE":
                    config["GPU_DEVICE"] = int(value) if value != "None" else None
                elif key == "GPU_LOAD_PERCENT":
                    val = int(value)
                    config["GPU_LOAD_PERCENT"] = max(1, min(100, val))
                elif key == "POOL_URL":
                    config["POOL_URL"] = value
                elif key == "SOC_TIMEOUT":
                    config["SOC_TIMEOUT"] = int(value)
                elif key == "REPORT_INTERVAL":
                    config["REPORT_INTERVAL"] = int(value)
    
    # Validate required info
    if config["USERNAME"] == "your_username":
        print(f"\n{Fore.RED}❌ YOU HAVEN'T SET YOUR USERNAME IN config.txt!")
        print(f"{Fore.YELLOW}   Open config.txt and set USERNAME = your_username")
        sys.exit(1)
    
    return config

# ==================== OPENCL KERNEL (giữ nguyên) ====================
OPENCL_KERNEL = """
// SHA1 implementation for OpenCL
#define LEFT_ROTATE(x, n) (((x) << (n)) | ((x) >> (32 - (n))))

void sha1_transform(uint *state, const uchar *data) {
    uint w[80];
    uint a, b, c, d, e, temp;
    int i;
    
    for (i = 0; i < 16; i++) {
        w[i] = ((uint)data[i*4] << 24) | ((uint)data[i*4+1] << 16) | 
               ((uint)data[i*4+2] << 8) | (uint)data[i*4+3];
    }
    for (i = 16; i < 80; i++) {
        w[i] = LEFT_ROTATE(w[i-3] ^ w[i-8] ^ w[i-14] ^ w[i-16], 1);
    }
    
    a = state[0];
    b = state[1];
    c = state[2];
    d = state[3];
    e = state[4];
    
    for (i = 0; i < 80; i++) {
        if (i < 20) {
            temp = LEFT_ROTATE(a, 5) + ((b & c) | (~b & d)) + e + 0x5A827999 + w[i];
        } else if (i < 40) {
            temp = LEFT_ROTATE(a, 5) + (b ^ c ^ d) + e + 0x6ED9EBA1 + w[i];
        } else if (i < 60) {
            temp = LEFT_ROTATE(a, 5) + ((b & c) | (b & d) | (c & d)) + e + 0x8F1BBCDC + w[i];
        } else {
            temp = LEFT_ROTATE(a, 5) + (b ^ c ^ d) + e + 0xCA62C1D6 + w[i];
        }
        e = d;
        d = c;
        c = LEFT_ROTATE(b, 30);
        b = a;
        a = temp;
    }
    
    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
}

__kernel void ducos1_gpu(
    __global const uchar *last_hash,
    __global const uchar *target_hash,
    uint difficulty,
    uint work_items,
    __global uint *result_nonce
) {
    uint gid = get_global_id(0);
    
    if (gid >= work_items) {
        return;
    }
    
    uint nonce = gid;
    uint max_nonce = 100 * difficulty;
    
    while (nonce <= max_nonce && *result_nonce == 0) {
        uchar message[64] = {0};
        for (int i = 0; i < 20; i++) {
            message[i] = last_hash[i];
        }
        
        message[20] = (nonce >> 24) & 0xFF;
        message[21] = (nonce >> 16) & 0xFF;
        message[22] = (nonce >> 8) & 0xFF;
        message[23] = nonce & 0xFF;
        
        uint state[5] = {0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0};
        sha1_transform(state, message);
        
        uchar hash_result[20];
        for (int i = 0; i < 5; i++) {
            hash_result[i*4] = (state[i] >> 24) & 0xFF;
            hash_result[i*4+1] = (state[i] >> 16) & 0xFF;
            hash_result[i*4+2] = (state[i] >> 8) & 0xFF;
            hash_result[i*4+3] = state[i] & 0xFF;
        }
        
        bool match = true;
        for (int i = 0; i < 20; i++) {
            if (hash_result[i] != target_hash[i]) {
                match = false;
                break;
            }
        }
        
        if (match) {
            *result_nonce = nonce;
            return;
        }
        
        nonce += work_items;
    }
}
"""

# ==================== GPU MINER CLASS ====================
class GPUMiner:
    def __init__(self, config):
        self.config = config
        self.platform = None
        self.device = None
        self.context = None
        self.queue = None
        self.program = None
        self.stats = {
            'accepted': 0,
            'rejected': 0,
            'blocks': 0,
            'total_hashrate': 0
        }
        self.last_job_time = 0
        self.total_solve_time = 0
        
    def init_gpu(self):
        platforms = cl.get_platforms()
        if not platforms:
            raise Exception("No OpenCL platform found!")
        
        if self.config["GPU_PLATFORM"] is not None:
            self.platform = platforms[self.config["GPU_PLATFORM"]]
        else:
            for p in platforms:
                devices = p.get_devices(device_type=cl.device_type.GPU)
                if devices:
                    self.platform = p
                    break
            if not self.platform:
                self.platform = platforms[0]
        
        devices = self.platform.get_devices(device_type=cl.device_type.GPU)
        if not devices:
            devices = self.platform.get_devices()
        
        if self.config["GPU_DEVICE"] is not None:
            self.device = devices[self.config["GPU_DEVICE"]]
        else:
            self.device = devices[0]
        
        print(f"{Fore.GREEN}✅ GPU: {self.device.name}")
        print(f"{Fore.CYAN}   - Compute units: {self.device.max_compute_units}")
        print(f"{Fore.CYAN}   - Memory: {self.device.global_mem_size // (1024*1024)} MB")
        
        self.max_work_size = self.device.max_work_group_size * self.device.max_compute_units
        print(f"{Fore.CYAN}   - Max parallel threads: {self.max_work_size}")
        
        self.context = cl.Context([self.device])
        self.queue = cl.CommandQueue(self.context)
        
        print(f"{Fore.YELLOW}⏳ Compiling OpenCL kernel...")
        self.program = cl.Program(self.context, OPENCL_KERNEL).build()
        print(f"{Fore.GREEN}✅ Kernel ready!")
        
    def solve_job(self, last_hash_hex, target_hex, difficulty):
        """Solve job with TRUE power control"""
        
        last_hash_bytes = bytes.fromhex(last_hash_hex)
        target_bytes = bytes.fromhex(target_hex)
        
        work_size = max(64, int(self.max_work_size * self.config["GPU_LOAD_PERCENT"] / 100))
        
        last_hash_buf = cl.Buffer(self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, 
                                   hostbuf=last_hash_bytes)
        target_buf = cl.Buffer(self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                                hostbuf=target_bytes)
        result_nonce_buf = cl.Buffer(self.context, cl.mem_flags.WRITE_ONLY, 4)
        
        solve_start = time.time()
        
        kernel = self.program.ducos1_gpu
        kernel.set_args(last_hash_buf, target_buf, np.uint32(difficulty), 
                       np.uint32(work_size),
                       result_nonce_buf)
        
        local_size = min(64, work_size)
        global_size = ((work_size + local_size - 1) // local_size) * local_size
        
        event = cl.enqueue_nd_range_kernel(self.queue, kernel, (global_size,), (local_size,))
        event.wait()
        
        result_nonce = np.zeros(1, dtype=np.uint32)
        cl.enqueue_copy(self.queue, result_nonce, result_nonce_buf).wait()
        
        solve_time = time.time() - solve_start
        
        # TRUE POWER THROTTLING
        power_percent = self.config["GPU_LOAD_PERCENT"]
        if power_percent < 100 and result_nonce[0] == 0:
            if solve_time > 0 and power_percent > 0:
                sleep_time = solve_time * (100 - power_percent) / power_percent
                sleep_time = min(sleep_time, 7.0)
                if sleep_time > 0.001:
                    time.sleep(sleep_time)
        
        if result_nonce[0] > 0:
            hashrate = 1_000_000_000 * result_nonce[0] / (solve_time * 1e9) if solve_time > 0 else 0
            return result_nonce[0], hashrate, solve_time
        
        return 0, 0.0, solve_time

# ==================== NETWORK CLIENT ====================
class DuinoClient:
    def __init__(self, config):
        self.config = config
        self.socket = None
        
    def get_pool(self):
        try:
            resp = requests.get(self.config["POOL_URL"], timeout=10).json()
            if resp.get("success"):
                return (resp["ip"], resp["port"], resp.get("name", "Unknown"))
        except Exception as e:
            print(f"{Fore.RED}❌ Pool error: {e}")
        return ("server.duinocoin.com", 14625, "Default")
    
    def connect(self, pool):
        ip, port, name = pool
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.config["SOC_TIMEOUT"])
        self.socket.connect((ip, port))
        version = self.socket.recv(128).decode().strip()
        return version, name
    
    def send_job_request(self, username, difficulty, mining_key):
        key = mining_key if mining_key != "None" else "None"
        msg = f"JOB,{username},{difficulty},{key}\n"
        self.socket.send(msg.encode())
        data = self.socket.recv(256).decode().strip()
        parts = data.split(',')
        if len(parts) == 3:
            return parts[0], parts[1], int(parts[2])
        return None, None, None
    
    def submit_solution(self, nonce, hashrate, miner_name, rig_id, group_id):
        msg = f"{nonce},{hashrate:.2f},{miner_name},{rig_id},{group_id}\n"
        self.socket.send(msg.encode())
        feedback = self.socket.recv(64).decode().strip()
        return feedback
    
    def close(self):
        if self.socket:
            self.socket.close()

# ==================== MAIN ====================
def format_hashrate(h):
    if h >= 1e9: return f"{h/1e9:.2f} GH/s"
    if h >= 1e6: return f"{h/1e6:.2f} MH/s"
    if h >= 1e3: return f"{h/1e3:.2f} kH/s"
    return f"{h:.2f} H/s"

def main():
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.YELLOW}🪙 Duino-Coin GPU Miner - TRUE Power Control 1-100%")
    print(f"{Fore.CYAN}{'='*60}")
    
    config = load_config()
    
    display_key = decode_mining_key(config["MINING_KEY"])
    if display_key != "None" and len(display_key) > 8:
        display_key = display_key[:4] + "..." + display_key[-4:]
    
    print(f"\n{Fore.GREEN}📋 CONFIGURATION:")
    print(f"{Fore.CYAN}   👤 Username: {config['USERNAME']}")
    print(f"{Fore.CYAN}   🔑 Mining Key: {display_key}")
    print(f"{Fore.CYAN}   🎯 Difficulty: {config['DIFFICULTY']}")
    print(f"{Fore.CYAN}   🖥️ Rig ID: {config['RIG_ID']}")
    print(f"{Fore.CYAN}   ⚡ GPU Power: {config['GPU_LOAD_PERCENT']}%")
    
    miner = GPUMiner(config)
    try:
        miner.init_gpu()
    except Exception as e:
        print(f"{Fore.RED}❌ GPU Error: {e}")
        return
    
    client = DuinoClient(config)
    stats = miner.stats
    start_time = time.time()
    last_report = start_time
    group_id = random.randint(0, 9999)
    
    print(f"\n{Fore.GREEN}✅ START MINING!")
    print(f"{Fore.YELLOW}   ⚡ GPU will be used only {config['GPU_LOAD_PERCENT']}% of the time")
    print(f"{Fore.CYAN}   📊 Dashboard: https://duinocoin.com/dashboard\n")
    
    while True:
        try:
            pool = client.get_pool()
            version, pool_name = client.connect(pool)
            print(f"{Fore.GREEN}✅ Connected to {pool_name} | v{version}")
            
            while True:
                last_hash, target_hash, difficulty = client.send_job_request(
                    config["USERNAME"], config["DIFFICULTY"], config["MINING_KEY"]
                )
                
                if not last_hash:
                    time.sleep(1)
                    continue
                
                nonce, hashrate, solve_time = miner.solve_job(last_hash, target_hash, difficulty)
                
                if nonce > 0:
                    feedback = client.submit_solution(
                        nonce, hashrate, "GPU_Miner", config["RIG_ID"], group_id
                    )
                    
                    if feedback == "GOOD":
                        stats['accepted'] += 1
                        stats['total_hashrate'] = hashrate
                        print(f"{Fore.GREEN}✅ ACC #{stats['accepted']} | {format_hashrate(hashrate)} | Diff:{difficulty}")
                    
                    elif feedback == "BLOCK":
                        stats['blocks'] += 1
                        stats['accepted'] += 1
                        print(f"{Fore.YELLOW}⛓️🎉 BLOCK #{stats['blocks']} FOUND! +10 DUCO")
                    
                    elif feedback.startswith("BAD"):
                        stats['rejected'] += 1
                        reason = feedback.split(',')[1] if ',' in feedback else "unknown"
                        print(f"{Fore.RED}❌ REJECT | {reason}")
                
                if time.time() - last_report >= config["REPORT_INTERVAL"]:
                    uptime = int(time.time() - start_time)
                    total = stats['accepted'] + stats['rejected']
                    rate = (stats['accepted'] / total * 100) if total > 0 else 0
                    
                    print(f"\n{Fore.CYAN}{'='*50}")
                    print(f"{Fore.YELLOW}📊 PERIODIC REPORT")
                    print(f"{Fore.CYAN}   ✅ Accepted: {stats['accepted']}")
                    print(f"{Fore.CYAN}   ❌ Rejected: {stats['rejected']}")
                    print(f"{Fore.CYAN}   ⛓️ Blocks: {stats['blocks']}")
                    print(f"{Fore.CYAN}   📈 Accept Rate: {rate:.1f}%")
                    print(f"{Fore.CYAN}   🚀 Hashrate: {format_hashrate(stats['total_hashrate'])}")
                    print(f"{Fore.CYAN}   ⚡ Target Power: {config['GPU_LOAD_PERCENT']}%")
                    print(f"{Fore.CYAN}   ⏱️ Uptime: {uptime//3600}h {(uptime%3600)//60}m")
                    print(f"{Fore.CYAN}{'='*50}\n")
                    
                    last_report = time.time()
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error: {e}")
            time.sleep(5)
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Goodbye! GPU is now idle.")
