import sys
import getpass

from db import (
    init_db,
    master_password_exists,
    set_master_password,
    verify_master_password,
    add_entry,
    get_entry,
    list_entries,
    delete_entry,
)
from crypto_utils import encrypt_password, decrypt_password


def cmd_add():
    name = input("Name: ").strip()
    login = input("Login: ").strip()
    password = getpass.getpass("Password: ")
    encrypted = encrypt_password(password)
    try:
        add_entry(name, login, encrypted)
        print(f"Entry '{name}' added.")
    except Exception as e:
        print(f"Error: {e}")


def cmd_get(name):
    row = get_entry(name)
    if row is None:
        print(f"Entry '{name}' not found.")
        return
    login, encrypted = row
    password = decrypt_password(encrypted)
    print(f"Login: {login}")
    print(f"Password: {password}")


def cmd_list():
    entries = list_entries()
    if not entries:
        print("No entries.")
        return
    print(f"{'Name':<20} {'Login':<30}")
    print("-" * 50)
    for name, login in entries:
        print(f"{name:<20} {login:<30}")


def cmd_delete(name):
    if delete_entry(name):
        print(f"Entry '{name}' deleted.")
    else:
        print(f"Entry '{name}' not found.")


def cmd_new():
    print("Setting new master password.")
    while True:
        p1 = getpass.getpass("New master password: ")
        p2 = getpass.getpass("Repeat: ")
        if p1 == p2 and len(p1) > 0:
            set_master_password(p1)
            print("Master password updated.")
            return
        print("Passwords do not match or empty. Try again.")


def repl():
    print("Type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if cmd in ("exit", "quit"):
            break
        elif cmd == "help":
            print("Commands:")
            print("  add            - add a new entry")
            print("  get <name>     - retrieve password by name")
            print("  list           - show all entries")
            print("  delete <name>  - delete entry by name")
            print("  new            - change master password")
            print("  exit / quit    - exit")
        elif cmd == "add":
            cmd_add()
        elif cmd == "get":
            if arg:
                cmd_get(arg)
            else:
                print("Usage: get <name>")
        elif cmd == "list":
            cmd_list()
        elif cmd == "delete":
            if arg:
                cmd_delete(arg)
            else:
                print("Usage: delete <name>")
        elif cmd == "new":
            cmd_new()
        else:
            print(f"Unknown command: {cmd}. Type 'help'.")


def main():
    init_db()

    if not master_password_exists():
        print("First run — set up master password.")
        while True:
            p1 = getpass.getpass("New master password: ")
            p2 = getpass.getpass("Repeat: ")
            if p1 == p2 and len(p1) > 0:
                set_master_password(p1)
                print("Master password saved.")
                break
            print("Passwords do not match or empty. Try again.")

    p = getpass.getpass("Master password: ")
    if not verify_master_password(p):
        print("Wrong password.")
        sys.exit(1)

    repl()


if __name__ == "__main__":
    main()
