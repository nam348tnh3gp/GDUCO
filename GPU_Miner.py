#!/usr/bin/env python3
"""
Duino-Coin GPU Miner – Intel Arc Compatible
Fixed OpenCL kernel: UINT32_MAX -> 0xFFFFFFFF
Reads config.txt | Real hashrate | Secure | All Linux + Windows GPU
"""

import sys
import os
import subprocess
import platform
import time
import re
import socket
import secrets
import json
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

MINER_VER = "4.3-gpu2"
SOFTWARE_NAME = f"Unofficial OpenCL PC/GPU Miner {MINER_VER}"
REQUEST_USER_AGENT = f"Duino-Coin-{SOFTWARE_NAME.replace(' ', '-')}"
UINT32_MAX = 0xFFFFFFFF
REQUIRED_GPU_DIFFICULTY = "EXTREME"
DEFAULT_GPU_LOAD_PERCENT = 25
MAX_ACCOUNT_MINERS = 25
AUTO_INSTALL_ENV = "DUCO_GPU_MINER_AUTO_INSTALL"
ALLOW_CUSTOM_POOL_ENV = "DUCO_GPU_MINER_ALLOW_CUSTOM_POOL"
ALLOW_NO_MINING_KEY_ENV = "DUCO_GPU_MINER_ALLOW_NO_MINING_KEY"

# ==================== CONFIG FILE PARSER ====================
def load_config_file(path="config.txt") -> Dict[str, str]:
    config = {}
    if not os.path.exists(path):
        print(f"❌ Config file '{path}' not found!")
        print("   Create it with at least USERNAME and MINING_KEY.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().upper()
            value = value.strip().strip('"').strip("'")
            config[key] = value
    return config

# ==================== DEPENDENCY HELPERS ====================
def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "y"}

def install_package(package: str) -> None:
    if not env_flag(AUTO_INSTALL_ENV):
        print(f"❌ Missing Python package: {package}")
        print(f"   Install manually or set {AUTO_INSTALL_ENV}=1")
        sys.exit(1)
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"✅ {package} installed. Re-run miner.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
    sys.exit(0)

def get_linux_distro() -> str:
    if not os.path.exists('/etc/os-release'):
        return "unknown"
    with open('/etc/os-release', 'r') as f:
        content = f.read().lower()
    if 'alpine' in content: return "alpine"
    if 'ubuntu' in content or 'debian' in content: return "debian"
    if 'fedora' in content: return "fedora"
    if 'arch' in content: return "arch"
    if 'centos' in content or 'rhel' in content: return "rhel"
    return "unknown"

def install_opencl_runtime_linux() -> bool:
    if not env_flag(AUTO_INSTALL_ENV):
        print("❌ OpenCL runtime missing. Install manually or enable auto-install.")
        return False
    distro = get_linux_distro()
    commands_map = {
        "alpine": [["apk", "add", "opencl-icd-loader", "clinfo"], ["apk", "add", "intel-opencl-icd"], ["apk", "add", "mesa-opencl-icd"]],
        "debian": [["apt", "update"], ["apt", "install", "-y", "opencl-headers", "clinfo", "ocl-icd-libopencl1"], ["apt", "install", "-y", "intel-opencl-icd"], ["apt", "install", "-y", "mesa-opencl-icd"]],
        "fedora": [["dnf", "install", "-y", "opencl-headers", "clinfo", "ocl-icd"], ["dnf", "install", "-y", "intel-opencl"], ["dnf", "install", "-y", "mesa-libOpenCL"]],
        "arch": [["pacman", "-S", "--noconfirm", "opencl-headers", "clinfo"], ["pacman", "-S", "--noconfirm", "intel-compute-runtime"], ["pacman", "-S", "--noconfirm", "opencl-mesa"]],
        "rhel": [["yum", "install", "-y", "opencl-headers", "clinfo", "ocl-icd"], ["yum", "install", "-y", "intel-opencl"], ["yum", "install", "-y", "mesa-libOpenCL"]]
    }
    for cmd in commands_map.get(distro, []):
        try:
            subprocess.run(cmd, capture_output=True, check=False, timeout=60)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    print("✅ OpenCL runtime installation attempted.")
    return True

