#!/usr/bin/env python3
"""
xforg3.py - Glitch Terminal UI (Menu Only)
------------------------------------
Fungsi fitur dilepas, fokus pada struktur dan animasi menu utama.
Ditambah animasi exit glitch.
"""

import os
import sys
import time
import random
import shutil

try:
    import termios
    import tty
    _PLATFORM = "unix"
except ImportError:
    try:
        import msvcrt
        _PLATFORM = "windows"
    except ImportError:
        _PLATFORM = "unsupported"

# ---------- Konfigurasi ----------
CORRECT_PASSWORD = "kingamba"
MAX_ATTEMPTS = 3

# ---------- ANSI ----------
RESET = "\033[0m"
BOLD = "\033[1m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J\033[H"

COLORS = {
    "green": "\033[92m",
    "bright_green": "\033[38;5;46m",
    "dim_green": "\033[38;5;22m",
    "red": "\033[91m",
    "gray": "\033[90m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
}

INPUT_GLITCH_CHARS = "!@#$%^&*<>/\\|_+=~`"
MATRIX_CHARS = "01アイウエオカキクケコサシスセソタチツテト"


# ================= Util layar =================

def move_cursor(row, col):
    sys.stdout.write(f"\033[{row};{col}H")


def get_size():
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def print_at(row, col, text, color=""):
    move_cursor(row, col)
    sys.stdout.write(f"{color}{text}{RESET}")


def clear_line(row, col, length):
    move_cursor(row, col)
    sys.stdout.write(" " * length)


def flush():
    sys.stdout.flush()


def restore_terminal():
    try:
        sys.stdout.write(RESET)
        sys.stdout.write(SHOW_CURSOR)
        _, height = get_size()
        move_cursor(height, 1)
        sys.stdout.write("\n")
        flush()
    except Exception:
        pass
    if _PLATFORM == "unix":
        try:
            os.system("stty sane")
        except Exception:
            pass


def _getch():
    if _PLATFORM == "unix":
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    elif _PLATFORM == "windows":
        ch = msvcrt.getch()
        try:
            return ch.decode("utf-8")
        except UnicodeDecodeError:
            return ""
    else:
        return None


def _readline_plain(prompt, color=COLORS["cyan"]):
    sys.stdout.write(f"{color}{prompt}{RESET}")
    flush()
    if _PLATFORM == "unsupported" or not sys.stdin.isatty():
        return input()
    buffer = ""
    while True:
        ch = _getch()
        if ch in ("\r", "\n"):
            sys.stdout.write("\n")
            flush()
            break
        elif ch in ("\x7f", "\x08"):
            if buffer:
                buffer = buffer[:-1]
                sys.stdout.write("\b \b")
                flush()
            continue
        elif ch == "\x03":
            raise KeyboardInterrupt
        elif ch is None or not ch.isprintable():
            continue
        else:
            sys.stdout.write(ch)
            flush()
            buffer += ch
    return buffer


# ================= Efek glitch dasar =================

def glitch_password_input(prompt, mask="*", glitch_frames=2, glitch_delay=0.02):
    sys.stdout.write(f"{COLORS['cyan']}{prompt}{RESET}")
    flush()

    if _PLATFORM == "unsupported" or not sys.stdin.isatty():
        import getpass
        return getpass.getpass("")

    buffer = ""
    while True:
        ch = _getch()

        if ch in ("\r", "\n"):
            sys.stdout.write("\n")
            flush()
            break
        elif ch in ("\x7f", "\x08"):
            if buffer:
                buffer = buffer[:-1]
                sys.stdout.write("\b \b")
                flush()
            continue
        elif ch == "\x03":
            raise KeyboardInterrupt
        elif ch is None or not ch.isprintable():
            continue
        else:
            for _ in range(glitch_frames):
                gc = random.choice(INPUT_GLITCH_CHARS)
                sys.stdout.write(f"{COLORS['red']}{gc}{RESET}")
                flush()
                time.sleep(glitch_delay)
                sys.stdout.write("\b")
            sys.stdout.write(f"{COLORS['gray']}{mask}{RESET}")
            flush()
            buffer += ch

    return buffer


def glitch_reveal_text(text, row, col, cycles=10, color=COLORS["bright_green"]):
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
                if random.random() < (c / cycles) * (i + 1) / n * 2:
                    revealed[i] = True
                    display.append(ch)
                else:
                    display.append(random.choice(INPUT_GLITCH_CHARS))
        print_at(row, col, "".join(display), color)
        flush()
        time.sleep(0.025)
    print_at(row, col, text, color + BOLD)
    flush()


