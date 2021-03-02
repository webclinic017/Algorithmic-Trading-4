import tkinter as tk
import tkinter.ttk as ttk

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import mplfinance as fplt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from Components.Account import Account
from Models.Snapshot import Snapshot
from Services.MyLogger import MyLogger
from Services.SimTracker import SimTracker

plt.rcParams.update({'figure.max_open_warning': 0})

from Services.TradingClock import TradingClock

plt.ioff()
matplotlib.use("TkAgg")

import numpy as np
from Services.Datafactory import DataFactory
import datetime


import matplotlib.units as munits
converter = mdates.ConciseDateConverter()
munits.registry[np.datetime64] = converter
munits.registry[datetime.date] = converter
munits.registry[datetime.datetime] = converter


class PortfolioView(tk.Frame):
    def __init__(self, parent, simtracker, account, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.simtracker = simtracker
        self.account = account
        self.logger = MyLogger.getLogger("PView")

        tk.Button(self, text="Refresh", command=self.refresh, relief=tk.GROOVE, borderwidth=1) \
            .pack(side=tk.BOTTOM, expand=True, fill=tk.X)

        tk.Label(self, text="Orders").pack()
        self.orders_entry = tk.Entry(self)
        self.orders_entry.pack()
        self.orders_entry.bind('<Return>', self.refresh)

        self.orderstv_frame = tk.Frame(self)
        self.orderstv = ttk.Treeview(self.orderstv_frame)
        self.orderstv["columns"] = ["id", "Symbol", "Action", "Time", "Price", "Filled"]
        self.orderstv["show"] = "headings"
        self.orderstv.heading("id", text="")
        self.orderstv.heading("Symbol", text="Symb")
        self.orderstv.heading("Action", text="Action")
        self.orderstv.heading("Time", text="Time")
        self.orderstv.heading("Price", text="Price")
        self.orderstv.heading("Filled", text="Filled")
        col_width = self.orderstv.winfo_width() // len(self.orderstv['columns'])
        for col in self.orderstv['columns']:
            self.orderstv.heading(col, anchor=tk.CENTER)
            self.orderstv.column(col, anchor=tk.CENTER, width=col_width)  # set column width
        self.orderstv.pack(fill=tk.BOTH, expand=True)
        self.orderstv_frame.pack(fill=tk.BOTH, expand=True)

        # treeScroll = ttk.Scrollbar(self.orderstv)
        # treeScroll.configure(command=self.orderstv.yview)
        # self.orderstv.configure(yscrollcommand=treeScroll.set)

        tk.Label(self, text="Portfolio").pack()

        self.holdingstv_frame = tk.Frame(self)
        self.holdingstv = ttk.Treeview(self.holdingstv_frame)
        self.holdingstv["columns"] = ["Symbol", "Vol", "Avg Price", "Price", "Change", "Realised"]
        self.holdingstv["show"] = "headings"
        self.holdingstv.heading("Symbol", text="Symb")
        self.holdingstv.heading("Vol", text="Vol")
        self.holdingstv.heading("Avg Price", text="Avg Price")
        self.holdingstv.heading("Price", text="Price")
        self.holdingstv.heading("Change", text="%")
        self.holdingstv.heading("Realised", text="Realised")
        col_width = self.holdingstv.winfo_width() // len(self.holdingstv['columns'])
        for col in self.holdingstv['columns']:
            self.holdingstv.heading(col, anchor=tk.CENTER)
            self.holdingstv.column(col, anchor=tk.CENTER, width=col_width)  # set column width
        self.holdingstv.pack(fill=tk.BOTH, expand=True)
        self.holdingstv_frame.pack(fill=tk.BOTH, expand=True)

        # ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, expand=1)

        tk.Label(self, text="Value").pack()

        self.plot_frame = tk.Frame(self, relief=tk.GROOVE, borderwidth=1)
        self.f = Figure(figsize=(5, 5), dpi=100)
        self.a = self.f.add_subplot(111)
        self.a.grid(True)
        self.a.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        self.a.xaxis.set_minor_formatter(mdates.DateFormatter("%m-%d"))
        self.a.plot([TradingClock.getInstance().sync_datetime], [self.account.value])
        # self.cash, = self.a.plot([TradingClock.getInstance().sync_datetime], [self.account.cash])
        # self.holdings, = self.a.plot([TradingClock.getInstance().sync_datetime], [self.account.holdings])

        self.canvas = FigureCanvasTkAgg(self.f, self.plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

    def refresh(self, view=0):
        self.orderstv.delete(*self.orderstv.get_children())
        for i, order in enumerate(list(self.account.orderLedger.values())):  # [:view+1]
            symbol = order["contract"].symbol
            if self.orders_entry.get() != "":
                if symbol != self.orders_entry.get().upper():
                    continue

            self.orderstv.insert("", tk.END, i, values=(
                f"{i + 1}", symbol, order["order"].action, order['time'].strftime('%d/%m %H:%M'),
                round(order["avgFillPrice"], 3), order["filled"]))

        self.holdingstv.delete(*self.holdingstv.get_children())
        holdings = []
        for symbol in self.account.portfolio.keys():  # [:view+1]
            try:
                vol, avgprice = self.account.getPosition(symbol)
                price = DataFactory.getInstance().getLatestPrice(symbol)
                percent = 100 * (price - avgprice) / avgprice
                realised = round(self.account.getRealised(symbol), 2)

                holdings.append(
                    (symbol, vol, round(avgprice, 3), round(price, 3), round(percent, 3), round(realised, 3)))
            except Exception as e:
                #self.logger.warn(f"Failed to update portfolio side view {e}")
                pass

        for i, (symbol, vol, avgprice, price, percent, realised) in enumerate(
                sorted(holdings, key=lambda item: (item[-1], item[-2]))):
            self.holdingstv.insert("", tk.END, i, values=(
                symbol, vol, avgprice, price, f"{'+' if percent > 0 else ''}{percent}", realised))

        self.f.clf()
        times = self.account.VALUE.index
        values = self.account.VALUE.values
        self.a = self.f.add_subplot(111)
        self.a.grid(True)
        #self.a.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        #self.a.xaxis.set_minor_formatter(mdates.DateFormatter("%m-%d"))
        self.a.plot(self.account.VALUE)
        # self.value.set_data(times, values)

        try:
            #https://matplotlib.org/stable/gallery/text_labels_and_annotations/date_index_formatter.html
            self.a.set_xlim(times[0], times[-1])
            self.a.set_ylim(min(values) * 0.99, max(values) * 1.01)
            #self.f.autofmt_xdate()
            self.canvas.draw()
        except Exception as e:
            self.logger.warn(f"Failed to update sideview {e}")


class StrategyView(tk.Frame):
    def __init__(self, parent, simtracker, account, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.logger = MyLogger.getLogger('StratView')

        self.simtracker = simtracker
        self.account = account
        self.canvas = None
        self.legend = tk.Frame(self)
        self.legend.pack(side=tk.RIGHT)
        # self.update()

    @staticmethod
    def snapshot_to_fig(snapshot, account=None, savefile=None):
        logger = MyLogger.getLogger('SS2Fig')
        legend_indicators = {}
        data = snapshot.data

        def getcolor(ii):
            colors = ["blue", "green", "red", "cyan", "magenta", "yellow"]
            return colors[ii % len(colors)]

        def get_addplot(ii, key, indicator, iargs):
            if "color" not in iargs:
                iargs["color"] = getcolor(ii)

            legend_indicators[key] = iargs["color"]
            if len(indicator) < len(data):
                missing_points = len(data) - len(indicator)
                indicator = pd.concat([indicator, pd.Series([np.nan] * missing_points)])
                logger.warn(f"Missing {missing_points} data points for indicator {key}")


            return fplt.make_addplot(indicator,**iargs)

        indicator_adps = [get_addplot(i, key, indicator, iargs) for i, (key, (indicator, iargs)) in enumerate(snapshot.indicators.items())]

        trade_adps = []
        symbol = snapshot.contract.symbol
        period = min([abs(d1 - d2) for d1, d2 in zip(data.index[1:], data.index[:-1])])

        if account is not None:
            # GET THE BUYS
            try:
                buy_times, buy_prices = map(list, zip(*[
                    (order["time"], order["lastFillPrice"]) for id, order in account.orderLedger.items() if
                    order["contract"].symbol == symbol and
                    data.index[0] <= order["time"] <= data.index[-1] and
                    order["order"].action == "BUY"]))

                if len(buy_times):
                    if period > datetime.timedelta(minutes=5):
                        buy_times = [bt.date() for bt in buy_times]
                        buys = pd.Series([buy_prices[buy_times.index(t)] if t.date() in buy_times else np.nan for t in data.index])
                    else:
                        buys = pd.Series([buy_prices[buy_times.index(t)] if t in buy_times else np.nan for t in data.index])

                    if np.any(~np.isnan(buys)):
                        trade_adps.append(
                            fplt.make_addplot(buys.transform(lambda x: x * 0.9975), scatter=True,
                                                marker=r'$\uparrow$', markersize=96, color="green"))
            except ValueError as e:
                pass
            except Exception as e:
                logger.warn(f"Failed buy markers: {e}")

            # GET THE SELLS
            try:
                sell_times, sell_prices = map(list, zip(*[
                    (order["time"], order["lastFillPrice"]) for id, order in account.orderLedger.items() if
                    order["contract"].symbol == symbol and
                    data.index[0] <= order["time"] <= data.index[-1] and
                    order["order"].action == "SELL"]))

                if len(sell_times):
                    if period > datetime.timedelta(minutes=5):
                        sell_times = [st.date() for st in sell_times]
                        sells = pd.Series([sell_prices[sell_times.index(t)] if t.date() in sell_times else np.nan for t in data.index])
                    else:
                        sells = pd.Series([sell_prices[sell_times.index(t)] if t in sell_times else np.nan for t in data.index])

                    if np.any(~np.isnan(sells)):
                        trade_adps.append(
                            fplt.make_addplot(sells.transform(lambda x: x * 1.0025), scatter=True,
                                                marker=r'$\downarrow$', markersize=96, color="red"))
            except ValueError as e:
                pass
            except Exception as e:
                logger.warn(f"Failed sell markers: {e}")

        mc = fplt.make_marketcolors(up='#7DFFB8', down='#FF7979', edge='black', wick='black', volume='in')
        s = fplt.make_mpf_style(base_mpl_style="seaborn", mavcolors=["lightseagreen", "orange"],
                                facecolor="#F9FBFD", gridcolor="#F2F2F2", gridstyle="--", marketcolors=mc)

        dates = list(set(pd.Series(data.index).transform(lambda x: x.date())))

        plotargs = {
            "type" : 'candle',
            "style" : s,
            "title" : symbol,
            "ylabel" :  'Price ($)',
            "volume" : True,
            "addplot" : indicator_adps + trade_adps,
            "returnfig" : True
        }

        if savefile is not None:
            # if period == datetime.timedelta(days=1):
            #     data.index = pd.DatetimeIndex(pd.Series(data.index).transform(lambda x:x.date()), dtype=datetime.date)
            plotargs["savefig"] = savefile

        if type(data.index) != pd.DatetimeIndex:
            # TODO: shouldn't come here
            data.index = pd.DatetimeIndex(pd.to_datetime(data.index, utc=True))
            logger.warn("ERROR index not datetime")

        for addplots in [indicator_adps + trade_adps, indicator_adps, trade_adps, []]:
            try:
                plotargs["addplot"] = addplots
                fig, ax = fplt.plot(data,  **plotargs)
                break
            except:
                pass#fig, ax = fplt.plot(data, **plotargs)

        if period <= datetime.timedelta(minutes=5):
            loc = mticker.MultipleLocator(73)
            ax[0].xaxis.set_major_locator(loc)
        else:
            loc = mticker.MultipleLocator(1)
            #loc = mticker.MultipleLocator(max(len(data)//20, 1))
            ax[0].xaxis.set_major_locator(loc)



        return fig, ax, legend_indicators



    def _get_fig(self, snapshot):
        # TODO: shoved in

        fig, ax, legend_indicators = StrategyView.snapshot_to_fig(snapshot, account=self.account)

        for child in self.legend.winfo_children():
            child.destroy()

        for key, color in legend_indicators.items():
            tk.Label(self.legend, text=key, fg=color).pack()

        return fig, ax

    def refresh(self, view):
        try:
            fig, ax = self._get_fig(self.simtracker.snapshots[view])
            canvas = FigureCanvasTkAgg(fig, self)
            toolbar = NavigationToolbar2Tk(canvas, self)
            toolbar.update()



            if self.canvas is not None:
                self.canvas.get_tk_widget().destroy()
                self.toolbar.destroy()

            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            self.canvas = canvas
            self.toolbar = toolbar

        except Exception as e:
            self.logger.exception(e)


class MainApplication(tk.Frame):
    @property
    def view(self):
        return self.__view

    @view.setter
    def view(self, vview):
        self.__view = min(max(0, vview), len(self.simtracker.snapshots) - 1)
        self.update_viewer_label()
        self.toggle_view()

    def __init__(self, parent, simtracker, account, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.simtracker = simtracker

        # Guts
        self.content_frame = tk.Frame(self)
        self.main = StrategyView(self.content_frame, simtracker, account, borderwidth=2, relief="groove")
        self.side = PortfolioView(self.content_frame, simtracker, account, borderwidth=2, relief="groove")
        self.main.grid(row=0, column=0, sticky="nsew")  # .pack(side="left", fill="both", expand=True)
        self.side.grid(row=0, column=1, sticky="nsew")

        self.content_frame.grid_columnconfigure(0, weight=2, uniform="group1")
        self.content_frame.grid_columnconfigure(1, weight=1, uniform="group1")
        self.content_frame.grid_rowconfigure(0, weight=1)

        # prev 0/1 next
        self.viewer_frame = tk.Frame(self)
        self.prev_button = tk.Button(self.viewer_frame, text="PREV", command=lambda: self._next_view("PREV"))
        self.prev_button.pack(side=tk.LEFT)
        self.viewer_entry = tk.Entry(self.viewer_frame, width=3, text='0')
        self.viewer_entry.bind('<Return>', self._set_view)
        self.viewer_entry.pack(side=tk.LEFT)
        self.viewer_label = tk.Label(self.viewer_frame, text="/0")
        self.viewer_label.pack(side=tk.LEFT)
        self.next_button = tk.Button(self.viewer_frame, text="NEXT", command=lambda: self._next_view("NEXT"))
        self.next_button.pack(side=tk.LEFT)
        self.view = -1

        self.viewer_frame.pack()
        self.content_frame.pack(fill="both", expand=True)

        self.simtracker.add_listener(self)

    def notify(self):
        self.update_viewer_label()
        self.toggle_view()
        # self.main.notify()
        # self.side.notify()

    def update_viewer_label(self):
        if not self.focus_get() == self.viewer_entry:
            self.viewer_entry.delete(0, tk.END)
            self.viewer_entry.insert(0, f"{self.view + 1}")
        self.viewer_label["text"] = f"/{len(self.simtracker.snapshots)}"

    def _next_view(self, side):
        self.view += 1 if side == "NEXT" else -1
        self.main.refresh(self.view)
        self.side.refresh(self.view)

    def _set_view(self, sender):
        self.view = eval(self.viewer_entry.get()) - 1
        self.main.refresh(self.view)
        self.side.refresh(self.view)

    def toggle_view(self):
        try:
            if self.view > 0:
                self.prev_button["state"] = tk.NORMAL
            else:
                self.prev_button["state"] = tk.DISABLED

            if self.view < len(self.simtracker.snapshots) - 1:
                self.next_button["state"] = tk.NORMAL
            else:
                self.next_button["state"] = tk.DISABLED
        except Exception as e:
            pass


class SimViewer(tk.Tk):
    def __init__(self, simtracker, account, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()

        self.geometry(f'{int(width * 0.9)}x{int(height * 0.9)}')
        self.resizable(0, 0)  # Don't allow resizing in the x or y direction

        mainapp = MainApplication(self, simtracker, account)
        mainapp.pack(side="top", fill="both", expand=True)

        self.mainloop()


if __name__ == "__main__":
    import talib
    from ibapi.contract import Contract
    from ibapi.order import Order

    datafactory = DataFactory.getInstance()

    d = SimTracker()

    name = "SA"
    data = datafactory.loadSymbol("VAS")
    indicators = {"WMA": talib.WMA(data["Close"], timeperiod=72 * 2)}
    contract = Contract()
    order = Order()

    snapshot = Snapshot(name, data, indicators, contract, order)
    d.add_shapshot(snapshot)

    name = "SA"
    data = datafactory.loadSymbol("NDQ")
    indicators = {"SMA": talib.SMA(data["Close"], timeperiod=72 * 2)}
    contract = Contract()
    order = Order()

    snapshot = Snapshot(name, data, indicators, contract, order)
    d.add_shapshot(snapshot)

    a = Account(1000)
    st = SimTracker()

    root = tk.Tk()
    mainapp = MainApplication(root, d, a)
    mainapp.pack(side="top", fill="both", expand=True)
    root.mainloop()
