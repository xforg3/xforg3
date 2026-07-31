#!/usr/bin/env python3
"""
terminal.py - Terminal Menu dengan 2 Opsi
---------------------------------------
Menu untuk mengakses FREQUENCY dan SOSIALS
"""

import os
import sys
import shutil
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
    "purple": "\033[95m",
    "white": "\033[97m",
    "blue": "\033[94m",
    "magenta": "\033[35m",
}

BOX_WIDTH = 44  # lebar isi box (di antara ╔...╗)

# ================= Util =================

def get_size():
    return shutil.get_terminal_size(fallback=(80, 24))

def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()

def draw_box_top():
    print(f"\n{COLORS['green']}{BOLD}╔{'═' * BOX_WIDTH}╗{RESET}")

def draw_box_bottom():
    print(f"{COLORS['green']}{BOLD}╚{'═' * BOX_WIDTH}╝{RESET}")

def draw_box_title(title: str):
    """Cetak baris judul dalam box, padding dihitung otomatis
    biar sisi kanan box selalu nyambung rapi."""
    inner = f" {title}"
    pad = BOX_WIDTH - len(inner)
    if pad < 0:
        inner = inner[:BOX_WIDTH]
        pad = 0
    print(
        f"{COLORS['green']}{BOLD}║{RESET}"
        f"{COLORS['yellow']}{BOLD}{inner}{RESET}"
        f"{' ' * pad}"
        f"{COLORS['green']}{BOLD}║{RESET}"
    )

# ================= Menu Terminal =================

def terminal_menu():
    """Menu utama terminal dengan 2 opsi - Rata Kiri"""
    clear_screen()

    # Header - Rata Kiri
    draw_box_top()
    draw_box_title("XFORG3 TERMINAL MENU")
    draw_box_bottom()

    print()

    # Menu Options - Rata Kiri
    print(f"  {COLORS['cyan']}{BOLD}[1]{RESET} {COLORS['purple']}FREQUENCY{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[2]{RESET} {COLORS['purple']}SOSIALS{RESET}")
    print()
    print(f"  {COLORS['cyan']}{BOLD}[3]{RESET} {COLORS['red']}BACK{RESET}")

    print()
    # Garis pemisah yang menyambung
    terminal_width = shutil.get_terminal_size().columns
    line_length = min(terminal_width - 4, 40)  # Max 40 karakter
    print(f"  {COLORS['yellow']}{BOLD}{'=' * line_length}{RESET}")
    print()

    # Input
    try:
        choice = input(f"  {COLORS['cyan']}{BOLD}pilihan : {RESET}")
    except (KeyboardInterrupt, EOFError):
        return "3"

    return choice.strip()

# ================= Menu Sosials =================

def sosials_menu():
    """Menu untuk SOSIALS - Rata Kiri"""
    clear_screen()

    draw_box_top()
    draw_box_title("SOSIALS MENU")
    draw_box_bottom()

    print()
    print(f"  {COLORS['yellow']}{BOLD}[1]{RESET} {COLORS['green']}Social Media Scanner{RESET}")
    print(f"  {COLORS['yellow']}{BOLD}[2]{RESET} {COLORS['green']}Social Media Analysis{RESET}")
    print(f"  {COLORS['yellow']}{BOLD}[3]{RESET} {COLORS['green']}Export Data{RESET}")
    print()
    print(f"  {COLORS['yellow']}{BOLD}[0]{RESET} {COLORS['red']}Back{RESET}")

    print()
    # Garis pemisah yang menyambung
    terminal_width = shutil.get_terminal_size().columns
    line_length = min(terminal_width - 4, 40)  # Max 40 karakter
    print(f"  {COLORS['magenta']}{BOLD}{'=' * line_length}{RESET}")
    print()

    try:
        choice = input(f"  {COLORS['yellow']}{BOLD}pilihan : {RESET}")
    except (KeyboardInterrupt, EOFError):
        return "0"

    return choice.strip()

# ================= Eksekusi Script =================

def run_frequency_script():
    """Menjalankan script frequency dari folder frequency/frequency.py"""
    script_path = os.path.join(os.path.dirname(__file__), "frequency", "frequency.py")

    if os.path.exists(script_path):
        print(f"\n  {COLORS['green']}[✓] Menjalankan: {script_path}{RESET}")
        time.sleep(1)
        os.execvp(sys.executable, [sys.executable, script_path])
        return True
    else:
        print(f"\n  {COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        print(f"  {COLORS['yellow']}Pastikan file berada di: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")
        return False

def run_sosials_script():
    """Menjalankan script sosials dari folder sosials/sosials.py"""
    script_path = os.path.join(os.path.dirname(__file__), "sosials", "sosials.py")

    if os.path.exists(script_path):
        print(f"\n  {COLORS['green']}[✓] Menjalankan: {script_path}{RESET}")
        time.sleep(1)
        os.execvp(sys.executable, [sys.executable, script_path])
        return True
    else:
        print(f"\n  {COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        print(f"  {COLORS['yellow']}Pastikan file berada di: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")
        return False

def run_xforg3():
    """Kembali ke xforg3.py di parent directory"""
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "xforg3.py")

    if os.path.exists(script_path):
        print(f"\n  {COLORS['green']}[✓] Kembali ke: {script_path}{RESET}")
        time.sleep(1)
        os.execvp(sys.executable, [sys.executable, script_path])
        return True
    else:
        print(f"\n  {COLORS['red']}[✗] xforg3.py tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")
        return False

# ================= Main App =================

def app_loop():
    """Loop utama aplikasi"""
    while True:
        choice = terminal_menu()

        if choice == "1":  # FREQUENCY - langsung jalankan script
            clear_screen()
            print(f"\n  {COLORS['green']}[+] Starting FREQUENCY...{RESET}\n")
            time.sleep(1)
            if run_frequency_script():
                return  # Script akan menggantikan proses

        elif choice == "2":  # SOSIALS
            while True:
                sos_choice = sosials_menu()

                if sos_choice == "0":
                    break
                elif sos_choice == "1":
                    clear_screen()
                    print(f"\n  {COLORS['green']}[+] Starting Social Media Scanner...{RESET}\n")
                    time.sleep(1)
                    if run_sosials_script():
                        return
                elif sos_choice == "2":
                    clear_screen()
                    print(f"\n  {COLORS['green']}[+] Starting Social Media Analysis...{RESET}\n")
                    time.sleep(1)
                    input("\n  Tekan Enter untuk kembali...")
                elif sos_choice == "3":
                    clear_screen()
                    print(f"\n  {COLORS['green']}[+] Exporting Data...{RESET}\n")
                    time.sleep(1)
                    input("\n  Tekan Enter untuk kembali...")
                else:
                    print(f"\n  {COLORS['red']}[!] Pilihan tidak valid!{RESET}")
                    time.sleep(1)

        elif choice == "3":  # BACK - Kembali ke xforg3.py
            clear_screen()
            print(f"\n  {COLORS['green']}[+] Kembali ke XFORG3...{RESET}\n")
            time.sleep(1)
            if run_xforg3():
                return  # Script akan menggantikan proses
            # Jika gagal, lanjutkan loop

        else:
            print(f"\n  {COLORS['red']}[!] Pilihan tidak valid!{RESET}")
            time.sleep(1)

def main():
    try:
        app_loop()
    except KeyboardInterrupt:
        clear_screen()
        print(f"\n  {COLORS['yellow']}[!] Program dihentikan oleh user{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()