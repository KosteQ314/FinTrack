import shlex

from core.models import Player, Session, SplitConfig, Transaction, TransactionType
from core.storage import delete_session, get_session, list_sessions, save_session

active_session = None


# Command error crash prevention
def parse_amount(value):
    try:
        return int(float(value))  # float first to handle "5000.5", then round down
    except ValueError:
        print(f"'{value}' isn't a valid amount.")
        return None


# Returns the prompt string to display to the user.
def get_prompt():
    if active_session:
        return f"[{active_session.name}] > "
    return "> "


# Prints a report of the session's transactions and players.
def print_report(session):
    GREEN = "\033[92m"
    RED = "\033[31m"
    FAINT = "\033[2m"
    RESET = "\033[0m"

    width = 60
    all_amounts = [session.total_income, session.total_expenses, session.net_profit]
    all_amounts += [t.amount for t in session.transactions]
    all_amounts += list(session.calculate_split().values())
    amt_width = max(len(f"{int(a):,}") for a in all_amounts) if all_amounts else 10
    pct_width = 6
    # 2 (indent) + 2 (symbol + space) + desc + 2 (gap) + amt + 5 (" aUEC") = width
    desc_width = width - 2 - 2 - 2 - amt_width - 5

    print("\n" + "─" * width)
    print(f"│{'Session Report':^{width - 2}}│")
    print("─" * width)
    print(f" Session: {session.name}\n")

    if session.players:
        print(" Players:")
        for p in session.players:
            print(f"  {p.name}")

    if session.transactions:
        print("\n Transactions:")
        for t in session.transactions:
            symbol = "+" if t.type == TransactionType.INCOME else "-"
            color = GREEN if t.type == TransactionType.INCOME else RED
            amt_str = f"{t.amount:>{amt_width},} aUEC"
            desc_str = f"{t.description:<{desc_width}}"
            print(f"  {color}{symbol}{RESET} {desc_str}  {amt_str}")
    else:
        print("\n  No transactions yet.")

    income_str = f"{session.total_income:>{amt_width},} aUEC"
    expenses_str = f"{session.total_expenses:>{amt_width},} aUEC"
    net_str = f"{session.net_profit:>{amt_width},} aUEC"
    label_width = desc_width + 2

    print("\n" + "─" * width)
    print(f"  {'Income:':<{label_width}}  {GREEN}{income_str}{RESET}")
    print(f"  {'Expenses:':<{label_width}}  {RED}{expenses_str}{RESET}")
    print(f"  {'Net profit:':<{label_width}}  {net_str}")

    split = session.calculate_split()
    if split:
        total = sum(split.values())
        # split columns: 2 indent + desc + 2 gap + pct_width + 2 gap + amt + 5 aUEC
        split_desc_width = width - 2 - 2 - pct_width - 2 - amt_width - 5
        print("\n" + "─" * width)
        print(f"│{'Splits':^{width - 2}}│")
        print("─" * width)
        header_pct = f"{'%':>{pct_width}}"
        header_amt = f"{'Share':>{amt_width + 5}}"
        print(f"  {'Player':<{split_desc_width}}  {header_pct}  {header_amt}")
        print("─" * width)
        for name, amount in split.items():
            pct = (amount / total * 100) if total else 0
            pct_str = f"{pct:.1f}%"
            amt_str = f"{amount:>{amt_width},} aUEC"
            print(
                f"  {name:<{split_desc_width}}  {FAINT}{pct_str:>{pct_width}}{RESET}  {amt_str}"
            )

    print("─" * width + "\n")


