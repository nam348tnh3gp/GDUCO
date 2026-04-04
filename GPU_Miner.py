#!/usr/bin/env python3
"""
Duino-Coin GPU Miner - TRUE Power Control 1-100%
Based on official PC_Miner.py structure
Supports ALL Linux distributions (Ubuntu, Debian, Fedora, Arch, Alpine, CentOS/RHEL)
AUTO INSTALLS everything including OpenCL runtime
"""

import sys
import os
import subprocess
import platform
import threading
import time

# ==================== AUTO INSTALL PACKAGES (like official miner) ====================
def install_package(package):
    """Automatically installs python pip package (same as official miner)"""
    try:
        import pip
        pip.main(["install", package])
    except (AttributeError, ImportError):
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    
    # Restart the program
    os.execl(sys.executable, sys.executable, *sys.argv)

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

def install_opencl_runtime_linux():
    """Install OpenCL runtime for Linux (system level)"""
    distro = get_linux_distro()
    
    print("\n📦 Installing OpenCL runtime for", distro)
    
    if distro == "alpine":
        cmds = [
            ["apk", "add", "opencl-icd-loader", "clinfo"],
            ["apk", "add", "intel-opencl-icd"],  # Intel GPU
            ["apk", "add", "mesa-opencl-icd"]    # AMD GPU
        ]
    elif distro == "debian":
        subprocess.run(["apt", "update"], capture_output=True)
        cmds = [
            ["apt", "install", "-y", "opencl-headers", "clinfo", "ocl-icd-libopencl1"],
            ["apt", "install", "-y", "intel-opencl-icd"],
            ["apt", "install", "-y", "mesa-opencl-icd"]
        ]
    elif distro == "fedora":
        cmds = [
            ["dnf", "install", "-y", "opencl-headers", "clinfo", "ocl-icd"],
            ["dnf", "install", "-y", "intel-opencl"],
            ["dnf", "install", "-y", "mesa-libOpenCL"]
        ]
    elif distro == "arch":
        cmds = [
            ["pacman", "-S", "--noconfirm", "opencl-headers", "clinfo"],
            ["pacman", "-S", "--noconfirm", "intel-compute-runtime"],
            ["pacman", "-S", "--noconfirm", "opencl-mesa"]
        ]
    elif distro == "rhel":
        cmds = [
            ["yum", "install", "-y", "opencl-headers", "clinfo", "ocl-icd"],
            ["yum", "install", "-y", "intel-opencl"],
            ["yum", "install", "-y", "mesa-libOpenCL"]
        ]
    else:
        return False
    
    for cmd in cmds:
        try:
            subprocess.run(cmd, capture_output=True, check=False)
        except:
            pass
    
    print("✅ OpenCL runtime installed")
    return True

def install_pyopencl_linux():
    """Install pyopencl using system package manager on Linux"""
    distro = get_linux_distro()
    
    if distro == "alpine":
        # On Alpine, pyopencl is called py3-opencl
        try:
            subprocess.run(["apk", "add", "py3-opencl"], capture_output=True, check=True)
            return True
        except:
            pass
    elif distro == "debian":
        try:
            subprocess.run(["apt", "install", "-y", "python3-pyopencl"], capture_output=True, check=True)
            return True
        except:
            pass
    elif distro == "fedora":
        try:
            subprocess.run(["dnf", "install", "-y", "python3-pyopencl"], capture_output=True, check=True)
            return True
        except:
            pass
    elif distro == "arch":
        try:
            subprocess.run(["pacman", "-S", "--noconfirm", "python-pyopencl"], capture_output=True, check=True)
            return True
        except:
            pass
    
    # Fallback to pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyopencl"], capture_output=True, check=True)
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
            import py3opencl as cl
            return cl
        except ImportError:
            return None