def install_pyopencl_linux() -> bool:
    if not env_flag(AUTO_INSTALL_ENV):
        print("❌ pyopencl missing. Install manually or enable auto-install.")
        return False
    distro = get_linux_distro()
    package_map = {
        "alpine": ["apk", "add", "py3-opencl"],
        "debian": ["apt", "install", "-y", "python3-pyopencl"],
        "fedora": ["dnf", "install", "-y", "python3-pyopencl"],
        "arch": ["pacman", "-S", "--noconfirm", "python-pyopencl"]
    }
    if distro in package_map:
        try:
            subprocess.run(package_map[distro], capture_output=True, check=True, timeout=60)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyopencl"], capture_output=True, check=True, timeout=120)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False

def try_import_opencl():
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
    print("\n" + "="*60)
    print("🔍 Duino-Coin GPU Miner - Environment Check")
    print("="*60)
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ required!"); sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    system = platform.system()
    distro = None
    if system == "Linux":
        distro = get_linux_distro()
        print(f"📦 Detected: {distro.capitalize()} Linux")
        if distro == "alpine" and os.geteuid() != 0:
            print("⚠️ Alpine needs root. Use sudo."); sys.exit(1)
    for pkg in ["requests", "colorama", "numpy"]:
        try:
            __import__(pkg); print(f"✅ {pkg}")
        except ImportError:
            install_package(pkg)
    try:
        from colorama import init, Fore, Back, Style
        init(autoreset=True)
    except ImportError:
        class ColorFallback:
            def __getattr__(self, name): return ''
        Fore = Back = Style = ColorFallback()
    if system == "Linux":
        print("\n🔧 Checking OpenCL runtime...")
        try:
            subprocess.run(["clinfo"], capture_output=True, timeout=10)
            print("✅ OpenCL runtime OK")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️ OpenCL runtime not found, installing...")
            if install_opencl_runtime_linux():
                sys.exit(0)
    print("\n📦 Checking pyopencl...")
    if try_import_opencl() is None:
        if system == "Linux":
            if install_pyopencl_linux(): sys.exit(0)
        else:
            install_package("pyopencl")
    cl = try_import_opencl()
    if cl is None:
        print("❌ Cannot import OpenCL."); sys.exit(1)
    print("\n🔍 Testing OpenCL...")
    platforms = cl.get_platforms()
    print(f"✅ OpenCL platforms: {len(platforms)}")
    for p in platforms:
        for d in p.get_devices(device_type=cl.device_type.GPU):
            print(f"   🖥️ GPU: {d.name}")
    print("\n✅ All dependencies OK!\n")
    return cl, Fore, Back, Style

cl, Fore, Back, Style = check_dependencies()
import numpy as np
import requests

# ==================== SECURITY HELPERS ====================
def sanitize_protocol_field(value, fallback="None", max_len=96):
    text = str(value).strip() if value is not None else fallback
    text = re.sub(r"[\r\n,]", "_", text)
    return text[:max_len]

def display_mining_key(key):
    if key != "None" and len(key) > 8:
        return key[:4] + "..." + key[-4:]
    return key

def validate_pool_url(url):
    parsed = urlparse(url)
    if parsed.scheme == "https" and parsed.netloc.lower() == "server.duinocoin.com":
        return True
    if env_flag(ALLOW_CUSTOM_POOL_ENV):
        return True
    print(f"{Fore.RED}❌ Unsafe pool URL: {url}")
    return False

def check_disallowed_hosting():
    markers = ["GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI", "TRAVIS", "REPL_ID", "RENDER", "RAILWAY_ENVIRONMENT", "VERCEL", "NETLIFY", "HEROKU_APP_NAME"]
    detected = [m for m in markers if os.environ.get(m)]
    if detected:
        print(f"{Fore.RED}❌ Cloud/CI hosting detected: {', '.join(detected)}")
        return False
    return True

# ==================== GPU DETECTION ====================
def detect_gpus(cl_module):
    gpus = []
    for p_idx, p in enumerate(cl_module.get_platforms()):
        for d_idx, d in enumerate(p.get_devices(device_type=cl_module.device_type.GPU)):
            gpus.append({
                'platform_idx': p_idx, 'device_idx': d_idx,
                'platform_name': p.name, 'device_name': d.name,
                'max_compute_units': d.max_compute_units,
                'global_mem': d.global_mem_size // (1024*1024)
            })
    return gpus