# Handles the user's command.
def handle_command(parts):
    # Defines color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    B_BLACK = "\033[90m"
    B_RED = "\033[91m"
    B_GREEN = "\033[92m"
    B_YELLOW = "\033[93m"
    B_BLUE = "\033[94m"
    B_MAGENTA = "\033[95m"
    B_CYAN = "\033[96m"
    B_WHITE = "\033[97m"

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
        print(f"""
    Commands:
      {B_CYAN}help{RESET}                          show this help message
      {B_CYAN}new <name>{RESET}                    create a new session
      {B_CYAN}use <name>{RESET}                    set active session
      {B_CYAN}unuse{RESET}                         clear active session
      {B_CYAN}delete <name>{RESET}                 delete a session
      {B_CYAN}list{RESET}                          show all sessions
      {B_CYAN}add-player <name>{RESET}             add a player to active session
      {B_CYAN}remove-player <name>{RESET}          remove a player from active session
      {B_CYAN}income <desc> <amount>{RESET}        record income
      {B_CYAN}expense <desc> <amount>{RESET}       record an expense
      {B_CYAN}show <mode>{RESET}                   show active session details
      {B_CYAN}report{RESET}                        show session report
      {B_CYAN}split <mode> <name>:<value>{RESET}   split income
      {B_CYAN}quit{RESET}                          exit

    Aliases:
      {B_CYAN}help{RESET}                          h, ?
      {B_CYAN}delete{RESET}                        del
      {B_CYAN}list{RESET}                          ls
      {B_CYAN}add-player{RESET}                    addp
      {B_CYAN}remove-player{RESET}                 rmp
      {B_CYAN}income{RESET}                        inc, i
      {B_CYAN}expense{RESET}                       exp, e
      {B_CYAN}show{RESET}                          s
        player = p, transactions = t
      {B_CYAN}report{RESET}                        rep, r
      {B_CYAN}split{RESET}                         sp
        equal = e, percentage = p, fixed = f
      {B_CYAN}quit{RESET}                          exit, q

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
        amount = parse_amount(parts[2])
        if amount is None:
            return
        s.transactions.append(Transaction(parts[1], amount, TransactionType.INCOME))
        save_session(s)
        print(f"Added income: {parts[1]}   {B_GREEN}{amount}{RESET}")

    # Add expense
    elif cmd in ("expense", "exp", "e"):
        if len(parts) < 3:
            print("Usage: expense <desc> <amount>")
            return
        s = active_session
        if not s:
            print("No active session. Use 'use <name>' first.")
            return
        amount = parse_amount(parts[2])
        if amount is None:
            return
        s.transactions.append(Transaction(parts[1], amount, TransactionType.EXPENSE))
        save_session(s)
        print(f"Added expense: {parts[1]}   {RED}{amount}{RESET}")

    # Session Details
    elif cmd in ("show", "s"):
        s = active_session
        if not s:
            print("No active session. Use 'use <name>' first.")
            return
        if len(parts) < 2:
            print("Usage: show players | show transactions")
            return

        sub = parts[1].lower()

        if sub in ("players", "p"):
            if not s.players:
                print("No players in this session.")
            else:
                print("\nPlayers:")
                for p in s.players:
                    print(f"  {p.name} (id: {p.id})")
                print()

        elif sub in ("transactions", "t"):
            if not s.transactions:
                print("No transactions in this session.")
            else:
                all_amounts = [t.amount for t in s.transactions]
                amt_width = max(len(f"{a:,.0f}") for a in all_amounts)
                desc_width = 40 - amt_width
                print("\nTransactions:")
                for t in s.transactions:
                    symbol = "+" if t.type == TransactionType.INCOME else "-"
                    color = (
                        "\033[92m" if t.type == TransactionType.INCOME else "\033[31m"
                    )
                    reset = "\033[0m"
                    line = f"  {symbol} {t.description:<{desc_width}} {t.amount:>{amt_width},.0f} aUEC  (id: {t.id})"
                    print(line[:2] + color + line[2] + reset + line[3:])
                print()

        else:
            print(f"Unknown option '{sub}'. Use 'show players' or 'show transactions'.")

    # Session report
    elif cmd in ("report", "rep", "r"):
        s = active_session
        if not s:
            print("No active session. Use 'use <name>' first.")
            return
        print_report(s)

    # Split income
    elif cmd in ("split", "sp"):
        s = active_session
        if not s:
            print("No active session. Use 'use <name>' first.")
            return
        if len(parts) < 2:
            print(
                "Usage: split equal | split percentage Name:pct... | split fixed Name:amt..."
            )
            return

        mode = parts[1]

        if mode in ("equal", "e"):
            s.split_config = SplitConfig(mode="equal", overrides={})
            save_session(s)
            print("Split set: equal among all players.")

        elif mode in ("percentage", "p"):
            overrides = {}
            for pair in parts[2:]:
                name, pct = pair.split(":")
                overrides[name.lower()] = float(pct)
            s.split_config = SplitConfig(mode="percentage", overrides=overrides)
            save_session(s)
            assigned = sum(overrides.values())
            unassigned = [p for p in s.players if p.name.lower() not in overrides]
            remainder = (100 - assigned) / len(unassigned) if unassigned else 0
            print("Split set:")
            for p in s.players:
                pct = overrides.get(p.name.lower(), remainder)
                print(f"  {p.name}: {pct:.1f}%")

        elif mode in ("fixed", "f"):
            overrides = {}
            for pair in parts[2:]:
                name, amt = pair.split(":")
                overrides[name.lower()] = float(amt)
            s.split_config = SplitConfig(mode="fixed", overrides=overrides)
            save_session(s)
            print("Split set:")
            for p in s.players:
                amt = overrides.get(p.name.lower(), "remainder")
                print(
                    f"  {p.name}: {amt} aUEC"
                    if amt != "remainder"
                    else f"  {p.name}: remainder"
                )

        else:
            print(f"Unknown split mode '{mode}'. Use equal, percentage, or fixed.")

    # If command is unrecognised
    else:
        print(f"Unknown command '{cmd}'. Type 'help' for help.")


# Main loop of the application.
def main():
    GOLD = "\033[33m"
    BLUE = "\033[36m"
    RESET = "\033[0m"

    print(f"""{BLUE}
        ███████╗██╗███╗   ██╗████████╗██████╗  █████╗  ██████╗██╗  ██╗
        ██╔════╝██║████╗  ██║╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝
        █████╗  ██║██╔██╗ ██║   ██║   ██████╔╝███████║██║     █████╔╝
        ██╔══╝  ██║██║╚██╗██║   ██║   ██╔══██╗██╔══██║██║     ██╔═██╗
        ██║     ██║██║ ╚████║   ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗
        ╚═╝     ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝{GOLD}
       ╚═══════════════  Star Citizen Finance Tracker  ═══════════════╝{RESET}
        """)
    print("FinTrack — type 'help' for commands, 'quit' to exit.")
    while True:
        try:
            raw = input(get_prompt())
            parts = shlex.split(raw)
            handle_command(parts)
        except (KeyboardInterrupt, EOFError):
            print("\nBye citizen! o7")
            break
        except SystemExit:
            break
    input("Press Enter to exit...")


# Entry point of the application.
if __name__ == "__main__":
    main()
