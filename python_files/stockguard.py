"""StockGuard core module.

Contains the two classes (Product and StockLossTracker) and the two
required record functions (add_record and display_records).

All product objects are stored in ONE Python list held by StockLossTracker.
Records live in memory only and are lost when the program exits.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# ---------------------------------------------------------------------------
# Constants (simple, readable settings)
# ---------------------------------------------------------------------------
CURRENCY = "Le"                    # Sierra Leonean leone (display only)
DATE_FORMAT = "%Y-%m-%d"           # e.g. 2026-12-31
DEFAULT_WARNING_DAYS = 30          # default "approaching expiry" window
LOSS_REASONS = ("expiry", "damage")  # tuple: a fixed set that must not change

STATUS_EXPIRED = "Expired"
STATUS_EXPIRING = "Approaching expiry"
STATUS_OK = "Not yet in warning period"
STATUS_NO_EXPIRY = "No expiry date"


def money(amount):
    """Format a Decimal amount as money, e.g. 'Le 1,250.00'."""
    return f"{CURRENCY} {amount:,.2f}"


# ---------------------------------------------------------------------------
# Class 1: Product
# ---------------------------------------------------------------------------
class Product:
    """One product in a small shop's stock."""

    def __init__(self, product_id, name, category, quantity, unit_cost,
                 expiry_date=None):
        """Create a product. Raises ValueError if any value is invalid."""
        product_id = str(product_id).strip().upper()
        name = str(name).strip()
        category = str(category).strip()

        if not product_id:
            raise ValueError("Product ID cannot be empty.")
        if not name:
            raise ValueError("Product name cannot be empty.")
        if not category:
            raise ValueError("Category cannot be empty.")
        if isinstance(quantity, bool) or not isinstance(quantity, int) \
                or quantity < 0:
            raise ValueError("Quantity must be a whole number (0 or more).")
        if expiry_date is not None and not isinstance(expiry_date, date):
            raise ValueError("Expiry date must be a date or None.")

        try:
            cost = Decimal(str(unit_cost))
        except InvalidOperation:
            raise ValueError("Unit cost must be a number.")
        if not cost.is_finite() or cost < 0:
            raise ValueError("Unit cost must be a number that is not negative.")

        self.product_id = product_id
        self.name = name
        self.category = category
        self.quantity = quantity
        self.unit_cost = cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.expiry_date = expiry_date

        # Loss history for this product (kept inside the object so that no
        # second list or dictionary is needed).
        self.loss_incidents = 0
        self.quantity_lost = 0
        self.loss_value = Decimal("0.00")

    # ---- static parsing helpers (used by the class method below) ----------
    @staticmethod
    def parse_quantity(text):
        """Convert text to a whole number >= 0, or raise ValueError."""
        text = text.strip()
        if not (text.isascii() and text.isdigit()):
            raise ValueError("Quantity must be a whole number (0 or more).")
        return int(text)

    @staticmethod
    def parse_cost(text):
        """Convert text to a non-negative Decimal, or raise ValueError."""
        try:
            cost = Decimal(text.strip())
        except InvalidOperation:
            raise ValueError("Unit cost must be a number, e.g. 12.50.")
        if not cost.is_finite() or cost < 0:
            raise ValueError("Unit cost must be a number that is not negative.")
        return cost

    @staticmethod
    def parse_expiry(text):
        """Convert 'YYYY-MM-DD' to a date. Empty text means no expiry (None)."""
        text = text.strip()
        if text == "":
            return None
        try:
            return datetime.strptime(text, DATE_FORMAT).date()
        except ValueError:
            raise ValueError("Invalid date. Use YYYY-MM-DD, e.g. 2026-12-31.")

    # ---- class method -----------------------------------------------------
    @classmethod
    def from_text(cls, product_id, name, category, quantity_text,
                  cost_text, expiry_text=""):
        """Build a Product from raw text typed by the user.

        A class method is used because it creates a NEW object of the class
        (it receives `cls`, not an existing object `self`). It converts and
        validates the text first, then calls the normal constructor.
        """
        return cls(
            product_id,
            name,
            category,
            cls.parse_quantity(quantity_text),
            cls.parse_cost(cost_text),
            cls.parse_expiry(expiry_text),
        )

    # ---- instance methods -------------------------------------------------
    def days_until_expiry(self, today=None):
        """Days from today to the expiry date (None if no expiry date)."""
        if self.expiry_date is None:
            return None
        today = today or date.today()
        return (self.expiry_date - today).days

    def expiry_status(self, today=None, warning_days=DEFAULT_WARNING_DAYS):
        """Return one of the STATUS_* texts.

        Rule: an expiry date that is today or earlier counts as Expired.
        """
        days = self.days_until_expiry(today)
        if days is None:
            return STATUS_NO_EXPIRY
        if days <= 0:
            return STATUS_EXPIRED
        if days <= warning_days:
            return STATUS_EXPIRING
        return STATUS_OK

    def record_loss(self, quantity, reason, today=None):
        """Record a loss (expiry or damage) and return its money value.

        Everything is checked BEFORE any attribute changes, so a failed
        attempt never leaves the product half-updated.
        """
        if reason not in LOSS_REASONS:
            raise ValueError("Reason must be 'expiry' or 'damage'.")
        if isinstance(quantity, bool) or not isinstance(quantity, int) \
                or quantity <= 0:
            raise ValueError("Quantity lost must be a whole number above 0.")
        if quantity > self.quantity:
            raise ValueError(
                f"Cannot lose {quantity}; only {self.quantity} in stock.")
        if reason == "expiry" and self.expiry_status(today) != STATUS_EXPIRED:
            raise ValueError(
                "An expiry loss needs a product whose expiry date has been "
                "reached. Use 'damage' for other losses.")

        value = self.unit_cost * quantity   # cost at the time of the loss
        self.quantity -= quantity
        self.quantity_lost += quantity
        self.loss_incidents += 1
        self.loss_value += value
        return value

    def stock_value(self):
        """Current value of the stock still held (quantity x unit cost)."""
        return self.unit_cost * self.quantity

    def __str__(self):
        expiry = self.expiry_date.strftime(DATE_FORMAT) \
            if self.expiry_date else "None"
        return (f"{self.product_id:<8} {self.name:<20} {self.category:<12} "
                f"{self.quantity:>5} {money(self.unit_cost):>14}  {expiry}")


