#!/usr/bin/env python3
"""
frequency.py - Frequency Menu
---------------------------------
Menu untuk mengakses BETTERCAP, DEAUTH, MDK4, dan AIRGEDDON
Dengan navigasi keyboard (arrow keys)
"""

import os
import sys
import shutil
import time
import termios
import tty
import select

# ---------- ANSI ----------
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
    "purple": "\033[95m",
    "white": "\033[97m",
    "magenta": "\033[35m",
}

BOX_WIDTH = 44  # lebar isi box (di antara ╔...╗)

# ================= Keyboard Input =================

def get_key():
    """Membaca input keyboard tanpa Enter"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        
        # Arrow keys are represented by escape sequences
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                if ch3 in ['A', 'B', 'C', 'D']:
                    return f'\x1b[{ch3}'
            return ch
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def kbhit():
    """Cek apakah ada input keyboard"""
    return select.select([sys.stdin], [], [], 0)[0] != []

# ================= Util =================

def get_size():
    return shutil.get_terminal_size(fallback=(80, 24))

def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()

def draw_box_top():
    print(f"\n{COLORS['yellow']}{BOLD}╔{'═' * BOX_WIDTH}╗{RESET}")

def draw_box_bottom():
    print(f"{COLORS['yellow']}{BOLD}╚{'═' * BOX_WIDTH}╝{RESET}")

def draw_box_title(title: str):
    """Cetak baris judul dalam box, padding dihitung otomatis"""
    inner = f" {title}"
    pad = BOX_WIDTH - len(inner)
    if pad < 0:
        inner = inner[:BOX_WIDTH]
        pad = 0
    print(
        f"{COLORS['yellow']}{BOLD}║{RESET}"
        f"{COLORS['magenta']}{BOLD}{inner}{RESET}"
        f"{' ' * pad}"
        f"{COLORS['yellow']}{BOLD}║{RESET}"
    )

def draw_menu_item(label, description, selected=False, icon="➜"):
    """Menggambar item menu dengan highlight jika selected"""
    if selected:
        print(f"  {COLORS['cyan']}{BOLD}{icon}{RESET} {COLORS['green']}{BOLD}{description}{RESET}")
        print(f"     {COLORS['gray']}{label}{RESET}")
    else:
        print(f"  {COLORS['gray']}  {RESET} {COLORS['green']}{description}{RESET}")

# ================= Menu Frequency =================

def frequency_menu():
    """Menu utama dengan navigasi arrow keys"""
    clear_screen()
    sys.stdout.write(HIDE_CURSOR)
    
    menu_items = [
        {"id": "1", "label": "BETTERCAP", "desc": "BetterCAP Menu"},
        {"id": "2", "label": "DEAUTH", "desc": "Deauth Attack Menu"},
        {"id": "3", "label": "MDK4", "desc": "MDK4 Attack Menu"},
        {"id": "4", "label": "AIRGEDDON", "desc": "Airgeddon Tool"},
        {"id": "0", "label": "BACK", "desc": "Back to Main Menu"},
        {"id": "99", "label": "EXIT", "desc": "Exit Program"},
    ]
    
    current_selection = 0
    
    while True:
        # Clear and redraw
        clear_screen()
        
        # Header
        draw_box_top()
        draw_box_title("FREQUENCY MENU")
        draw_box_bottom()
        print()
        
        # Draw menu items
        for idx, item in enumerate(menu_items):
            if idx == current_selection:
                draw_menu_item(item["label"], item["desc"], True)
            else:
                draw_menu_item(item["label"], item["desc"], False)
        
        print()
        print(f"  {COLORS['gray']}Use {COLORS['cyan']}↑↓{COLORS['gray']} to navigate, {COLORS['green']}ENTER{COLORS['gray']} to select{RESET}")
        
        # Get key input
        key = get_key()
        
        if key == '\x1b[A':  # Up arrow
            current_selection = (current_selection - 1) % len(menu_items)
        elif key == '\x1b[B':  # Down arrow
            current_selection = (current_selection + 1) % len(menu_items)
        elif key == '\r' or key == '\n':  # Enter
            selected_item = menu_items[current_selection]
            sys.stdout.write(SHOW_CURSOR)
            return selected_item["id"]
        elif key == 'q' or key == 'Q':  # Quick exit
            sys.stdout.write(SHOW_CURSOR)
            return "99"
        elif key == 'b' or key == 'B':  # Quick back
            sys.stdout.write(SHOW_CURSOR)
            return "0"
        elif key in ['1', '2', '3', '4']:  # Number shortcuts
            sys.stdout.write(SHOW_CURSOR)
            return key
        elif key == '0':  # Number shortcut for back
            sys.stdout.write(SHOW_CURSOR)
            return "0"
        elif key == '9':  # Number shortcut for exit
            sys.stdout.write(SHOW_CURSOR)
            return "99"

# ================= Eksekusi Script =================

def launch_bettercap():
    """Menjalankan bettercap-menu.py"""
    script_path = os.path.join(os.path.dirname(__file__), "bettercap", "bettercap-menu.py")
    if os.path.exists(script_path):
        os.execvp(sys.executable, [sys.executable, script_path])
    else:
        print(f"\n  {COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def launch_deauth():
    """Menjalankan deauth-menu.py"""
    script_path = os.path.join(os.path.dirname(__file__), "deauth", "deauth-menu.py")
    if os.path.exists(script_path):
        os.execvp(sys.executable, [sys.executable, script_path])
    else:
        print(f"\n  {COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def launch_mdk4():
    """Menjalankan mdk4-menu.py"""
    script_path = os.path.join(os.path.dirname(__file__), "mdk4", "mdk4-menu.py")
    if os.path.exists(script_path):
        os.execvp(sys.executable, [sys.executable, script_path])
    else:
        print(f"\n  {COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def launch_airgeddon():
    """Menjalankan Airgeddon dengan sudo"""
    print(f"\n  {COLORS['green']}[+] Menjalankan Airgeddon...{RESET}\n")
    try:
        os.execvp("sudo", ["sudo", "airgeddon"])
    except FileNotFoundError:
        print(f"  {COLORS['red']}[✗] Airgeddon tidak ditemukan!{RESET}")
        print(f"  {COLORS['yellow']}Install Airgeddon dengan:{RESET}")
        print(f"  {COLORS['cyan']}git clone https://github.com/v1s1t0r1sh3r3/airgeddon.git{RESET}")
        print(f"  {COLORS['cyan']}cd airgeddon && sudo bash airgeddon.sh{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def return_to_main_menu():
    """Kembali ke xforg3.py di parent directory"""
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "xforg3.py")
    
    if os.path.exists(script_path):
        os.execvp(sys.executable, [sys.executable, script_path])
    else:
        print(f"\n  {COLORS['red']}[✗] xforg3.py tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def exit_program():
    sys.stdout.write(SHOW_CURSOR)
    clear_screen()
    sys.exit(0)

# ================= Main App =================

def app_loop():
    """Loop utama aplikasi"""
    while True:
        choice = frequency_menu()

        if choice == "1":  # BETTERCAP
            launch_bettercap()
        elif choice == "2":  # DEAUTH
            launch_deauth()
        elif choice == "3":  # MDK4
            launch_mdk4()
        elif choice == "4":  # AIRGEDDON
            launch_airgeddon()
            input("\n  Tekan Enter untuk kembali...")
        elif choice == "0":  # BACK TO MAIN MENU
            return_to_main_menu()
            return
        elif choice == "99":  # EXIT
            exit_program()
        else:
            print(f"\n  {COLORS['red']}[!] Pilihan tidak valid!{RESET}")
            time.sleep(1)

def main():
    try:
        app_loop()
    except KeyboardInterrupt:
        sys.stdout.write(SHOW_CURSOR)
        clear_screen()
        print(f"\n  {COLORS['yellow']}[!] Program dihentikan oleh user{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()