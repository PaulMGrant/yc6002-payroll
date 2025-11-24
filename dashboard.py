"""
Tkinter Dashboard
-----------------
A well-designed, single-file Tkinter dashboard demonstrating:
 - System monitoring (CPU, memory, disk) using `psutil`
 - Weather info from OpenWeatherMap (requires API key)
 - Stock price chart from Alpha Vantage (requires API key)
 - Live small charts embedded using matplotlib
 - Responsive layout using ttk and ttk styling
 - Background data updates using threading

How to use:
 1. Install dependencies:
    pip install psutil requests matplotlib pillow

 2. Obtain API keys (optional features):
    - OpenWeatherMap: https://openweathermap.org/api (paste your key into OPENWEATHER_API_KEY)
    - Alpha Vantage: https://www.alphavantage.co/ (paste your key into ALPHAV_API_KEY)

 3. Run:
    python tkinter_dashboard.py

Notes:
 - If you don't have API keys, the dashboard will still show system stats.
 - The code is written to be readable and modular so you can swap APIs or widgets easily.

"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import psutil
import requests
from io import BytesIO
from PIL import Image, ImageTk
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for safe rendering to canvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -------------
# Configuration
# -------------
OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"
ALPHAV_API_KEY = "YOUR_ALPHAVANTAGE_API_KEY"
DEFAULT_CITY = "London,UK"
DEFAULT_STOCK = "AAPL"
REFRESH_INTERVAL = 5  # seconds for system stats
API_REFRESH = 60  # seconds for external APIs

# -----------------------------
# Utility functions
# -----------------------------

def safe_request(url, params=None, timeout=8):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# -----------------------------
# Data fetchers
# -----------------------------

def get_system_stats():
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()
    return {
        'cpu_percent': cpu,
        'mem_total': mem.total,
        'mem_used': mem.used,
        'mem_percent': mem.percent,
        'disk_total': disk.total,
        'disk_used': disk.used,
        'disk_percent': disk.percent,
        'bytes_sent': net.bytes_sent,
        'bytes_recv': net.bytes_recv,
    }


def get_weather(city=DEFAULT_CITY, api_key=OPENWEATHER_API_KEY):
    if not api_key or api_key.startswith('YOUR_'):
        return {'error': 'No OpenWeather API key configured.'}
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'q': city, 'appid': api_key, 'units': 'metric'}
    return safe_request(url, params)


def get_stock_time_series(symbol=DEFAULT_STOCK, api_key=ALPHAV_API_KEY):
    if not api_key or api_key.startswith('YOUR_'):
        return {'error': 'No Alpha Vantage API key configured.'}
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '5min',
        'outputsize': 'compact',
        'apikey': api_key,
    }
    return safe_request(url, params)

# -----------------------------
# Widgets / UI components
# -----------------------------

class StatBar(ttk.Frame):
    """A horizontal stat bar that displays label, value, and a small progressbar."""
    def __init__(self, parent, title, unit='', maxvalue=100, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = ttk.Label(self, text=title, font=('Segoe UI', 10, 'bold'))
        self.value = ttk.Label(self, text='—', font=('Segoe UI', 12))
        self.pb = ttk.Progressbar(self, orient='horizontal', mode='determinate', maximum=maxvalue)
        self.unit = unit
        self.title.grid(row=0, column=0, sticky='w')
        self.value.grid(row=0, column=1, sticky='e')
        self.pb.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(4,0))
        self.columnconfigure(0, weight=1)

    def update_value(self, val):
        text = f"{val}{self.unit}" if self.unit else f"{val}"
        try:
            # format numeric percentages nicely
            if isinstance(val, float):
                text = f"{val:.1f}{self.unit}"
        except Exception:
            pass
        self.value.config(text=text)
        try:
            num = float(val)
            self.pb['value'] = num
        except Exception:
            pass


class SmallChart(ttk.Frame):
    """A small matplotlib chart embedded in a Tk widget."""
    def __init__(self, parent, title='Chart', width=4, height=2.5, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = ttk.Label(self, text=title, font=('Segoe UI', 10, 'bold'))
        self.title.pack(anchor='w')
        self.fig = Figure(figsize=(width, height), dpi=80)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.fig.tight_layout()

    def plot(self, xs, ys, label=None):
        self.ax.clear()
        self.ax.plot(xs, ys)
        if label:
            self.ax.set_title(label, fontsize=9)
        self.fig.tight_layout()
        # draw on the Tk canvas
        self.canvas.draw()

# -----------------------------
# Main application
# -----------------------------

class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('System + API Dashboard')
        self.geometry('1000x640')
        self.minsize(900, 560)
        self.configure(bg='#f7f9fc')
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        # Top header
        header = ttk.Frame(self, padding=12)
        header.pack(side='top', fill='x')
        title = ttk.Label(header, text='Dashboard', font=('Segoe UI', 18, 'bold'))
        title.pack(side='left')
        self.last_updated_lbl = ttk.Label(header, text='Last update: —', font=('Segoe UI', 9))
        self.last_updated_lbl.pack(side='right')

        # Main area: left sidebar + content
        main = ttk.Frame(self)
        main.pack(fill='both', expand=True, padx=12, pady=(0,12))
        main.columnconfigure(1, weight=1)

        # Sidebar
        sidebar = ttk.Frame(main, width=260)
        sidebar.grid(row=0, column=0, sticky='ns')
        sidebar.grid_propagate(False)

        # System stats card
        sys_card = ttk.LabelFrame(sidebar, text='System Stats', padding=10)
        sys_card.pack(fill='x', pady=(0,12))
        self.cpu_bar = StatBar(sys_card, 'CPU', unit='%')
        self.mem_bar = StatBar(sys_card, 'Memory', unit='%')
        self.disk_bar = StatBar(sys_card, 'Disk', unit='%')
        self.cpu_bar.pack(fill='x', pady=6)
        self.mem_bar.pack(fill='x', pady=6)
        self.disk_bar.pack(fill='x', pady=6)

        # Weather card
        weather_card = ttk.LabelFrame(sidebar, text='Weather', padding=10)
        weather_card.pack(fill='x', pady=(0,12))
        self.weather_icon_lbl = ttk.Label(weather_card)
        self.weather_icon_lbl.pack(side='left')
        self.weather_text = ttk.Label(weather_card, text='—', font=('Segoe UI', 10))
        self.weather_text.pack(side='left', padx=8)
        self.weather_city_entry = ttk.Entry(weather_card)
        self.weather_city_entry.insert(0, DEFAULT_CITY)
        self.weather_city_entry.pack(fill='x', pady=(8,0))
        self.weather_refresh_btn = ttk.Button(weather_card, text='Refresh Weather', command=self.fetch_weather_now)
        self.weather_refresh_btn.pack(pady=(6,0))

        # Quick controls
        control_card = ttk.LabelFrame(sidebar, text='Controls', padding=10)
        control_card.pack(fill='x')
        ttk.Label(control_card, text='Stock symbol').pack(anchor='w')
        self.stock_entry = ttk.Entry(control_card)
        self.stock_entry.insert(0, DEFAULT_STOCK)
        self.stock_entry.pack(fill='x', pady=(4,6))
        self.stock_refresh_btn = ttk.Button(control_card, text='Refresh Stock', command=self.fetch_stock_now)
        self.stock_refresh_btn.pack(fill='x')

        # Main content area
        content = ttk.Frame(main)
        content.grid(row=0, column=1, sticky='nsew', padx=(12,0))
        content.rowconfigure(1, weight=1)
        content.columnconfigure(0, weight=1)

        # Top row: small charts
        charts_frame = ttk.Frame(content)
        charts_frame.grid(row=0, column=0, sticky='ew')
        charts_frame.columnconfigure((0,1,2), weight=1)

        self.cpu_chart = SmallChart(charts_frame, title='CPU (last N)', width=3, height=1.6)
        self.mem_chart = SmallChart(charts_frame, title='Memory (last N)', width=3, height=1.6)
        self.net_chart = SmallChart(charts_frame, title='Network Tx (last N)', width=3, height=1.6)

        self.cpu_chart.grid(row=0, column=0, sticky='nsew', padx=6)
        self.mem_chart.grid(row=0, column=1, sticky='nsew', padx=6)
        self.net_chart.grid(row=0, column=2, sticky='nsew', padx=6)

        # Middle row: stock chart + details panel
        mid_frame = ttk.Frame(content)
        mid_frame.grid(row=1, column=0, sticky='nsew', pady=10)
        mid_frame.columnconfigure(0, weight=1)
        mid_frame.columnconfigure(1, weight=0)

        self.stock_big_chart = SmallChart(mid_frame, title='Stock (5-min)', width=7, height=3.2)
        self.stock_big_chart.grid(row=0, column=0, sticky='nsew', padx=(0,10))

        details_card = ttk.LabelFrame(mid_frame, text='Details', padding=10, width=240)
        details_card.grid(row=0, column=1, sticky='ns')
        details_card.grid_propagate(False)
        self.details_text = tk.Text(details_card, height=14, wrap='word')
        self.details_text.pack(fill='both', expand=True)

        # Bottom row: log area
        log_card = ttk.LabelFrame(content, text='Activity Log', padding=6)
        log_card.grid(row=2, column=0, sticky='ew')
        self.log_list = tk.Listbox(log_card, height=6)
        self.log_list.pack(fill='both', expand=True)

        # Internal state
        self.cpu_history = []
        self.mem_history = []
        self.net_history = []
        self.max_history = 36

        # Start background refresh threads
        self._stop = False
        self._start_background_tasks()

        # Graceful close
        self.protocol('WM_DELETE_WINDOW', self._on_close)

    # -----------------------------
    # Background tasks
    # -----------------------------

    def _start_background_tasks(self):
        t1 = threading.Thread(target=self._system_updater, daemon=True)
        t1.start()
        t2 = threading.Thread(target=self._api_updater, daemon=True)
        t2.start()

    def _system_updater(self):
        while not self._stop:
            try:
                data = get_system_stats()
                self.after(0, lambda d=data: self._update_system_ui(d))
            except Exception as e:
                self._log(f'System update failed: {e}')
            time.sleep(REFRESH_INTERVAL)

    def _api_updater(self):
        # Run once at startup
        self.fetch_weather_now()
        self.fetch_stock_now()
        while not self._stop:
            try:
                self.fetch_weather_now()
                self.fetch_stock_now()
            except Exception as e:
                self._log(f'API update failed: {e}')
            time.sleep(API_REFRESH)

    # -----------------------------
    # UI update handlers
    # -----------------------------

    def _update_system_ui(self, data):
        cpu = data.get('cpu_percent', 0)
        mem = data.get('mem_percent', 0)
        disk = data.get('disk_percent', 0)
        self.cpu_bar.update_value(cpu)
        self.mem_bar.update_value(mem)
        self.disk_bar.update_value(disk)

        # update histories
        self._push_history(self.cpu_history, cpu)
        self._push_history(self.mem_history, mem)
        self._push_history(self.net_history, data.get('bytes_sent', 0) / 1024.0)

        # plot small charts
        xs = list(range(-len(self.cpu_history)+1, 1))
        self.cpu_chart.plot(xs, self.cpu_history, label='CPU %')
        self.mem_chart.plot(xs, self.mem_history, label='Mem %')
        self.net_chart.plot(xs, self.net_history, label='KB sent')

        now = time.strftime('%Y-%m-%d %H:%M:%S')
        self.last_updated_lbl.config(text=f'Last update: {now}')

    def _push_history(self, arr, value):
        arr.append(value)
        if len(arr) > self.max_history:
            arr.pop(0)

    def _on_close(self):
        if messagebox.askokcancel('Quit', 'Are you sure you want to quit?'):
            self._stop = True
            self.destroy()

    # -----------------------------
    # API fetch actions
    # -----------------------------

    def fetch_weather_now(self):
        city = self.weather_city_entry.get().strip() or DEFAULT_CITY
        def job():
            res = get_weather(city)
            self.after(0, lambda r=res, c=city: self._handle_weather_response(r, c))
        threading.Thread(target=job, daemon=True).start()

    def _handle_weather_response(self, res, city):
        if 'error' in res:
            self.weather_text.config(text=f'Error: {res.get("error")}')
            self._log(f'Weather error: {res.get("error")}')
            return
        try:
            desc = res['weather'][0]['description'].capitalize()
            temp = res['main']['temp']
            icon_code = res['weather'][0].get('icon')
            text = f"{city}: {desc}, {temp:.1f} °C"
            self.weather_text.config(text=text)
            if icon_code:
                self._set_weather_icon(icon_code)
            self._log(f'Weather updated: {text}')
        except Exception as e:
            self.weather_text.config(text='Weather parse error')
            self._log(f'Weather parse failed: {e}')

    def _set_weather_icon(self, code):
        try:
            url = f'http://openweathermap.org/img/wn/{code}@2x.png'
            r = requests.get(url, timeout=6)
            r.raise_for_status()
            img = Image.open(BytesIO(r.content)).resize((64,64), Image.LANCZOS)
            self._weather_icon = ImageTk.PhotoImage(img)
            self.weather_icon_lbl.config(image=self._weather_icon)
        except Exception as e:
            self._log(f'Icon load failed: {e}')

    def fetch_stock_now(self):
        symbol = self.stock_entry.get().strip().upper() or DEFAULT_STOCK
        def job():
            res = get_stock_time_series(symbol)
            self.after(0, lambda r=res, s=symbol: self._handle_stock_response(r, s))
        threading.Thread(target=job, daemon=True).start()

    def _handle_stock_response(self, res, symbol):
        if 'error' in res:
            self._log(f'Stock error: {res.get("error")}')
            self.details_text.delete('1.0', 'end')
            self.details_text.insert('end', f'Error: {res.get("error")}\n')
            return
        # Alpha Vantage returns either an error message or a dict with a key like 'Time Series (5min)'
        try:
            ts_key = None
            for k in res.keys():
                if 'Time Series' in k:
                    ts_key = k
                    break
            if not ts_key:
                # Try detect note or error
                if 'Note' in res:
                    self._log('AlphaVantage note: rate limit or similar')
                    self.details_text.delete('1.0', 'end')
                    self.details_text.insert('end', res.get('Note','No timeseries found.'))
                    return
                self._log('No timeseries data found for stock')
                self.details_text.delete('1.0', 'end')
                self.details_text.insert('end', 'No timeseries data found.')
                return

            timeseries = res[ts_key]
            # timeseries is a dict keyed by timestamp
            items = sorted(timeseries.items())
            xs = [i for i,_ in enumerate(items[-50:])]
            ys = [float(v['4. close']) for _,v in items[-50:]]
            self.stock_big_chart.plot(xs, ys, label=f'{symbol} price')
            last_ts, last_vals = items[-1]
            details = f"Symbol: {symbol}\nLast: {last_vals['4. close']}\nHigh: {last_vals['2. high']}\nLow: {last_vals['3. low']}\nVolume: {last_vals['5. volume']}\nTimestamp: {last_ts}\n"
            self.details_text.delete('1.0', 'end')
            self.details_text.insert('end', details)
            self._log(f'Stock updated: {symbol} {last_vals["4. close"]}')
        except Exception as e:
            self._log(f'Stock parse failed: {e}')
            self.details_text.delete('1.0', 'end')
            self.details_text.insert('end', f'Parse error: {e}')

    # -----------------------------
    # Logging
    # -----------------------------

    def _log(self, message):
        ts = time.strftime('%H:%M:%S')
        try:
            self.log_list.insert(0, f'[{ts}] {message}')
            # limit rows
            if self.log_list.size() > 200:
                self.log_list.delete(200, 'end')
        except Exception:
            pass


if __name__ == '__main__':
    app = DashboardApp()
    app.mainloop()
