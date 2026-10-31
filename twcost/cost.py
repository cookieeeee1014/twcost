"""台灣證券交易成本的計算。

規則來源：
- 手續費公定費率 0.1425%，電子單常見 6 折，券商多有單筆最低收費
- 證券交易稅：賣出時課徵 0.3%，當日沖銷減半為 0.15%
- 零股與整股適用相同費率

參考：台灣證券交易所「證券交易稅條例」、各券商費率表。
"""

from dataclasses import dataclass, field


@dataclass
class FeeSchedule:
    """券商費率方案。

    預設值取台灣常見條款：公定費率 0.1425%、電子單 6 折、單筆最低 20 元、
    賣出證交稅 0.3%、當沖 0.15%。實際條款以券商公告為準。
    """

    fee_rate: float = 0.001425
    discount: float = 0.6
    min_fee: float = 20.0
    tax_rate: float = 0.003
    daytrade_tax_rate: float = 0.0015

    def fee(self, amount):
        """單邊手續費。不足最低收費時以最低收費計。"""
        return max(amount * self.fee_rate * self.discount, self.min_fee)

    def tax(self, amount, daytrade=False):
        """證券交易稅。僅賣出時課徵。"""
        rate = self.daytrade_tax_rate if daytrade else self.tax_rate
        return amount * rate

    @property
    def effective_fee_rate(self):
        """折扣後的手續費率（不含最低收費）。"""
        return self.fee_rate * self.discount


@dataclass
class Trade:
    """一筆現股買賣。

    buy / sell 為每股成交價，shares 為股數。整數股與零股適用相同規則，
    差別僅在交易時段與當沖資格。
    """

    buy: float
    sell: float
    shares: int
    schedule: FeeSchedule = field(default_factory=FeeSchedule)
    daytrade: bool = False

    def __post_init__(self):
        if self.shares <= 0:
            raise ValueError('shares must be positive')
        if self.daytrade and self.shares < 1:
            raise ValueError('daytrade requires shares')

    @property
    def buy_amount(self):
        return self.buy * self.shares

    @property
    def sell_amount(self):
        return self.sell * self.shares

    @property
    def buy_fee(self):
        return self.schedule.fee(self.buy_amount)

    @property
    def sell_fee(self):
        return self.schedule.fee(self.sell_amount)

    @property
    def tax(self):
        return self.schedule.tax(self.sell_amount, self.daytrade)

    @property
    def total_cost(self):
        return self.buy_fee + self.sell_fee + self.tax

    def cost_breakdown(self):
        return {
            'buy_fee': round(self.buy_fee, 2),
            'sell_fee': round(self.sell_fee, 2),
            'tax': round(self.tax, 2),
            'total': round(self.total_cost, 2),
        }

    def cost_ratio(self):
        """總成本佔買入金額的比例。"""
        return self.total_cost / self.buy_amount

    def net_pnl(self):
        """扣除所有成本後的淨損益。"""
        return (self.sell_amount - self.sell_fee - self.tax) - (self.buy_amount + self.buy_fee)

    def _net_at(self, sell_price):
        """給定賣出價時的淨損益，供 break_even 求根。"""
        sell_amount = sell_price * self.shares
        sell_fee = self.schedule.fee(sell_amount)
        tax = self.schedule.tax(sell_amount, self.daytrade)
        return (sell_amount - sell_fee - tax) - (self.buy_amount + self.buy_fee)

    def break_even(self):
        """打平所需的漲幅。

        成本函式在最低收費處不連續，閉式解需分情況討論，容易寫錯；
        直接對淨損益做二分，200 次迭代足以收斂到浮點精度。
        """
        lo, hi = self.buy, self.buy * 3
        if self._net_at(lo) >= 0:
            return 0.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if self._net_at(mid) < 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2 / self.buy - 1

    def summary(self):
        return {
            'buy_amount': round(self.buy_amount, 2),
            'sell_amount': round(self.sell_amount, 2),
            'cost': self.cost_breakdown(),
            'cost_ratio': round(self.cost_ratio(), 4),
            'net_pnl': round(self.net_pnl(), 2),
            'break_even': round(self.break_even(), 4),
        }


@dataclass
class DayTrade(Trade):
    """當日沖銷。證券交易稅減半。"""

    daytrade: bool = True
