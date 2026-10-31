# twcost

台灣證券交易成本的 Python 實作。手續費折扣、券商最低收費、證券交易稅、當日沖銷稅、零股。

## 計算一筆交易的損益

```python
>>> from twcost import Trade
>>> t = Trade(buy=112.05, sell=104.95, shares=8)
>>> round(t.net_pnl(), 2)
-99.32
>>> t.cost_breakdown()
{'buy_fee': 20.0, 'sell_fee': 20.0, 'tax': 2.52, 'total': 42.52}
>>> round(t.cost_ratio(), 4)
0.0474
>>> round(t.break_even(), 4)
0.0478
```

`break_even()` 是打平所需漲幅 —— 這筆交易的股價漲 4.78% 才剛好不賠。

## 核心元件

- `FeeSchedule` — 券商費率方案：公定費率、電子單折扣、單筆最低收費、證交稅、當沖稅率
- `Trade` — 現股買賣。分別計算買入手續費、賣出手續費、賣出證交稅
- `DayTrade` — 當日沖銷，證交稅減半

預設取台灣常見條款：公定費率 0.1425%、電子單 6 折、單筆最低 20 元、證交稅 0.3%、當沖 0.15%。

```python
>>> from twcost import FeeSchedule, Trade
>>> s = FeeSchedule(discount=0.28, min_fee=1)     # 自訂券商條款
>>> t = Trade(buy=112.05, sell=104.95, shares=8, schedule=s)
>>> round(t.cost_ratio(), 4)
0.005
```

## 最低收費的影響

回測通常按 0.1425% 或 6 折後的 0.0855% 計算手續費，不計券商的單筆最低收費。
單筆金額低於門檻時，最低收費決定成本：

| 單筆金額 | 最低收費 20 元 | 最低收費 1 元 |
|---|---|---|
| 1,000 | 4.30% | 0.50% |
| 10,000 | 0.70% | 0.47% |
| 100,000 | 0.47% | 0.47% |

表格按買賣同價、手續費率 0.0855%、證交稅 0.3% 計算，只反映成本，不含價差。

## 安裝

從原始碼：

```bash
git clone <repo>
cd twcost
pip install -e .
```

無第三方依賴，只用到標準庫。

## 介面

安裝後在任意目錄：

```bash
twcost-gui
```

未安裝時，在專案根目錄：

```bash
python -m twcost
```

五個輸入框（買入價、賣出價、股數、折扣、最低收費），下方即時顯示成本明細。
輸入無效時明細清空，不彈錯誤。介面與上面範例共用同一個 `Trade`。

## 測試

```bash
python -m unittest discover -s tests
```

README 裡出現的每個數字都在 `tests/test_cost.py` 中被固定，改程式碼而不同步改 README 會讓測試失敗。

## 規則依據

- 手續費：證券商公會公定費率 0.1425%，電子下單折扣由各券商訂定
- 證券交易稅：賣出時課徵 0.3%，當日沖銷減半為 0.15%
- 零股與整股適用相同費率，差別在交易時段與當沖資格

實際條款以券商公告與財政部現行規定為準，本套件只做計算，不提供服務商資訊。

## License

MIT