def glitch_error_flash(width, height):
    row = random.randint(2, max(2, height - 2))
    length = random.randint(10, max(10, min(40, width - 4)))
    start_col = random.randint(1, max(1, width - length))
    junk = "".join(random.choice(INPUT_GLITCH_CHARS) for _ in range(length))
    print_at(row, start_col, junk, COLORS["red"])
    flush()
    time.sleep(0.03)
    clear_line(row, start_col, length)
    flush()


def rain_background(width, height, duration, density=0.02):
    end_time = time.time() + duration
    while time.time() < end_time:
        for x in range(width):
            if random.random() < density:
                y = random.randint(1, max(1, height - 2))
                ch = random.choice(MATRIX_CHARS)
                color = random.choice([COLORS["dim_green"], COLORS["green"]])
                print_at(y, x + 1, ch, color)
        flush()
        time.sleep(0.03)


def glitch_bar(row, col, width, percent, color=COLORS["cyan"]):
    filled = int(width * percent)
    bar = ""
    for i in range(width):
        if i < filled:
            bar += random.choice("█▓") if random.random() < 0.06 else "█"
        else:
            bar += random.choice(" .:-") if random.random() < 0.15 else " "
    pct_text = f"{int(percent * 100):3d}%"
    print_at(row, col, f"[{bar}] {pct_text}", color)
    flush()