# ---------------------------------------------------------------------------
# Class 2: StockLossTracker
# ---------------------------------------------------------------------------
class StockLossTracker:
    """Manages the product list and coordinates stock-loss operations."""

    def __init__(self, warning_days=DEFAULT_WARNING_DAYS):
        self.products = []              # the ONE required data structure
        self.set_warning_days(warning_days)

    def set_warning_days(self, warning_days):
        """Set the 'approaching expiry' window (whole days, 0 or more)."""
        if isinstance(warning_days, bool) or not isinstance(warning_days, int) \
                or warning_days < 0:
            raise ValueError("Warning period must be a whole number of days.")
        self.warning_days = warning_days

    def find_product(self, product_id):
        """Search the list for a product ID. Returns the Product or None."""
        wanted = str(product_id).strip().upper()
        for product in self.products:
            if product.product_id == wanted:
                return product
        return None

    def add_product(self, product):
        """Add a Product object to the list. Duplicate IDs are rejected."""
        if self.find_product(product.product_id) is not None:
            raise ValueError(f"Product ID {product.product_id} already exists.")
        self.products.append(product)

    def expiry_report(self, today=None):
        """Return a list of (product, status) for every product."""
        today = today or date.today()
        return [(p, p.expiry_status(today, self.warning_days))
                for p in self.products]

    def record_loss(self, product_id, quantity, reason, today=None):
        """Find the product, record the loss on it, return the loss value."""
        product = self.find_product(product_id)
        if product is None:
            raise ValueError(f"Product ID {str(product_id).strip().upper()} "
                             "was not found.")
        return product.record_loss(quantity, reason, today)

    def total_loss_value(self):
        return sum((p.loss_value for p in self.products), Decimal("0.00"))

    def total_loss_incidents(self):
        return sum(p.loss_incidents for p in self.products)

    def total_quantity_in_stock(self):
        return sum(p.quantity for p in self.products)

    def attention_count(self, today=None):
        """In-stock products that are expired or approaching expiry."""
        return sum(1 for p, status in self.expiry_report(today)
                   if p.quantity > 0 and status in (STATUS_EXPIRED,
                                                    STATUS_EXPIRING))

    def summary(self, today=None):
        """Return the financial summary as a dictionary of totals."""
        return {
            "products": len(self.products),
            "quantity_in_stock": self.total_quantity_in_stock(),
            "needing_attention": self.attention_count(today),
            "loss_incidents": self.total_loss_incidents(),
            "total_loss": self.total_loss_value(),
        }


# ---------------------------------------------------------------------------
# Required simple functions: add and display records
# ---------------------------------------------------------------------------
def add_record(tracker, product):
    """Add a Product object to the tracker's list (raises ValueError if the
    ID is a duplicate). Returns a confirmation message."""
    tracker.add_product(product)
    return f"Product {product.product_id} ({product.name}) added."


def display_records(tracker):
    """Print every product stored in the tracker's list."""
    if not tracker.products:
        print("No products registered yet.")
        return
    header = (f"{'ID':<8} {'Name':<20} {'Category':<12} {'Qty':>5} "
              f"{'Unit cost':>14}  Expiry")
    print(header)
    print("-" * len(header))
    for product in tracker.products:
        print(product)