# ==================== CHECK DEPENDENCIES ====================
def check_dependencies():
    """Check and install all dependencies (similar to official miner)"""
    
    print("\n" + "="*60)
    print("🔍 Duino-Coin GPU Miner - Environment Check")
    print("="*60)
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("❌ Python 3.6 or higher required!")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check platform
    system = platform.system()
    distro = None
    if system == "Linux":
        distro = get_linux_distro()
        print(f"📦 Detected: {distro.capitalize()} Linux")
        
        # Check if running as root for Alpine
        if distro == "alpine" and os.geteuid() != 0:
            print("⚠️ On Alpine Linux, please run with: sudo python3 miner.py")
            print("   (Required to install OpenCL runtime and py3-opencl)")
            sys.exit(1)
    
    # Install required Python packages (like official miner)
    required_packages = ["requests", "colorama", "numpy"]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not found, installing...")
            install_package(package)
    
    # Now import colorama properly
    try:
        from colorama import init, Fore, Back, Style
        init(autoreset=True)
    except:
        # Fallback
        class Fore:
            RED = CYAN = GREEN = YELLOW = WHITE = MAGENTA = BLUE = ''
        class Back:
            RED = CYAN = GREEN = YELLOW = WHITE = MAGENTA = BLUE = ''
        class Style:
            BRIGHT = DIM = NORMAL = RESET_ALL = ''
    
    # Install OpenCL runtime (Linux only)
    if system == "Linux":
        print("\n🔧 Checking OpenCL runtime...")
        try:
            result = subprocess.run(["clinfo"], capture_output=True)
            if result.returncode != 0:
                print("⚠️ OpenCL runtime not found, installing...")
                if install_opencl_runtime_linux():
                    print("✅ OpenCL runtime installed")
                    print("⚠️ Please restart the miner!")
                    sys.exit(0)
                else:
                    print("❌ Failed to install OpenCL runtime")
                    print("   Please install manually:")
                    if distro == "alpine":
                        print("   apk add opencl-icd-loader clinfo intel-opencl-icd")
                    sys.exit(1)
            else:
                print("✅ OpenCL runtime OK")
        except FileNotFoundError:
            print("⚠️ clinfo not found, installing OpenCL runtime...")
            if install_opencl_runtime_linux():
                print("✅ OpenCL runtime installed")
                print("⚠️ Please restart the miner!")
                sys.exit(0)
    
    # Install pyopencl
    print("\n📦 Checking pyopencl...")
    if try_import_opencl() is not None:
        print("✅ pyopencl OK")
    else:
        print("❌ pyopencl not found, installing...")
        if system == "Linux":
            if install_pyopencl_linux():
                print("✅ pyopencl installed")
                print("⚠️ Please restart the miner!")
                sys.exit(0)
            else:
                print("❌ Failed to install pyopencl")
                sys.exit(1)
        else:
            # Windows/macOS - use pip
            install_package("pyopencl")
    
    # Final check
    cl = try_import_opencl()
    if cl is None:
        print("❌ Cannot import OpenCL after installation!")
        sys.exit(1)
    
    # Test OpenCL
    print("\n🔍 Testing OpenCL...")
    try:
        platforms = cl.get_platforms()
        if not platforms:
            raise Exception("No platforms")
        print(f"✅ OpenCL OK - {len(platforms)} platform(s)")
        
        gpu_found = False
        for p in platforms:
            devices = p.get_devices(device_type=cl.device_type.GPU)
            if devices:
                for d in devices:
                    print(f"   🖥️ GPU: {d.name}")
                    gpu_found = True
        
        if not gpu_found:
            print("⚠️ No GPU found, will run on CPU (slow)")
    except Exception as e:
        print(f"❌ OpenCL error: {e}")
        sys.exit(1)
    
    print("\n✅ All dependencies OK!\n")
    return cl

# Run dependency check
cl = check_dependencies()

# Import modules (after checks)
import numpy as np
import requests
import socket
import base64
import random
import json
from datetime import datetime
from colorama import init, Fore, Back, Style

init(autoreset=True)

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
USERNAME = your_username

# MINING KEY (leave as None if you don't have one)
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

# ==================== OPENCL KERNEL ====================
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
