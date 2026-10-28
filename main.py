"""StockGuard - Small Business Stock Loss and Expiry Tracker.

Menu-driven command-line program. Run with:  python main.py
Records are kept in memory only and are not saved when the program ends.
"""

from datetime import date

from stockguard import (
    DEFAULT_WARNING_DAYS, LOSS_REASONS, Product, StockLossTracker,
    add_record, display_records, money,
)

MENU = """
========== StockGuard ==========
1. Add a product
2. Display all products
3. Search for a product
4. Check expiry status
5. Record a stock loss
6. Show loss summary
7. Exit
================================"""


def ask(prompt, parser):
    """Keep asking until the parser accepts the input."""
    while True:
        try:
            return parser(input(prompt))
        except ValueError as error:
            print(f"  Error: {error}")


def ask_required_text(prompt):
    """Ask for text that must not be empty."""
    def parser(text):
        if not text.strip():
            raise ValueError("This field cannot be empty.")
        return text.strip()
    return ask(prompt, parser)


def add_product_menu(tracker):
    print("\n--- Add a product ---")
    product_id = ask_required_text("Product ID: ")
    if tracker.find_product(product_id):
        print(f"  Error: Product ID {product_id.upper()} already exists.")
        return
    name = ask_required_text("Product name: ")
    category = ask_required_text("Category: ")
    quantity = ask("Quantity in stock: ", Product.parse_quantity)
    cost = ask("Unit cost (Le): ", Product.parse_cost)
    expiry = ask("Expiry date YYYY-MM-DD (press Enter if none): ",
                 Product.parse_expiry)
    try:
        product = Product(product_id, name, category, quantity, cost, expiry)
        print(add_record(tracker, product))
    except ValueError as error:
        print(f"  Error: {error}")


def search_menu(tracker):
    print("\n--- Search for a product ---")
    product_id = ask_required_text("Product ID to find: ")
    product = tracker.find_product(product_id)
    if product is None:
        print(f"  Product {product_id.upper()} was not found.")
        return
    print(f"  ID: {product.product_id}")
    print(f"  Name: {product.name}")
    print(f"  Category: {product.category}")
    print(f"  Quantity: {product.quantity}")
    print(f"  Unit cost: {money(product.unit_cost)}")
    print(f"  Expiry: {product.expiry_date or 'None'}")
    print(f"  Status: {product.expiry_status(date.today(), tracker.warning_days)}")


def expiry_menu(tracker):
    print("\n--- Check expiry status ---")
    text = input(f"Warning period in days [{tracker.warning_days}] "
                 "(press Enter to keep): ").strip()
    if text:
        try:
            tracker.set_warning_days(Product.parse_quantity(text))
        except ValueError:
            print(f"  Invalid period. Keeping {tracker.warning_days} days.")
    if not tracker.products:
        print("No products registered yet.")
        return
    today = date.today()
    print(f"Today: {today}   Warning period: {tracker.warning_days} days")
    for product, status in tracker.expiry_report(today):
        days = product.days_until_expiry(today)
        extra = "" if days is None else f" ({days} days)"
        print(f"  {product.product_id:<8} {product.name:<20} "
              f"qty {product.quantity:<4} {status}{extra}")


def loss_menu(tracker):
    print("\n--- Record a stock loss ---")
    if not tracker.products:
        print("No products registered yet.")
        return
    product_id = ask_required_text("Product ID: ")
    product = tracker.find_product(product_id)
    if product is None:
        print(f"  Product {product_id.upper()} was not found.")
        return
    print(f"  {product.name}: {product.quantity} in stock at "
          f"{money(product.unit_cost)} each.")
    print("  Reason: 1. Expiry   2. Damage")
    choice = input("Choose reason (1/2): ").strip()
    if choice not in ("1", "2"):
        print("  Error: please choose 1 or 2.")
        return
    reason = LOSS_REASONS[int(choice) - 1]
    quantity = ask("Quantity lost: ", Product.parse_quantity)
    try:
        value = tracker.record_loss(product_id, quantity, reason, date.today())
        print(f"  Loss recorded: {quantity} x {product.name} ({reason}) = "
              f"{money(value)}. Stock left: {product.quantity}.")
    except ValueError as error:
        print(f"  Error: {error}")


def summary_menu(tracker):
    print("\n--- Loss summary ---")
    data = tracker.summary(date.today())
    print(f"  Registered products:               {data['products']}")
    print(f"  Total quantity in stock:           {data['quantity_in_stock']}")
    print(f"  In-stock products expired/expiring: {data['needing_attention']}")
    print(f"  Loss incidents recorded:           {data['loss_incidents']}")
    print(f"  Total financial loss:              {money(data['total_loss'])}")


def main():
    tracker = StockLossTracker(DEFAULT_WARNING_DAYS)
    print("Welcome to StockGuard. Records are kept in memory only.")
    try:
        while True:
            print(MENU)
            choice = input("Choose an option (1-7): ").strip()
            if choice == "1":
                add_product_menu(tracker)
            elif choice == "2":
                print("\n--- All products ---")
                display_records(tracker)
            elif choice == "3":
                search_menu(tracker)
            elif choice == "4":
                expiry_menu(tracker)
            elif choice == "5":
                loss_menu(tracker)
            elif choice == "6":
                summary_menu(tracker)
            elif choice == "7":
                break
            else:
                print("  Invalid choice. Please enter a number from 1 to 7.")
    except (EOFError, KeyboardInterrupt):
        print()
    print("Goodbye. Remember: records were not saved.")


if __name__ == "__main__":
    main()
