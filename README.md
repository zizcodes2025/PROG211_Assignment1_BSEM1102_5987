# PROG211_Assignment1_BSEM1102_5987
A Python OOP application for small-business inventory monitoring and stock-loss tracking.

# StockGuard — Small Business Stock Loss and Expiry Tracker

A simple, menu-driven Python program that helps small retailers keep product
records, watch expiry dates, record stock losses (expired or damaged items) and
see how much money those losses cost.

> **Assignment:** PROG211 Object-Oriented Programming 1 — Individual Assignment
> "Real-World Solutions under DPG Standards", Limkokwing University of Creative
> Technology, Sierra Leone (Semester 3, September 2026 – February 2027).
> **Author:** Abdul Aziz Sesay

## 1. Overview and problem statement

Small shops often track stock on paper. It is then hard to know what is in
stock, which products are close to expiry, and how much money has been lost
through expired or damaged goods. StockGuard keeps these records in a small
Python program so the owner can see the problem clearly.

## 2. Objectives

- Register products with quantity, unit cost and (optional) expiry date.
- Show which products are expired or approaching expiry.
- Record losses caused by expiry or damage and update the stock.
- Calculate the total money lost.
- Demonstrate classes, objects, a list, instance methods and a class method.

## 3. Target users

Small retailers and shop owners in Sierra Leone and similar communities.

## 4. Features

1. Add a product (ID, name, category, quantity, unit cost, optional expiry date)
2. Display all products
3. Search for a product by ID
4. Check expiry status (Expired / Approaching expiry / Not yet in warning period / No expiry date), with a configurable warning period (default 30 days)
5. Record a stock loss (expiry or damage) and reduce the stock
6. Loss summary (products, quantity in stock, products needing attention, loss incidents, total loss)
7. Exit

## 5. Technologies and prerequisites

- Python 3.9 or newer (tested on Python 3.13). Only the standard library is used (`datetime`, `decimal`, `unittest`). Nothing needs to be installed.

## 6. Installation and running

```bash
git clone https://github.com/<your-username>/StockGuard.git
cd StockGuard
python main.py        # on some systems: python3 main.py
```

## 7. Running the tests

```bash
python -m unittest -v
```

18 automated tests are in `test_stockguard.py`.

## 8. Example session

Lines after `>` are typed by the user. Today's date in this example is 2026-10-27.

```text
Choose an option (1-7): > 1
--- Add a product ---
Product ID: > P001
Product name: > Milk
Category: > Dairy
Quantity in stock: > 20
Unit cost (Le): > 10.50
Expiry date YYYY-MM-DD (press Enter if none): > 2026-10-20
Product P001 (Milk) added.
   ... (P002 Yoghurt 10 @ 5.25 exp 2026-11-10, P003 Notebook 50 @ 3.00 no expiry,
        P004 Rice 5kg 8 @ 90 exp 2027-06-01 are added the same way) ...

Choose an option (1-7): > 1
Product ID: > p001
  Error: Product ID P001 already exists.

Choose an option (1-7): > 2
--- All products ---
ID       Name                 Category       Qty      Unit cost  Expiry
-----------------------------------------------------------------------
P001     Milk                 Dairy           20       Le 10.50  2026-10-20
P002     Yoghurt              Dairy           10        Le 5.25  2026-11-10
P003     Notebook             Stationery      50        Le 3.00  None
P004     Rice 5kg             Grocery          8       Le 90.00  2027-06-01

Choose an option (1-7): > 4
Warning period in days [30] (press Enter to keep): >
Today: 2026-10-27   Warning period: 30 days
  P001     Milk                 qty 20   Expired (-7 days)
  P002     Yoghurt              qty 10   Approaching expiry (14 days)
  P003     Notebook             qty 50   No expiry date
  P004     Rice 5kg             qty 8    Not yet in warning period (217 days)

Choose an option (1-7): > 5
Product ID: > P001
  Milk: 20 in stock at Le 10.50 each.
  Reason: 1. Expiry   2. Damage
Choose reason (1/2): > 1
Quantity lost: > 5
  Loss recorded: 5 x Milk (expiry) = Le 52.50. Stock left: 15.

Choose an option (1-7): > 5
Product ID: > P003      (reason 2, quantity 4)
  Loss recorded: 4 x Notebook (damage) = Le 12.00. Stock left: 46.

Choose an option (1-7): > 5
Product ID: > P004      (reason 2, quantity 9)
  Error: Cannot lose 9; only 8 in stock.

Choose an option (1-7): > 6
--- Loss summary ---
  Registered products:               4
  Total quantity in stock:           79
  In-stock products expired/expiring: 2
  Loss incidents recorded:           2
  Total financial loss:              Le 64.50
```

