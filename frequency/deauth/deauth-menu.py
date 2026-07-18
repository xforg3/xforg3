#!/usr/bin/env python3
import random
import time
import sys
import os

GLITCH_CHARS = "!@#$%^&*<>/\\|=+~`_-;:?01アイウエオ卍卐░▒▓█"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def glitch_print(text, duration=1.2, interval=0.04):
    """Efek teks glitch sebelum settle ke teks aslinya."""
    end_time = time.time() + duration
    while time.time() < end_time:
        glitched = ''.join(
            random.choice(GLITCH_CHARS) if random.random() < 0.35 else c
            for c in text
        )
        color = random.choice([RED, GREEN, YELLOW, CYAN, MAGENTA])
        sys.stdout.write(f"\r{color}{BOLD}{glitched}{RESET}")
        sys.stdout.flush()
        time.sleep(interval)
    sys.stdout.write(f"\r{GREEN}{BOLD}{text}{RESET}\n")
    sys.stdout.flush()


def glitch_line_flicker(text, times=6, interval=0.05):
    """Flicker on/off buat efek layar rusak."""
    for i in range(times):
        sys.stdout.write("\r" + " " * (len(text) + 5))
        sys.stdout.flush()
        time.sleep(interval / 2)
        color = random.choice([RED, CYAN, MAGENTA, GREEN])
        sys.stdout.write(f"\r{color}{BOLD}{text}{RESET}")
        sys.stdout.flush()
        time.sleep(interval)
    print()


def loading_sequence():
    clear()
    glitch_print("LOADING AIREPLAY-NG...", duration=1.4, interval=0.05)
    glitch_line_flicker("INITIALIZING AIREPLAY-NG...", times=5, interval=0.06)
    time.sleep(0.3)
    clear()


def launch_aireplay_ng():
    clear()
    glitch_print("LAUNCHING AIREPLAY-NG...", duration=0.9, interval=0.04)
    aireplay_path = os.path.join(os.path.dirname(__file__), "deauth.py")
    if os.path.exists(aireplay_path):
        os.execvp(sys.executable, [sys.executable, aireplay_path])
    print(f"{YELLOW}{BOLD}AIREPLAY-NG script not found. Placeholder only.{RESET}")
    time.sleep(0.5)


def show_menu():
    print(f"{CYAN}{'=' * 34}{RESET}")
    print(f"{BOLD}{YELLOW}      AIRCRACK-NG MENU{RESET}")
    print(f"{CYAN}{'=' * 34}{RESET}")
    print(f"{GREEN}1. AIREPLAY-NG{RESET}")
    print(f"{RED}0. BACK TO MAIN MENU{RESET}")
    print(f"{RED}99. EXIT{RESET}")
    print(f"{CYAN}{'=' * 34}{RESET}")


def main():
    loading_sequence()
    show_menu()
    choice = input(f"{BOLD}{MAGENTA}chose your option > {RESET}")

    if choice.strip() == "1":
        launch_aireplay_ng()
    elif choice.strip() == "0":
        parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frequency.py"))
        if not os.path.exists(parent):
            parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frequency.py"))
        os.execvp(sys.executable, [sys.executable, parent])
    elif choice.strip() == "99":
        clear()
        glitch_print("EXITING...", duration=0.8, interval=0.04)
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}Pilihan tidak valid!{RESET}")


if __name__ == "__main__":
    main()