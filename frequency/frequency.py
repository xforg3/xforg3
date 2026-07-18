#!/usr/bin/env python3
"""
Glitch Loading + Menu - Terminal
---------------------------------
Loading di tengah layar dengan efek glitch yang lebih "menggelegar":
kombinasi chromatic aberration, screen shake, dan flash noise, tapi
intensitasnya di-tune ke level SEDANG (nggak sampe bikin mata sakit).
Abis loading kelar, nongol ASCII art banner + menu pilihan dengan efek
glitch di prompt "pilih menu >".

Jalanin: python menu_glitch.py
"""

import os
import sys
import time
import random
import shutil

RESET = "\033[0m"
BOLD = "\033[1m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J\033[H"

RED = "\033[38;5;196m"
GREEN = "\033[38;5;46m"
BLUE = "\033[38;5;39m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"
YELLOW = "\033[93m"
MAGENTA = "\033[38;5;201m"
ORANGE = "\033[38;5;208m"

GLITCH_CHARS = "!@#$%^&*<>/\\|_+=~`░▒▓█"
NOISE_BLOCKS = "▓▒░█▌▐▄▀"

ASCII_ART = r""" (    (                         )           )  
 )\ ) )\ )     (             ( /(   (    ( /(  
(()/((()/((  ( )\     (  (   )\())  )\   )\()) 
 /(_))/(_))\ )((_)    )\ )\ ((_)\ (((_) ((_)\  
(_))_(_))((_|(_)_  _ ((_|(_) _((_))\_____ ((_) 
| |_ | _ \ __/ _ \| | | | __| \| ((/ __\ \ / / 
| __||   / _| (_) | |_| | _|| .` || (__ \ V /  
|_|  |_|_\___\__\_\\___/|___|_|\_| \___| |_|"""


def get_size():
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def move(row, col):
    sys.stdout.write(f"\033[{row};{col}H")


def clear():
    sys.stdout.write(CLEAR)


def print_at(row, col, text, color=""):
    if row < 1:
        row = 1
    if col < 1:
        col = 1
    move(row, col)
    sys.stdout.write(f"{color}{text}{RESET}")


def flush():
    sys.stdout.flush()


def flash_noise_line(row, width, color):
    """Satu baris noise block acak, buat nambah kesan 'menggelegar'."""
    line = "".join(random.choice(NOISE_BLOCKS) for _ in range(width))
    print_at(row, 1, line, color)


