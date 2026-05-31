import shlex

from models import Player, Session, Transaction, TransactionType
from storage import delete_session, get_session, list_sessions, save_session

active_session = None


# Returns the prompt string to display to the user.
def get_prompt():
    if active_session:
        return f"[{active_session.name}] > "
    return "> "


# Prints a report of the session's transactions and players.
def print_report(session):
    width = 60

    # find the widest amount so we can align everything to it
    all_amounts = [session.total_income, session.total_expenses, session.net_profit]
    all_amounts += [t.amount for t in session.transactions]
    amt_width = max(len(f"{a:,.2f}") for a in all_amounts) if all_amounts else 10

    desc_width = width - amt_width - 10  # 10 = padding + " aUEC" + "[+] "

    print("\n" + "─" * width)
    print(f"│{'Session Report':^{width - 2}}│")
    print("─" * width)
    print(f"  Session: {session.name}\n")

    if session.players:
        print(" Players:")
        for p in session.players:
            print(f"  {p.name}")

    if session.transactions:
        print("\nTransactions:")
        for t in session.transactions:
            symbol = "+" if t.type == TransactionType.INCOME else "-"
            print(
                f"  [{symbol}] {t.description:<{desc_width}} {t.amount:>{amt_width},.2f} aUEC"
            )
    else:
        print("\n  No transactions yet.")

    print("\n" + "─" * width)
    print(
        f"  {'Income:':<{desc_width + 4}} {session.total_income:>{amt_width},.2f} aUEC"
    )
    print(
        f"  {'Expenses:':<{desc_width + 4}} {session.total_expenses:>{amt_width},.2f} aUEC"
    )
    print(
        f"  {'Net profit:':<{desc_width + 4}} {session.net_profit:>{amt_width},.2f} aUEC"
    )
    print("─" * width + "\n")


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
      help                     show this help message
      new <name>               create a new session
      use <name>               set active session
      unuse                    clear active session
      delete <name>            delete a session
      list                     show all sessions
      add-player <name>        add a player to active session
      remove-player <name>     remove a player from active session
      income <desc> <amount>   record income
      expense <desc> <amount>  record an expense
      report                   show session report
      quit                     exit

    Aliases:
      help                h, ?
      delete              del
      list                ls
      add-player          addp
      remove-player       rmp
      income              inc, i
      expense             exp, e
      report              rep, r
      quit                exit, q

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

    # Player managment commands
    # Add player
    elif cmd in ("add-player", "addp"):
        if len(parts) < 2:
            print("Usage: add-player <name>")
            return
        s = active_session
        if not s:
            print("No active session. Use 'use <name>' first.")
            return
        s.players.append(Player(name=parts[1]))
        save_session(s)
        print(f"Added player '{parts[1]}'.")

    # Remove player
    elif cmd in ("remove-player", "rmp"):
        if len(parts) < 2:
            print("Usage: remove-player <name>")
            return
        s = active_session
        if not s:
            print("No active session. Use 'use <name>' first.")
            return
        before = len(s.players)
        s.players = [p for p in s.players if p.name.lower() != parts[1].lower()]
        if len(s.players) == before:
            print(f"No player named '{parts[1]}'.")
            return
        save_session(s)
        print(f"Removed player '{parts[1]}'.")

    # Finances managment commands
    # Add income
    elif cmd in ("income", "inc", "i"):
        if len(parts) < 3:
            print("Usage: income <desc> <amount>")
            return
        s = active_session
        if not s:
            print("No active session. Use 'use <name>' first.")
            return
        try:
            amount = float(parts[2])
        except ValueError:
            print(f"'{parts[2]}' isn't a valid number.")
            return
        s.transactions.append(Transaction(parts[1], amount, TransactionType.INCOME))
        save_session(s)
        print(f"Added income: {parts[1]} — {amount}")

    # Add expense
    elif cmd in ("expense", "exp", "e"):
        if len(parts) < 3:
            print("Usage: expense <desc> <amount>")
            return
        s = active_session
        if not s:
            print("No active session. Use 'use <name>' first.")
            return
        try:
            amount = float(parts[2])
        except ValueError:
            print(f"'{parts[2]}' isn't a valid number.")
            return
        s.transactions.append(Transaction(parts[1], amount, TransactionType.EXPENSE))
        save_session(s)
        print(f"Added expense: {parts[1]} — {amount}")

    # Session report
    elif cmd in ("report", "rep", "r"):
        s = active_session
        if not s:
            print("No active session. Use 'use <name>' first.")
            return
        print_report(s)

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