# ==================== CONFIGURATION ====================
def load_config(cl_module):
    cfg_file = load_config_file("config.txt")
    USERNAME = cfg_file.get("USERNAME", "")
    MINING_KEY = cfg_file.get("MINING_KEY", "None")
    RIG_ID = cfg_file.get("RIG_ID", "GPU_Miner")
    GPU_LOAD_PERCENT = int(cfg_file.get("GPU_LOAD_PERCENT", DEFAULT_GPU_LOAD_PERCENT))
    GPU_PLATFORM = int(cfg_file["GPU_PLATFORM"]) if "GPU_PLATFORM" in cfg_file and cfg_file["GPU_PLATFORM"] != "None" else None
    GPU_DEVICE = int(cfg_file["GPU_DEVICE"]) if "GPU_DEVICE" in cfg_file and cfg_file["GPU_DEVICE"] != "None" else None
    POOL_URL = cfg_file.get("POOL_URL", "https://server.duinocoin.com/getPool")
    SOC_TIMEOUT = int(cfg_file.get("SOC_TIMEOUT", 10))
    REPORT_INTERVAL = int(cfg_file.get("REPORT_INTERVAL", 300))

    if not USERNAME:
        print(f"{Fore.RED}❌ USERNAME not set in config.txt!"); sys.exit(1)

    config = {
        "USERNAME": USERNAME,
        "MINING_KEY": MINING_KEY.strip(),
        "DIFFICULTY": REQUIRED_GPU_DIFFICULTY,
        "RIG_ID": sanitize_protocol_field(RIG_ID),
        "GPU_PLATFORM": GPU_PLATFORM,
        "GPU_DEVICE": GPU_DEVICE,
        "GPU_LOAD_PERCENT": max(1, min(100, GPU_LOAD_PERCENT)),
        "POOL_URL": POOL_URL,
        "SOC_TIMEOUT": SOC_TIMEOUT,
        "REPORT_INTERVAL": REPORT_INTERVAL,
    }

    print(f"{Fore.CYAN}🔍 DETECTING GPU...")
    gpus = detect_gpus(cl)
    if gpus:
        if config["GPU_PLATFORM"] is None or config["GPU_DEVICE"] is None:
            config["GPU_PLATFORM"] = gpus[0]['platform_idx']
            config["GPU_DEVICE"] = gpus[0]['device_idx']
            print(f"{Fore.GREEN}💡 Auto-selected: {gpus[0]['device_name']}")
    else:
        print(f"{Fore.YELLOW}⚠️ No GPU found.")
    
    if not validate_pool_url(config["POOL_URL"]):
        sys.exit(1)
    return config

