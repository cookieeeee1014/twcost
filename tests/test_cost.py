"""twcost 的成本計算測試。

README 裡出現的每個數字都必須在這裡被固定，跑不過就說明 README 在說謊。
"""

import unittest

from twcost import DayTrade, FeeSchedule, Trade


class TestFeeSchedule(unittest.TestCase):
    def test_min_fee_wins_on_small_amount(self):
        s = FeeSchedule()
        # 896.4 * 0.0855% = 0.77，低於最低收費 20
        self.assertEqual(s.fee(896.4), 20.0)

    def test_rate_wins_on_large_amount(self):
        s = FeeSchedule()
        # 100000 * 0.0855% = 85.5，高於最低收費
        self.assertAlmostEqual(s.fee(100000), 85.5, places=4)

    def test_tax_is_sell_side_only(self):
        s = FeeSchedule()
        self.assertAlmostEqual(s.tax(10000), 30.0, places=4)

    def test_daytrade_tax_is_half(self):
        s = FeeSchedule()
        self.assertAlmostEqual(s.tax(10000, daytrade=True), 15.0, places=4)


class TestTradeReadmeNumbers(unittest.TestCase):
    """README 的範例：1000 元買 0050 八股。"""

    def setUp(self):
        self.t = Trade(buy=112.05, sell=104.95, shares=8)

    def test_buy_amount(self):
        self.assertAlmostEqual(self.t.buy_amount, 896.40, places=2)

    def test_cost_breakdown(self):
        self.assertEqual(
            self.t.cost_breakdown(),
            {'buy_fee': 20.0, 'sell_fee': 20.0, 'tax': 2.52, 'total': 42.52},
        )

    def test_cost_ratio(self):
        self.assertAlmostEqual(self.t.cost_ratio(), 0.0474, places=4)

    def test_net_pnl(self):
        self.assertAlmostEqual(self.t.net_pnl(), -99.32, places=2)


class TestMinFeeTable(unittest.TestCase):
    """README 的表格：最低收費對往返成本的影響。"""

    @staticmethod
    def roundtrip(amount, min_fee, buy=100.0, sell=100.0):
        shares = int(amount // buy)
        s = FeeSchedule(min_fee=min_fee)
        t = Trade(buy=buy, sell=sell, shares=shares, schedule=s)
        return t.cost_ratio()

    def test_below_min_fee_threshold(self):
        # 單筆 1000，最低收費 20：成本約 4.30%
        self.assertAlmostEqual(self.roundtrip(1000, 20), 0.0430, places=3)

    def test_at_10000_min_fee_20(self):
        self.assertAlmostEqual(self.roundtrip(10000, 20), 0.0070, places=3)

    def test_at_10000_min_fee_1(self):
        self.assertAlmostEqual(self.roundtrip(10000, 1), 0.0047, places=3)

    def test_at_100000_min_fee_irrelevant(self):
        a = self.roundtrip(100000, 20)
        b = self.roundtrip(100000, 1)
        self.assertAlmostEqual(a, b, places=6)
        self.assertAlmostEqual(a, 0.0047, places=3)


class TestCustomSchedule(unittest.TestCase):
    """README 的自訂費率範例。"""

    def test_custom_schedule_example(self):
        s = FeeSchedule(discount=0.28, min_fee=1)
        t = Trade(buy=112.05, sell=104.95, shares=8, schedule=s)
        self.assertEqual(
            t.cost_breakdown(),
            {'buy_fee': 1, 'sell_fee': 1, 'tax': 2.52, 'total': 4.52},
        )
        self.assertAlmostEqual(t.cost_ratio(), 0.005, places=4)


class TestDayTrade(unittest.TestCase):
    def test_daytrade_tax_lower(self):
        normal = Trade(buy=100, sell=101, shares=1000)
        day = DayTrade(buy=100, sell=101, shares=1000)
        self.assertLess(day.tax, normal.tax)
        # 賣出金額 101,000：0.3% = 303，0.15% = 151.5，差 151.5
        self.assertAlmostEqual(normal.tax - day.tax, 151.5, places=2)

    def test_daytrade_total_cost_lower(self):
        normal = Trade(buy=100, sell=101, shares=1000)
        day = DayTrade(buy=100, sell=101, shares=1000)
        self.assertLess(day.total_cost, normal.total_cost)


class TestBreakEven(unittest.TestCase):
    def test_flat_price_loses_money(self):
        t = Trade(buy=100, sell=100, shares=1000)
        self.assertLess(t.net_pnl(), 0)

    def test_break_even_actually_breaks_even(self):
        t = Trade(buy=112.05, sell=104.95, shares=8)
        be = t.break_even()
        flat = Trade(buy=t.buy, sell=t.buy * (1 + be), shares=8)
        self.assertAlmostEqual(flat.net_pnl(), 0, delta=0.01)

    def test_small_trade_needs_more(self):
        small = Trade(buy=100, sell=100, shares=5)
        large = Trade(buy=100, sell=100, shares=5000)
        self.assertGreater(small.break_even(), large.break_even())


class TestValidation(unittest.TestCase):
    def test_zero_shares_rejected(self):
        with self.assertRaises(ValueError):
            Trade(buy=100, sell=100, shares=0)

    def test_negative_shares_rejected(self):
        with self.assertRaises(ValueError):
            Trade(buy=100, sell=100, shares=-1)


try:
    import tkinter  # noqa: F401
    HAS_TK = True
except Exception:
    HAS_TK = False


@unittest.skipUnless(HAS_TK, 'tkinter unavailable')
class TestGui(unittest.TestCase):
    """介面與計算共用 Trade，這裡確認綁定沒接錯。"""

    def setUp(self):
        import tkinter as tk
        from twcost.gui import App
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = App(self.root)
        self.root.update_idletasks()

    def tearDown(self):
        self.root.destroy()

    def test_defaults_match_readme(self):
        self.assertEqual(self.app.outputs['總成本'].get(), '42.52')
        self.assertEqual(self.app.outputs['買入金額'].get(), '896.40')
        self.assertEqual(self.app.outputs['淨損益'].get(), '-99.32')
        self.assertEqual(self.app.outputs['成本比'].get(), '4.74%')
        self.assertEqual(self.app.outputs['打平需漲'].get(), '4.78%')

    def test_recomputes_on_change(self):
        self.app.inputs['shares'].set('1000')
        self.root.update_idletasks()
        self.assertEqual(self.app.outputs['買入金額'].get(), '112,050.00')
        self.assertEqual(self.app.outputs['成本比'].get(), '0.45%')

    def test_invalid_input_blanks_outputs(self):
        self.app.inputs['buy'].set('abc')
        self.root.update_idletasks()
        for name, var in self.app.outputs.items():
            self.assertEqual(var.get(), '-', name)

    def test_zero_shares_blanks_outputs(self):
        self.app.inputs['shares'].set('0')
        self.root.update_idletasks()
        self.assertEqual(self.app.outputs['總成本'].get(), '-')


if __name__ == '__main__':
    unittest.main(verbosity=2)
