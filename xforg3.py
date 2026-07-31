#!/usr/bin/env python3
"""
xforg3.py - Clean Terminal UI (Menu Only)
------------------------------------
Fungsi login password dan seluruh animasi glitch yang memperlambat performa telah dihapus.
Tampilan disamain konsepnya kayak terminal.py - box auto-align, tanpa ASCII art.
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
}

BOX_WIDTH = 44  # lebar isi box (di antara ╔...╗)

# ================= Util =================

def get_size():
    return shutil.get_terminal_size(fallback=(80, 24))

def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()

def draw_box_top():
    print(f"\n{COLORS['red']}{BOLD}╔{'═' * BOX_WIDTH}╗{RESET}")

def draw_box_bottom():
    print(f"{COLORS['red']}{BOLD}╚{'═' * BOX_WIDTH}╝{RESET}")

def draw_box_title(title: str):
    """Cetak baris judul dalam box, padding dihitung otomatis
    biar sisi kanan box selalu nyambung rapi."""
    inner = f" {title}"
    pad = BOX_WIDTH - len(inner)
    if pad < 0:
        inner = inner[:BOX_WIDTH]
        pad = 0
    print(
        f"{COLORS['red']}{BOLD}║{RESET}"
        f"{COLORS['yellow']}{BOLD}{inner}{RESET}"
        f"{' ' * pad}"
        f"{COLORS['red']}{BOLD}║{RESET}"
    )

# ================= Menu Utama =================

def main_menu():
    """Menu utama XFORG3 - Rata Kiri"""
    clear_screen()

    # Header
    draw_box_top()
    draw_box_title("XFORG3 MAIN MENU")
    draw_box_bottom()

    print()

    # Menu Options - Rata Kiri
    print(f"  {COLORS['cyan']}{BOLD}[1]{RESET} {COLORS['green']}TERMINAL{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[2]{RESET} {COLORS['green']}WEBSITE{RESET}")
    print()
    print(f"  {COLORS['cyan']}{BOLD}[0]{RESET} {COLORS['red']}EXIT{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[99]{RESET} {COLORS['red']}REGULAR{RESET}")

    print()
    # Garis pemisah yang menyambung
    terminal_width = shutil.get_terminal_size().columns
    line_length = min(terminal_width - 4, 40)  # Max 40 karakter
    print(f"  {COLORS['yellow']}{BOLD}{'=' * line_length}{RESET}")
    print()

    try:
        choice = input(f"  {COLORS['yellow']}>> option : {RESET}")
    except (KeyboardInterrupt, EOFError):
        return "0"

    if choice.strip() == "4":
        return "0"
    return choice.strip()

# ================= Alur Utama =================

def app_loop():
    while True:
        choice = main_menu()

        if choice == "1":  # TERMINAL
            clear_screen()
            terminal_path = os.path.join(os.path.dirname(__file__), "terminal", "terminal.py")
            if os.path.exists(terminal_path):
                os.execvp(sys.executable, [sys.executable, terminal_path])
            else:
                print(f"\n{COLORS['red']}[!] Terminal script tidak ditemukan: {terminal_path}{RESET}")
                input("\nTekan Enter untuk kembali...")

        elif choice == "2":  # WEBSITE
            clear_screen()
            website_path = os.path.join(os.path.dirname(__file__), "website", "website.py")
            if os.path.exists(website_path):
                os.execvp(sys.executable, [sys.executable, website_path])
            else:
                print(f"\n{COLORS['red']}[!] Website script tidak ditemukan: {website_path}{RESET}")
                input("\nTekan Enter untuk kembali...")

        elif choice == "0":
            clear_screen()
            break

        elif choice == "99":
            clear_screen()
            # Menjalankan perintah eksternal standar bawaan dari kode lama kamu
            os.system("ls")
            sys.exit(0)

        else:
            print(f"\n  {COLORS['red']}[!] Pilihan tidak valid!{RESET}")
            time.sleep(0.6)

def main():
    try:
        app_loop()
    except KeyboardInterrupt:
        clear_screen()
        sys.exit(0)

if __name__ == "__main__":
    main()