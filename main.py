import shlex

from models import Player, Session, Transaction, TransactionType
from storage import delete_session, get_session, list_sessions, save_session

active_session = None


# Returns the prompt string to display to the user.
def get_prompt():
    if active_session:
        return f"[{active_session.name}] > "
    return "> "


# Handles the user's command.
def handle_command(parts):
    global active_session
    if not parts:
        return

    cmd = parts[0].lower()

    # Quit command
    if cmd in ("quit", "exit", "q"):
        print("Bye citizen! o7")
        raise SystemExit

    # Help command
    elif cmd in ("help", "h", "?"):
        print("""
    Commands:
      help                show this help message
      new <name>          create a new session
      use <name>          set active session
      unuse               clear active session
      delete <name>       delete a session
      list                show all sessions
      quit                exit

    Aliases:
      help                h, ?
      delete              del
      list                ls
      quit                exit, q

    Coming soon:
      income <desc> <amt>
      expense <desc> <amt>
      add-player <name>
      report
    """)

    # Session management commands
    # New session
    elif cmd == "new":
        if len(parts) < 2:
            print("Usage: new <name>")
            return
        name = parts[1]
        s = Session(name=name)
        save_session(s)
        print(f"Created session '{name}'.")

    # Use session
    elif cmd == "use":
        if len(parts) < 2:
            print("Usage: use <name>")
            return
        s = get_session(parts[1])
        if not s:
            print(f"No session named '{parts[1]}'.")
            return
        active_session = s
        print(f"Now using '{s.name}'.")

    # Unuse session
    elif cmd == "unuse":
        active_session = None
        print("Cleared active session.")

    # Delete session
    elif cmd in ("delete", "del"):
        if len(parts) < 2:
            print("Usage: delete <name>")
            return
        deleted = delete_session(parts[1])
        if deleted:
            print(f"Deleted '{parts[1]}'.")
            if active_session and active_session.name.lower() == parts[1].lower():
                active_session = None
        else:
            print(f"No session named '{parts[1]}'.")

    # List sessions
    elif cmd in ("list", "ls"):
        sessions = list_sessions()
        if not sessions:
            print("No sessions yet.")
        for s in sessions:
            print(f"  {s.name}  —  net: {s.net_profit}")

    # If command is unrecognised
    else:
        print(f"Unknown command '{cmd}'. Type 'help' for help.")


# Main loop of the application.
def main():
    print("FinTrack — type 'help' for commands, 'quit' to exit.")
    while True:
        try:
            raw = input(get_prompt())
            parts = shlex.split(raw)
            handle_command(parts)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break
        except SystemExit:
            break
    input("Press any key to exit...")


# Entry point of the application.
if __name__ == "__main__":
    main()
