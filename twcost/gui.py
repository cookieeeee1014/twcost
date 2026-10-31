"""twcost 的極簡介面。

啟動：python -m twcost
"""

import tkinter as tk

from .cost import FeeSchedule, Trade

BG = 'white'
FG = 'black'
FONT = ('TkFixedFont', 10)

INPUTS = [
    ('buy', '買入價', '112.05'),
    ('sell', '賣出價', '104.95'),
    ('shares', '股數', '8'),
    ('discount', '折扣', '0.6'),
    ('min_fee', '最低收費', '20'),
]

OUTPUTS = ['買入金額', '買入手續費', '賣出手續費', '證交稅',
           '總成本', '成本比', '淨損益', '打平需漲']


class App:
    def __init__(self, root):
        self.root = root
        root.title('twcost')
        root.configure(bg=BG)
        root.resizable(False, False)

        self.inputs = {}
        for row, (key, label, default) in enumerate(INPUTS):
            self._label(root, label, row, 0, 'w')
            var = tk.StringVar(value=default)
            entry = tk.Entry(root, textvariable=var, font=FONT, width=14,
                             bg=BG, fg=FG, relief='solid', bd=1,
                             insertbackground=FG)
            entry.grid(row=row, column=1, sticky='w', padx=(0, 14), pady=3)
            var.trace_add('write', lambda *_: self.refresh())
            self.inputs[key] = var

        sep_row = len(INPUTS)
        tk.Frame(root, height=1, bg=FG).grid(
            row=sep_row, column=0, columnspan=2, sticky='ew', padx=14, pady=(8, 6))

        self.outputs = {}
        for i, name in enumerate(OUTPUTS):
            row = sep_row + 1 + i
            self._label(root, name, row, 0, 'w')
            var = tk.StringVar(value='-')
            tk.Label(root, textvariable=var, font=FONT, width=14, anchor='e',
                     bg=BG, fg=FG).grid(row=row, column=1, sticky='e',
                                        padx=(0, 14), pady=1)
            self.outputs[name] = var

        self.refresh()

    @staticmethod
    def _label(parent, text, row, column, sticky):
        tk.Label(parent, text=text, font=FONT, anchor='w', width=11,
                 bg=BG, fg=FG).grid(row=row, column=column, sticky=sticky,
                                    padx=(14, 4), pady=3)

    def read_inputs(self):
        """把輸入框讀成數值。任何一項無效就回傳 None。"""
        try:
            buy = float(self.inputs['buy'].get())
            sell = float(self.inputs['sell'].get())
            shares = int(float(self.inputs['shares'].get()))
            discount = float(self.inputs['discount'].get())
            min_fee = float(self.inputs['min_fee'].get())
        except ValueError:
            return None
        if shares <= 0 or buy <= 0 or sell < 0 or discount < 0 or min_fee < 0:
            return None
        return buy, sell, shares, discount, min_fee

    def compute(self):
        """當前的 Trade 物件，輸入無效時為 None。"""
        values = self.read_inputs()
        if values is None:
            return None
        buy, sell, shares, discount, min_fee = values
        schedule = FeeSchedule(discount=discount, min_fee=min_fee)
        return Trade(buy=buy, sell=sell, shares=shares, schedule=schedule)

    def refresh(self):
        trade = self.compute()
        if trade is None:
            for var in self.outputs.values():
                var.set('-')
            return
        cost = trade.cost_breakdown()
        self.outputs['買入金額'].set('{:,.2f}'.format(trade.buy_amount))
        self.outputs['買入手續費'].set('{:,.2f}'.format(cost['buy_fee']))
        self.outputs['賣出手續費'].set('{:,.2f}'.format(cost['sell_fee']))
        self.outputs['證交稅'].set('{:,.2f}'.format(cost['tax']))
        self.outputs['總成本'].set('{:,.2f}'.format(cost['total']))
        self.outputs['成本比'].set('{:.2f}%'.format(trade.cost_ratio() * 100))
        self.outputs['淨損益'].set('{:,.2f}'.format(trade.net_pnl()))
        self.outputs['打平需漲'].set('{:.2f}%'.format(trade.break_even() * 100))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