def loading_sequence(title="SYSTEM BOOT", subtitle="INITIALIZING SECURE MODULE",
                      status_msgs=None):
    width, height = get_size()
    width = max(width, 40)
    center_col = max(1, (width - len(title)) // 2)

    sys.stdout.write(CLEAR)
    flush()

    rain_background(width, height, duration=0.45, density=0.025)

    sys.stdout.write(CLEAR)
    flush()

    glitch_reveal_text(title, height // 2 - 2, center_col, cycles=8)
    time.sleep(0.08)

    sub_col = max(1, (width - len(subtitle)) // 2)
    glitch_reveal_text(subtitle, height // 2 - 1, sub_col, cycles=6, color=COLORS["gray"])
    time.sleep(0.15)

    bar_width = min(50, width - 20)
    bar_col = max(1, (width - bar_width - 6) // 2)
    bar_row = height // 2 + 1

    if status_msgs is None:
        status_msgs = [
            "loading modules...",
            "rendering interface...",
            "preparing menu...",
        ]

    percent = 0.0
    while percent < 1.0:
        percent += random.uniform(0.01, 0.06)
        percent = min(percent, 1.0)
        glitch_bar(bar_row, bar_col, bar_width, percent)

        if random.random() < 0.25:
            glitch_error_flash(width, height)

        status = random.choice(status_msgs)
        status_col = max(1, (width - len(status)) // 2)
        print_at(bar_row + 2, status_col, status.ljust(30), COLORS["dim_green"])
        flush()

        time.sleep(random.uniform(0.01, 0.04))

    clear_line(bar_row + 2, 1, width)
    flush()
    time.sleep(0.3)


def access_granted():
    width, height = get_size()
    width = max(width, 40)
    text = "ACCESS GRANTED"
    col = max(1, (width - len(text)) // 2)
    row = height // 2

    sys.stdout.write(CLEAR)
    flush()
    glitch_reveal_text(text, row, col, cycles=14, color=COLORS["bright_green"])
    flush()
    time.sleep(0.9)


def access_denied(remaining):
    width, height = get_size()
    width = max(width, 40)
    text = "ACCESS DENIED"
    col = max(1, (width - len(text)) // 2)
    row = height // 2

    for _ in range(6):
        glitch_error_flash(width, height)

    for _ in range(5):
        offset = random.choice([-1, 0, 1])
        garbled = "".join(
            random.choice(INPUT_GLITCH_CHARS) if random.random() < 0.4 else ch
            for ch in text
        )
        shake_col = max(1, col + offset)
        print_at(row, shake_col, garbled, COLORS["red"])
        flush()
        time.sleep(0.05)
        clear_line(row, shake_col, len(garbled))

    print_at(row, col, text, COLORS["red"] + BOLD)
    flush()

    if remaining > 0:
        sub = f"{remaining} attempt(s) remaining"
        sub_col = max(1, (width - len(sub)) // 2)
        print_at(row + 2, sub_col, sub, COLORS["gray"])
        flush()

    time.sleep(1.1)


def lockout():
    width, height = get_size()
    width = max(width, 40)
    text = "SYSTEM LOCKED"
    col = max(1, (width - len(text)) // 2)
    row = height // 2

    for _ in range(8):
        glitch_error_flash(width, height)

    print_at(row, col, text, COLORS["red"] + BOLD)
    flush()
    time.sleep(1.3)


def glitch_exit_sequence():
    """Animasi saat program ditutup."""
    width, height = get_size()
    sys.stdout.write(CLEAR)
    flush()
    
    msg1 = "TERMINATING SESSION"
    msg2 = "DISCONNECTING..."
    
    col1 = max(1, (width - len(msg1)) // 2)
    glitch_reveal_text(msg1, height // 2 - 1, col1, cycles=10, color=COLORS["red"])
    time.sleep(0.3)
    
    col2 = max(1, (width - len(msg2)) // 2)
    print_at(height // 2 + 1, col2, msg2, COLORS["gray"])
    flush()
    
    # Animasi kedip error cepat
    for _ in range(15):
        glitch_error_flash(width, height)
        time.sleep(random.uniform(0.01, 0.04))
        
    sys.stdout.write(CLEAR)
    flush()
    time.sleep(0.2)


# ================= Menu / tampilan =================

def main_menu():
    """Menu utama POLOS tanpa bingkai dan penomoran berurutan ke bawah."""
    width, height = get_size()
    sys.stdout.write(CLEAR)
    flush()

    options = [
        "1. FREQUENCY",
        "",
        "0. EXIT",
        "99. REGULAR",
    ]
    
    start_row = height // 2 - len(options) // 2 - 2
    
    for i, opt in enumerate(options):
        col = 6  # Rata kiri menjorok 6 karakter dari tepi screen
        color = COLORS["green"]
        if opt in {"0. EXIT", "99. REGULAR"}:
            color = COLORS["red"]
        glitch_reveal_text(opt, start_row + i, col, cycles=6, color=color)
        time.sleep(0.02)

    move_cursor(start_row + len(options) + 2, 6)
    choice = _readline_plain(">> option : ", COLORS["yellow"])
    
    if choice.strip() == "4":
        return "0"
    return choice.strip()


# ================= Alur utama =================

def login_flow():
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        sys.stdout.write(CLEAR)
        flush()
        pwd = glitch_password_input("PASSWORD : ")
        if pwd == CORRECT_PASSWORD:
            access_granted()
            return True
        attempts += 1
        remaining = MAX_ATTEMPTS - attempts
        if remaining > 0:
            access_denied(remaining)
        else:
            lockout()
    return False


def app_loop():
    while True:
        choice = main_menu()
        if choice == "1":
            restore_terminal()
            menu_path = os.path.join(os.path.dirname(__file__), "frequency", "frequency.py")
            if not os.path.exists(menu_path):
                fallback_path = os.path.join(os.path.dirname(__file__), "frequency", "bettercap", "bettercap-menu.py")
                if os.path.exists(fallback_path):
                    menu_path = fallback_path
            os.execvp(sys.executable, [sys.executable, menu_path])
        elif choice == "2":
            # TODO: Taruh pemicu script/fungsi eksternal kamu di sini
            pass
        elif choice == "3":
            # TODO: Taruh pemicu script/fungsi eksternal kamu di sini
            pass
        elif choice == "0":  # Dipicu jika mengetik angka '4'
            glitch_exit_sequence()
            os.system("clear")
            break
        elif choice == "99":
            restore_terminal()
            os.system("clear")
            os.system("ls")
            sys.exit(0)
        else:
            width, height = get_size()
            msg = "invalid option"
            print_at(height - 2, 4, msg, COLORS["red"])
            flush()
            time.sleep(0.8)


def main():
    random.seed()
    sys.stdout.write(HIDE_CURSOR)
    flush()
    try:
        loading_sequence(title="SYSTEM BOOT", subtitle="INITIALIZING SECURE MODULE")
        if login_flow():
            app_loop()
    except KeyboardInterrupt:
        # Bakal trigger animasi ini juga kalau kamu maksa close pakai Ctrl+C
        glitch_exit_sequence()
    finally:
        restore_terminal()


if __name__ == "__main__":
    main()