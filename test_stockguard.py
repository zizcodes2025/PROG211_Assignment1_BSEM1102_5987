"""Automated tests for StockGuard. Run with:  python -m unittest -v"""

import unittest
from datetime import date
from decimal import Decimal

from stockguard import (
    STATUS_EXPIRED, STATUS_EXPIRING, STATUS_NO_EXPIRY, STATUS_OK,
    Product, StockLossTracker, add_record, display_records,
)

TODAY = date(2026, 10, 27)   # fixed date so results never change


def make_tracker():
    """Tracker with four products used by several tests."""
    tracker = StockLossTracker()
    tracker.add_product(Product("P001", "Milk", "Dairy", 20, "10.50",
                                date(2026, 10, 20)))   # expired
    tracker.add_product(Product("P002", "Yoghurt", "Dairy", 10, "5.25",
                                date(2026, 11, 10)))   # 14 days -> approaching
    tracker.add_product(Product("P003", "Notebook", "Stationery", 50, "3.00"))
    tracker.add_product(Product("P004", "Rice 5kg", "Grocery", 8, "90.00",
                                date(2027, 6, 1)))     # far away
    return tracker


class TestAddAndDisplay(unittest.TestCase):
    def test_T01_add_valid_product(self):
        tracker = StockLossTracker()
        message = add_record(tracker, Product("p1", "Soap", "Home", 5, "2"))
        self.assertEqual(len(tracker.products), 1)
        self.assertEqual(tracker.products[0].product_id, "P1")
        self.assertIn("added", message)

    def test_T02_duplicate_id_rejected(self):
        tracker = make_tracker()
        with self.assertRaises(ValueError):
            tracker.add_product(Product("p001", "Other", "X", 1, "1"))
        self.assertEqual(len(tracker.products), 4)

    def test_T03_display_empty(self):
        import io
        from contextlib import redirect_stdout
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            display_records(StockLossTracker())
        self.assertIn("No products registered", buffer.getvalue())


class TestSearch(unittest.TestCase):
    def test_T04_search_existing(self):
        self.assertEqual(make_tracker().find_product("p002").name, "Yoghurt")

    def test_T05_search_missing(self):
        self.assertIsNone(make_tracker().find_product("P999"))


class TestExpiry(unittest.TestCase):
    def test_T06_expired(self):
        tracker = make_tracker()
        self.assertEqual(tracker.find_product("P001").expiry_status(TODAY),
                         STATUS_EXPIRED)

    def test_T07_approaching(self):
        tracker = make_tracker()
        self.assertEqual(tracker.find_product("P002").expiry_status(TODAY),
                         STATUS_EXPIRING)

    def test_T08_no_expiry_date(self):
        tracker = make_tracker()
        self.assertEqual(tracker.find_product("P003").expiry_status(TODAY),
                         STATUS_NO_EXPIRY)

    def test_T09_far_expiry_is_ok_and_today_is_expired(self):
        tracker = make_tracker()
        self.assertEqual(tracker.find_product("P004").expiry_status(TODAY),
                         STATUS_OK)
        today_product = Product("P9", "Bread", "Bakery", 1, "1", TODAY)
        self.assertEqual(today_product.expiry_status(TODAY), STATUS_EXPIRED)

    def test_T10_custom_warning_period(self):
        tracker = make_tracker()
        tracker.set_warning_days(5)
        statuses = {p.product_id: s for p, s in tracker.expiry_report(TODAY)}
        self.assertEqual(statuses["P002"], STATUS_OK)


class TestLosses(unittest.TestCase):
    def test_T11_valid_expiry_loss(self):
        tracker = make_tracker()
        value = tracker.record_loss("P001", 5, "expiry", TODAY)
        self.assertEqual(value, Decimal("52.50"))
        self.assertEqual(tracker.find_product("P001").quantity, 15)

    def test_T12_valid_damage_loss(self):
        tracker = make_tracker()
        value = tracker.record_loss("P003", 4, "damage", TODAY)
        self.assertEqual(value, Decimal("12.00"))
        self.assertEqual(tracker.find_product("P003").quantity, 46)

    def test_T13_loss_more_than_stock_rejected_no_change(self):
        tracker = make_tracker()
        with self.assertRaises(ValueError):
            tracker.record_loss("P004", 9, "damage", TODAY)
        product = tracker.find_product("P004")
        self.assertEqual(product.quantity, 8)
        self.assertEqual(product.loss_incidents, 0)
        self.assertEqual(tracker.total_loss_value(), Decimal("0.00"))

    def test_T14_invalid_quantities(self):
        tracker = make_tracker()
        for bad in (0, -3, 2.5):
            with self.assertRaises(ValueError):
                tracker.record_loss("P003", bad, "damage", TODAY)
        for text in ("abc", "-1", "2.5", "", "  "):
            with self.assertRaises(ValueError):
                Product.parse_quantity(text)
        with self.assertRaises(ValueError):
            Product.parse_cost("-5")
        with self.assertRaises(ValueError):
            Product.parse_cost("abc")

    def test_T15_invalid_date(self):
        for text in ("2026-13-45", "31/12/2026", "tomorrow", "2026-2-30"):
            with self.assertRaises(ValueError):
                Product.parse_expiry(text)
        self.assertIsNone(Product.parse_expiry(""))

    def test_T16_totals_and_final_stock(self):
        tracker = make_tracker()
        tracker.record_loss("P001", 5, "expiry", TODAY)    # 52.50
        tracker.record_loss("P001", 15, "expiry", TODAY)   # 157.50
        tracker.record_loss("P003", 4, "damage", TODAY)    # 12.00
        data = tracker.summary(TODAY)
        self.assertEqual(data["total_loss"], Decimal("222.00"))
        self.assertEqual(data["loss_incidents"], 3)
        self.assertEqual(data["quantity_in_stock"], 0 + 10 + 46 + 8)
        self.assertEqual(data["products"], 4)
        # P001 is expired but now has 0 stock, so only P002 needs attention
        self.assertEqual(data["needing_attention"], 1)
        # a further loss on the empty product must fail
        with self.assertRaises(ValueError):
            tracker.record_loss("P001", 1, "expiry", TODAY)

    def test_T17_loss_unknown_product_and_wrong_reason(self):
        tracker = make_tracker()
        with self.assertRaises(ValueError):
            tracker.record_loss("NOPE", 1, "damage", TODAY)
        with self.assertRaises(ValueError):
            tracker.record_loss("P003", 1, "expiry", TODAY)  # no expiry date
        with self.assertRaises(ValueError):
            tracker.record_loss("P004", 1, "expiry", TODAY)  # not expired yet
        with self.assertRaises(ValueError):
            tracker.record_loss("P003", 1, "theft", TODAY)

    def test_T18_class_method_builds_product(self):
        product = Product.from_text("a1", "Tea", "Grocery", "12", "7.5",
                                    "2027-01-31")
        self.assertEqual(product.unit_cost, Decimal("7.50"))
        self.assertEqual(product.quantity, 12)
        self.assertEqual(product.expiry_date, date(2027, 1, 31))
        with self.assertRaises(ValueError):
            Product.from_text("a2", "Tea", "Grocery", "-1", "7.5")


if __name__ == "__main__":
    unittest.main()