# ==================== OPENCL KERNEL (FIXED) ====================
OPENCL_KERNEL = """
#define UINT32_MAX 0xFFFFFFFF
#define LEFT_ROTATE(x, n) (((x) << (n)) | ((x) >> (32 - (n))))

void sha1_transform(uint *state, const uchar *data) {
    uint w[80], a, b, c, d, e, temp;
    for (int i=0; i<16; i++) w[i] = ((uint)data[i*4]<<24)|((uint)data[i*4+1]<<16)|((uint)data[i*4+2]<<8)|(uint)data[i*4+3];
    for (int i=16; i<80; i++) w[i] = LEFT_ROTATE(w[i-3]^w[i-8]^w[i-14]^w[i-16], 1);
    a=state[0]; b=state[1]; c=state[2]; d=state[3]; e=state[4];
    for (int i=0; i<80; i++) {
        if (i<20) temp = LEFT_ROTATE(a,5) + ((b&c)|(~b&d)) + e + 0x5A827999 + w[i];
        else if (i<40) temp = LEFT_ROTATE(a,5) + (b^c^d) + e + 0x6ED9EBA1 + w[i];
        else if (i<60) temp = LEFT_ROTATE(a,5) + ((b&c)|(b&d)|(c&d)) + e + 0x8F1BBCDC + w[i];
        else temp = LEFT_ROTATE(a,5) + (b^c^d) + e + 0xCA62C1D6 + w[i];
        e=d; d=c; c=LEFT_ROTATE(b,30); b=a; a=temp;
    }
    state[0]+=a; state[1]+=b; state[2]+=c; state[3]+=d; state[4]+=e;
}

__kernel void ducos1_gpu(
    __global const uchar *last_hash,
    __global const uchar *target_hash,
    uint start_nonce,
    uint work_items,
    volatile __global uint *result_nonce
) {
    uint gid = get_global_id(0);
    if (gid >= work_items || *result_nonce != UINT32_MAX) return;
    uint nonce = start_nonce + gid;

    uchar message[64] = {0};
    for (int i=0; i<40; i++) message[i] = last_hash[i];
    uchar digits[10];
    uint dc=0, tmp=nonce;
    if (tmp==0) { digits[0]='0'; dc=1; }
    else { while(tmp>0 && dc<10) { digits[dc++] = (uchar)('0'+(tmp%10)); tmp/=10; } }
    for (uint i=0; i<dc; i++) message[40+i] = digits[dc-1-i];

    uint msg_len = 40+dc;
    ulong bit_len = (ulong)msg_len*8UL;
    message[msg_len]=0x80;
    message[56]=(uchar)(bit_len>>56); message[57]=(uchar)(bit_len>>48);
    message[58]=(uchar)(bit_len>>40); message[59]=(uchar)(bit_len>>32);
    message[60]=(uchar)(bit_len>>24); message[61]=(uchar)(bit_len>>16);
    message[62]=(uchar)(bit_len>>8);  message[63]=(uchar)(bit_len);

    uint state[5] = {0x67452301,0xEFCDAB89,0x98BADCFE,0x10325476,0xC3D2E1F0};
    sha1_transform(state, message);

    uchar hash_result[20];
    for (int i=0; i<5; i++) {
        hash_result[i*4]=(state[i]>>24)&0xFF; hash_result[i*4+1]=(state[i]>>16)&0xFF;
        hash_result[i*4+2]=(state[i]>>8)&0xFF; hash_result[i*4+3]=state[i]&0xFF;
    }

    bool match=true;
    for (int i=0; i<20; i++) if (hash_result[i]!=target_hash[i]) { match=false; break; }
    if (match) atomic_cmpxchg(result_nonce, UINT32_MAX, nonce);
}
"""