def loading(text="LOADING", duration=0.8, fps=60):
    """
    Progress bar kiri->kanan, tapi dibumbuin efek lebih rame:
    - leading edge tetep flicker glitch char sebelum solid
    - screen shake ringan (offset kolom acak +/-1) tiap beberapa frame
    - sesekali "flash burst": baris noise di atas & bawah bar + warna nyala
    - chromatic ghost: baris bayangan warna merah/biru dikit di atas bar
    Intensitas di-tune sedang, bukan ekstrem.
    """
    width, height = get_size()
    width = max(width, 40)
    row = height // 2
    label_row = row - 2
    ghost_row = row - 1
    bar_col = 2
    bar_width = width - 4  # sisa margin kiri-kanan 2 kolom

    sys.stdout.write(HIDE_CURSOR)
    clear()

    label_col = max(1, (width - len(text)) // 2)
    flush()

    frame_delay = duration / bar_width
    shake_offset = 0

    for filled in range(bar_width + 1):
        progress = filled / bar_width

        # --- screen shake ringan, berubah tiap ~6 frame ---
        if filled % 6 == 0:
            shake_offset = random.choice([-1, 0, 0, 0, 1])

        # --- label dengan sedikit chromatic ghost di kanan-kiri ---
        clear()  # biar shake berasa (nggak numpuk sisa frame lama)
        if random.random() < 0.12:
            print_at(label_row, label_col - 1, text, RED)
            print_at(label_row, label_col + 1, text, BLUE)
        print_at(label_row + shake_offset, label_col + shake_offset, text, WHITE + BOLD)

        # --- burst besar sesekali: noise block penuh + warna nyala ---
        is_burst = random.random() < 0.10
        if is_burst:
            burst_color = random.choice([RED, MAGENTA, ORANGE, CYAN])
            flash_noise_line(ghost_row, width, burst_color)

        chars = []
        for c in range(bar_width):
            if c < filled - 1:
                chars.append("█")
            elif c < filled:
                # 1-2 kolom di ujung fill: flicker glitch, makin rame kalau burst
                flicker_chance = 0.75 if is_burst else 0.55
                chars.append(random.choice(GLITCH_CHARS) if random.random() < flicker_chance else "█")
            else:
                if is_burst and random.random() < 0.08:
                    chars.append(random.choice(NOISE_BLOCKS))
                else:
                    chars.append(" ")

        if is_burst:
            edge_color = random.choice([RED, MAGENTA, ORANGE])
        elif progress < 1.0:
            edge_color = random.choice([RED, GREEN, BLUE, CYAN])
        else:
            edge_color = GREEN + BOLD

        bar_line = f"[{''.join(chars)}]"
        print_at(row + shake_offset, bar_col + shake_offset, bar_line, edge_color)
        print_at(row + 1 + shake_offset, bar_col + shake_offset, f"{int(progress * 100):3d}%", GRAY)
        flush()
        time.sleep(frame_delay)

    # settle: hapus shake/ghost, tampilan final bersih
    clear()
    print_at(label_row, label_col, text, WHITE + BOLD)
    print_at(row, bar_col, f"[{'█' * bar_width}]", GREEN + BOLD)
    print_at(row + 1, bar_col, "100%", GRAY)
    flush()
    time.sleep(0.2)


MENU_OPTIONS = ["BETTERCAP", "AIRCRACK-NG", "MDK4"]
LEFT_MARGIN = 5  # indent dari kiri, biar mirip layout screenshot
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
XFORG3_PATH = os.path.abspath(os.path.join(THIS_DIR, "..", "..", "xforg3.py"))
BETTERCAP_MENU_PATH = os.path.abspath(os.path.join(THIS_DIR, "bettercap", "bettercap-menu.py"))
AIRCRACK_MENU_PATH = os.path.abspath(os.path.join(THIS_DIR, "deauth", "deauth-menu.py"))
MDK4_MENU_PATH = os.path.abspath(os.path.join(THIS_DIR, "mdk4", "mdk4-menu.py"))


def draw_ascii_art(start_row=1):
    """Cetak ASCII art banner rata kiri, dikit indent biar senada sama menu."""
    lines = ASCII_ART.splitlines()
    row = start_row
    for line in lines:
        print_at(row, LEFT_MARGIN, line, CYAN + BOLD)
        row += 1
    return row


def draw_menu():
    """
    Tampilin ASCII art di atas, lalu menu RATA KIRI di bawahnya,
    style mirip terminal tool: opsi warna hijau, EXIT warna merah.
    """
    width, height = get_size()
    width = max(width, 40)

    clear()

    art_end_row = draw_ascii_art(start_row=2)

    row = art_end_row + 2  # jarak antara art dan menu
    for i, opt in enumerate(MENU_OPTIONS, start=1):
        print_at(row, LEFT_MARGIN, f"{i}. {opt}", GREEN + BOLD)
        row += 1

    row += 1  # baris kosong
    print_at(row, LEFT_MARGIN, "0. BACK TO MAIN MENU", RED + BOLD)
    row += 1
    print_at(row, LEFT_MARGIN, "99. EXIT", RED + BOLD)
    row += 2  # baris kosong sebelum prompt

    flush()
    return row, width


def glitch_prompt(row, width, text=">> option: ", bursts=12, delay=0.03):
    """
    Prompt yang flicker glitch dulu beberapa kali sebelum settle jadi teks
    asli. Sesekali nyelip noise block kecil di sisi kanan teks buat kesan
    lebih "rame", tapi tetap moderat. Posisinya rata kiri, sejajar menu.
    """
    col = LEFT_MARGIN

    for i in range(bursts):
        glitched = "".join(
            random.choice(GLITCH_CHARS) if ch != " " and random.random() < 0.55 else ch
            for ch in text
        )
        color = random.choice([RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA])

        # sesekali burst tambahan: noise block nempel di ujung teks
        suffix = ""
        if random.random() < 0.2:
            suffix = "".join(random.choice(NOISE_BLOCKS) for _ in range(3))

        print_at(row, col, glitched + suffix, color + BOLD)
        flush()
        time.sleep(delay)
        # bersihin suffix biar nggak numpuk kalau baris berikutnya lebih pendek
        if suffix:
            print_at(row, col + len(glitched), " " * len(suffix))

    print_at(row, col, text, YELLOW + BOLD)
    flush()
    sys.stdout.write(SHOW_CURSOR)
    flush()

    return input()


def launch_bettercap_menu():
    clear()
    os.execvp(sys.executable, [sys.executable, BETTERCAP_MENU_PATH])


def launch_mdk4_menu():
    clear()
    os.execvp(sys.executable, [sys.executable, MDK4_MENU_PATH])


def return_to_main_menu():
    clear()
    os.execvp(sys.executable, [sys.executable, XFORG3_PATH])


def exit_program():
    clear()
    print_at(2, LEFT_MARGIN, "EXITING...", RED + BOLD)
    flush()
    sys.exit(0)


def main():
    try:
        loading(text="LOADING", duration=0.8, fps=60)
        row, width = draw_menu()
        choice = glitch_prompt(row + 1, width)
        if choice.strip() == "1":
            launch_bettercap_menu()
        elif choice.strip() == "2":
            clear()
            os.execvp(sys.executable, [sys.executable, AIRCRACK_MENU_PATH])
        elif choice.strip() == "3":
            launch_mdk4_menu()
        elif choice.strip() == "0":
            return_to_main_menu()
        elif choice.strip() == "99":
            exit_program()
        else:
            print(f"\nLo milih: {choice}")
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR)
        flush()
        print()


if __name__ == "__main__":
    random.seed()
    main()