(The output above is from a real run of the program; the day count for expired
products is shown as a negative number of days.)

## 9. OOP concepts demonstrated

| Concept | Where |
|---|---|
| Classes | `Product`, `StockLossTracker` in `stockguard.py` |
| Attributes | `product_id, name, category, quantity, unit_cost, expiry_date, loss_incidents, quantity_lost, loss_value`; `products`, `warning_days` |
| Objects and interaction | Each product is a `Product` object stored in the tracker; the tracker calls the product's methods (`record_loss`, `expiry_status`) |
| `__init__()` | Validates and sets the attributes of both classes |
| Instance methods | `Product.expiry_status()`, `Product.record_loss()`, `Product.days_until_expiry()`, `StockLossTracker.add_product()`, `find_product()`, `record_loss()`, `summary()` ... |
| Class method | `Product.from_text()` (`@classmethod`) |
| Static methods (extra, Lecture 4) | `Product.parse_quantity()`, `parse_cost()`, `parse_expiry()` |
| Class attributes / constants | `LOSS_REASONS`, `DEFAULT_WARNING_DAYS`, `DATE_FORMAT`, `CURRENCY` |

## 10. Classes and responsibilities

- **`Product`** — one product. It knows its own details, works out its own expiry status and records a loss against itself (checking everything before changing anything).
- **`StockLossTracker`** — the manager. It owns the list of products, finds products, rejects duplicate IDs, produces the expiry report and the summary totals.

They are separate because one describes a single item and the other manages the collection, which keeps each class small and easy to explain.

The two required functions, `add_record(tracker, product)` and `display_records(tracker)`, work on the tracker's list.
`main.py` contains only the menu and user input.

## 11. Data structure: the list

All products are stored in **one Python list**: `StockLossTracker.products`.
A list was chosen because the shop has a small number of products, the order of entry is kept, and looping through a list to display or search is simple.
No dictionary or second list is used.
To find a product the program loops through the same list (`find_product`).
Loss records are stored inside each `Product` object (`loss_incidents`, `quantity_lost`, `loss_value`), so no second collection is needed.
A tuple (`LOSS_REASONS = ("expiry", "damage")`) is used only as a fixed constant, not to store product records.

## 12. Instance methods and the class method

- An **instance method** works on one existing object through `self`, e.g. `milk.record_loss(5, "expiry")` changes Milk's own quantity.
- The **class method** `Product.from_text(...)` receives `cls`, not `self`. It is used to *create* a new `Product` from text typed by a user: it converts and validates the text, then calls the constructor. It is called on the class (`Product.from_text(...)`), before any object exists.

## 13. Calculation rules and assumptions

- Dates use Python's `datetime`; they are never compared as text. Format: `YYYY-MM-DD`.
- An expiry date **equal to today counts as Expired**. Products with no expiry date are never expired.
- "Approaching expiry" means 1 to *N* days left (default N = 30).
- Money uses `Decimal`, rounded to 2 decimal places; the currency label is "Le" (display only).
- Loss value = quantity lost × the product's unit cost at that time.
- An **expiry loss** is only accepted for a product whose expiry date has been reached; use **damage** otherwise.
- A loss cannot be more than the stock; a failed entry changes nothing.
- The summary counts only products that still have stock when counting "expired/expiring".

## 14. Digital Public Goods (DPG) principles

| Principle | What this project does |
|---|---|
| Open source | Source code is plain Python, uploaded to GitHub under the MIT Licence. |
| Inclusive and accessible | Text-only menu that works with screen readers; plain English; numbered choices; clear error messages; no colour or mouse needed; runs on any computer with Python and no internet. |
| Privacy-respecting | No names, phone numbers or other personal data are asked for or stored. Only product data is used, and nothing is written to disk or sent anywhere. |
| Modular | Logic (`stockguard.py`), menu (`main.py`) and tests (`test_stockguard.py`) are separate; each class and method has one job. |
| Reusable | `stockguard.py` has no `input()` or menu code, so it can be reused in other programs; the idea works for any shop or store. |

StockGuard follows these principles as a student project. It has **not** been
reviewed or certified by the Digital Public Goods Alliance.

## 15. Limitations

- Data is kept **in memory only** and is lost when the program closes (the brief does not require saving).
- Only one user at a time; command-line only; one warning period for all products.
- Individual loss events are not listed; only totals per product are kept.
- Unit cost cannot be edited after a product is added.

## 16. Possible future improvements (not implemented)

Saving records to a file, editing products, a list of individual loss events, reports by category, translation of the menu into Krio.

## 17. Licence

MIT Licence — see the `LICENSE` file.

## 18. Author

Abdul Aziz Sesay — Software Engineering, Limkokwing University of Creative Technology, Sierra Leone.