# ==================== GPU MINER CLASS ====================
class GPUMiner:
    def __init__(self, config, cl_module):
        self.config = config
        self.cl = cl_module
        self.context = self.queue = self.program = self.kernel = None
        self.max_work_size = 0
        self.stats = {'accepted': 0, 'rejected': 0, 'blocks': 0, 'total_hashrate': 0.0}

    def cleanup(self):
        for attr in ['kernel','program','queue','context']:
            if hasattr(self, attr) and getattr(self, attr):
                delattr(self, attr)

    def init_gpu(self):
        platforms = self.cl.get_platforms()
        if not platforms: raise RuntimeError("No OpenCL platform")
        if self.config["GPU_PLATFORM"] is not None and self.config["GPU_PLATFORM"] < len(platforms):
            self.platform = platforms[self.config["GPU_PLATFORM"]]
        else:
            self.platform = next((p for p in platforms if p.get_devices(device_type=self.cl.device_type.GPU)), platforms[0])
        devices = self.platform.get_devices(device_type=self.cl.device_type.GPU) or self.platform.get_devices()
        self.device = devices[self.config["GPU_DEVICE"]] if self.config["GPU_DEVICE"] is not None and self.config["GPU_DEVICE"] < len(devices) else devices[0]
        print(f"{Fore.GREEN}✅ GPU: {self.device.name}")
        self.max_work_size = self.device.max_work_group_size * self.device.max_compute_units * 4
        self.context = self.cl.Context([self.device])
        self.queue = self.cl.CommandQueue(self.context)
        print(f"{Fore.YELLOW}⏳ Compiling OpenCL kernel...")
        try:
            self.program = self.cl.Program(self.context, OPENCL_KERNEL).build()
            self.kernel = self.cl.Kernel(self.program, "ducos1_gpu")
            print(f"{Fore.GREEN}✅ Kernel compiled!")
        except Exception as e:
            print(f"{Fore.RED}❌ Kernel compilation failed: {e}")
            raise

    def solve_job(self, last_hash_hex, target_hex, difficulty):
        try:
            last_hash_bytes = last_hash_hex.encode("ascii")
            target_bytes = bytes.fromhex(target_hex)
        except ValueError:
            return None, 0.0, 0.0

        max_nonce = 100 * difficulty
        chunk_items = max(64, int(self.max_work_size * self.config["GPU_LOAD_PERCENT"] / 100))

        last_buf = self.cl.Buffer(self.context, self.cl.mem_flags.READ_ONLY | self.cl.mem_flags.COPY_HOST_PTR, hostbuf=last_hash_bytes)
        target_buf = self.cl.Buffer(self.context, self.cl.mem_flags.READ_ONLY | self.cl.mem_flags.COPY_HOST_PTR, hostbuf=target_bytes)
        result_buf = self.cl.Buffer(self.context, self.cl.mem_flags.READ_WRITE, 4)
        init_val = np.full(1, UINT32_MAX, dtype=np.uint32)
        self.cl.enqueue_copy(self.queue, result_buf, init_val)

        self.kernel.set_arg(0, last_buf)
        self.kernel.set_arg(1, target_buf)
        self.kernel.set_arg(5, result_buf)

        solve_start = time.time()
        total_checked = 0
        start_nonce = 0
        while start_nonce <= max_nonce:
            current_items = min(chunk_items, max_nonce - start_nonce + 1)
            local_size = min(64, current_items)
            global_size = ((current_items + local_size - 1) // local_size) * local_size
            self.kernel.set_arg(2, np.uint32(start_nonce))
            self.kernel.set_arg(3, np.uint32(current_items))
            self.cl.enqueue_nd_range_kernel(self.queue, self.kernel, (global_size,), (local_size,)).wait()
            total_checked += current_items

            res = np.zeros(1, dtype=np.uint32)
            self.cl.enqueue_copy(self.queue, res, result_buf).wait()
            if res[0] != UINT32_MAX:
                solve_time = time.time() - solve_start
                hashrate = total_checked / solve_time if solve_time > 0 else 0.0
                print(f"{Fore.GREEN}   [GPU] Found! Nonce: {res[0]}, Real HR: {hashrate/1e3:.2f} kH/s")
                return int(res[0]), hashrate, solve_time

            if self.config["GPU_LOAD_PERCENT"] < 100:
                time.sleep(0.003)
            start_nonce += current_items

        solve_time = time.time() - solve_start
        return None, 0.0, solve_time

# ==================== NETWORK CLIENT ====================
class DuinoClient:
    def __init__(self, config):
        self.config = config
        self.sock = None

    def get_pool(self):
        try:
            r = requests.get(self.config["POOL_URL"], timeout=10, headers={'User-Agent': REQUEST_USER_AGENT}).json()
            if r.get("success"):
                ip = sanitize_protocol_field(r["ip"])
                port = int(r["port"])
                name = sanitize_protocol_field(r.get("name","Unknown"))
                if ip and 1<=port<=65535:
                    return (ip, port, name)
        except: pass
        return ("server.duinocoin.com", 2813, "Default")

    def connect(self, pool):
        ip, port, name = pool
        if self.sock: self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.config["SOC_TIMEOUT"])
        self.sock.connect((ip, port))
        ver = self.sock.recv(256).decode().strip()
        return ver, name

    def send_job_request(self, user, diff, key):
        if not self.sock: return None,None,None
        msg = f"JOB,{sanitize_protocol_field(user,max_len=32)},{sanitize_protocol_field(diff,max_len=12)},{key},\n"
        self.sock.sendall(msg.encode())
        data = self.sock.recv(512).decode().strip()
        parts = data.split(',')
        if len(parts) >= 3:
            return parts[0], parts[1], int(parts[2])
        return None,None,None

    def submit_solution(self, nonce, hashrate, miner_name, rig_id, group_id):
        if not self.sock: return None
        msg = f"{nonce},{hashrate:.2f},{sanitize_protocol_field(miner_name,96)},{sanitize_protocol_field(rig_id,96)},{group_id}\n"
        self.sock.sendall(msg.encode())
        return self.sock.recv(512).decode().strip()

    def close(self):
        if self.sock:
            try: self.sock.close()
            except: pass
            self.sock = None

# ==================== UTILS ====================
def format_hashrate(h):
    if h>=1e9: return f"{h/1e9:.2f} GH/s"
    if h>=1e6: return f"{h/1e6:.2f} MH/s"
    if h>=1e3: return f"{h/1e3:.2f} kH/s"
    return f"{h:.2f} H/s"

def format_uptime(seconds):
    h,m,s = seconds//3600, (seconds%3600)//60, seconds%60
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

# ==================== MAIN ====================
def main():
    print(f"{Fore.CYAN}{'='*60}\n{Fore.YELLOW}🪙 Duino-Coin GPU Miner – Intel Arc Ready\n{Fore.CYAN}{'='*60}")
    if not check_disallowed_hosting(): sys.exit(1)
    config = load_config(cl)
    print(f"{Fore.GREEN}📋 Config: {config['USERNAME']}, Key: {display_mining_key(config['MINING_KEY'])}, Power: {config['GPU_LOAD_PERCENT']}%")
    
    miner = GPUMiner(config, cl)
    miner.init_gpu()
    client = DuinoClient(config)
    stats = miner.stats
    start_time = time.time()
    last_report = start_time
    group_id = secrets.randbelow(10000)
    
    print(f"\n{Fore.GREEN}✅ START MINING!")
    reconnect_attempts = 0
    try:
        while True:
            try:
                pool = client.get_pool()
                ver, name = client.connect(pool)
                print(f"{Fore.GREEN}✅ Connected {name} v{ver}")
                reconnect_attempts = 0
                while True:
                    lh, th, diff = client.send_job_request(config["USERNAME"], config["DIFFICULTY"], config["MINING_KEY"])
                    if not lh: time.sleep(1); continue
                    nonce, hr, t = miner.solve_job(lh, th, diff)
                    if nonce is not None:
                        fb = client.submit_solution(nonce, hr, SOFTWARE_NAME, config["RIG_ID"], group_id)
                        if fb is None:
                            print(f"{Fore.RED}❌ Connection lost"); break
                        if fb == "GOOD":
                            stats['accepted'] += 1
                            stats['total_hashrate'] = hr
                            print(f"{Fore.GREEN}✅ ACC #{stats['accepted']} | {format_hashrate(hr)} | {t:.3f}s")
                        elif fb == "BLOCK":
                            stats['blocks'] += 1; stats['accepted'] += 1
                            print(f"{Fore.YELLOW}⛓️🎉 BLOCK FOUND! +10 DUCO!")
                        elif fb.startswith("BAD"):
                            stats['rejected'] += 1
                            print(f"{Fore.RED}❌ REJECT #{stats['rejected']}")
                    if time.time()-last_report >= config["REPORT_INTERVAL"]:
                        uptime=int(time.time()-start_time)
                        total=stats['accepted']+stats['rejected']
                        rate=(stats['accepted']/total*100) if total>0 else 0
                        print(f"\n{Fore.CYAN}{'='*50}\n{Fore.YELLOW}📊 REPORT\n{Fore.CYAN}✅ {stats['accepted']} ❌ {stats['rejected']} ⛓️ {stats['blocks']} 📈 {rate:.1f}% 🚀 {format_hashrate(hr)}\n{Fore.CYAN}{'='*50}")
                        last_report=time.time()
            except (ConnectionError,socket.timeout) as e:
                reconnect_attempts+=1
                print(f"{Fore.RED}❌ Connection error: {e} ({reconnect_attempts}/10)")
                time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Mining stopped")
    finally:
        client.close()
        miner.cleanup()
        uptime=int(time.time()-start_time)
        total=stats['accepted']+stats['rejected']
        rate=(stats['accepted']/total*100) if total>0 else 0
        print(f"\n{Fore.GREEN}{'='*50}\n{Fore.YELLOW}📊 FINAL STATS\n{Fore.CYAN}✅ {stats['accepted']} ❌ {stats['rejected']} ⛓️ {stats['blocks']} 📈 {rate:.1f}% ⏱️ {format_uptime(uptime)}\n{Fore.GREEN}{'='*50}")

if __name__ == "__main__":
    main()
