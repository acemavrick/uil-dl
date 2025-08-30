import sys
import portalocker
import json
import setup.mylogging
import threading
from pathlib import Path
from time import sleep
import os
import webapp.analytics
import webapp.splash
from config import data_path
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import webbrowser
import subprocess

# tkinter root reference
root = None

# app metadata and runtime state
APP_VERSION = "1.0.0-beta-2"
app_start_time = time.time()
current_url = ""
current_port = None

# ui theme colors
UI_BG = '#0D1117'           # github dark bg
UI_SURFACE = '#161B22'      # elevated surface
UI_PANEL = '#21262D'        # panel background
UI_TEXT = '#F0F6FC'         # primary text
UI_MUTED = '#8B949E'        # secondary text
UI_ACCENT = '#238636'       # green accent
UI_ACCENT_HOVER = '#2EA043' # green hover
UI_SECONDARY = '#373E47'    # secondary button
UI_SECONDARY_HOVER = '#444C56' # secondary hover
UI_BORDER = '#30363D'       # border color
UI_SUCCESS = '#238636'      # success green
UI_ERROR = '#DA3633'        # error red

# ui logging buffer and target widget (set later)
ui_log_buffer = []
details_text = None

def log(msg: str):
    """print to console and append to ui details if available."""
    try:
        print(msg)
    finally:
        ui_log_buffer.append(str(msg))
        if root and details_text is not None:
            def _append():
                try:
                    details_text.configure(state='normal')
                    details_text.insert('end', str(msg) + ("\n" if not str(msg).endswith("\n") else ""))
                    details_text.see('end')
                    details_text.configure(state='disabled')
                except Exception:
                    pass
            try:
                root.after(0, _append)
            except Exception:
                pass

# get user directory
downloads_dir_path = None

if not data_path.exists():
    log("xx user data directory does not exist. creating...")
    data_path.mkdir(parents=True, exist_ok=True)
    log("OK user data directory created")

log(f"Data path: {data_path.as_uri()}")
log("This is where the app stores logs, config, and other important files.")
log("Do not modify this directory unless you know what you are doing.\n")


# configure logging to file
setup.mylogging.setup_logging(data_path)

# verify config
def verify_config():
    global data_path, downloads_dir_path
    print()
    config_file = data_path / "config.cfg"
    downloads_dir = Path.home() / "Downloads" / "uildl-downloads"
    config_data = {
        "default_download_dir": downloads_dir.as_posix(),
        "download_dir": downloads_dir.as_posix(),
    }

    ## check if exists
    if not config_file.exists():
        print("xx config file does not exist. creating...")
        config_file.touch()
        with open(config_file, "w") as f:
            json.dump(config_data, f, sort_keys=True)
        print("OK config file created")
    else:
        opening_went_well = False
        with open(config_file, "r") as f:
            try:
                loaded_config = json.load(f)
                opening_went_well = True
            except json.JSONDecodeError:
                print("xx config file is not valid json. recreating config file...")
                config_file.touch()
                with open(config_file, "w") as f:
                    json.dump(config_data, f, sort_keys=True)
                print("OK config file created")

        ## verify everything is in place
        if opening_went_well:
            print("OK config file exists")

            changed_config = False

            for key, value in config_data.items():
                if not loaded_config.get(key):
                    print(f"xx {key} is not set. setting...")
                    loaded_config[key] = value
                    changed_config = True
                    print(f"OK {key} set")
                else:
                    print(f"OK {key} is in place")

            if changed_config:
                with open(config_file, "w") as f:
                    json.dump(loaded_config, f, sort_keys=True)
                print("OK config saved")
            else:
                print("OK config proper")

    with open(config_file, "r") as f:
        config_data = json.load(f)
    downloads_dir_path = Path(config_data["download_dir"])

updated_info = False

def verify_info_json():
    global data_path, updated_info
    import setup.manageInfo as manageInfo
    from setup.manageInfo import UpdateResult

    result, err_msg = manageInfo.update_info(data_path)
    print()
    if result == UpdateResult.UPDATED:
        print("OK info.json updated")
        updated_info = True
    elif result == UpdateResult.NOT_UPDATED:
        print("OK info.json not updated")
    elif result == UpdateResult.ERROR:
        print(f"xx Failed to update info.json. Check logs for details")
        setup.mylogging.LOGGER.error(f"When updating info.json: \n {err_msg}")
        # check if info.json exists... if it does, then attempt to load it (see if it's valid)
        if (data_path / "info.json").exists():
            try:
                with open(data_path / "info.json", "r") as f:
                    json.load(f)
                print("OK local info.json is valid")
                return
            except json.JSONDecodeError:
                print("xx info.json is not valid.")
        else:
            print("xx no local info.json found")
        
        print("-- No proper info.json found. The app will not work properly.")
        sys.exit(1)


def verify_info_db():
    global data_path, updated_info
    print()
    import setup.buildDB as buildDB
    # always build db (it is small enought to be fast)
    if True or updated_info or not (data_path / "info.db").exists():
        buildDB.create_database(data_path / "info.json", data_path / "info.db", interactive=False)
        print("OK info.db created")
    else:
        print("OK info.db exists")

def find_free_port(port_range=range(5000, 60000)):
    import socket
    for i in port_range:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", i))
            s.close()
            return i
        except OSError:
            continue
    return None

def start_flask_in_background(on_ready, on_error):
    """Initialize app, start Flask, then notify UI callbacks."""
    try:
        log("Starting initialization...")
        verify_config()
        verify_info_json()
        verify_info_db()
        log("Initialization complete.")

        flask_port = find_free_port()
        if flask_port is None:
            msg = "no free port found for the main application"
            log(f"xx {msg}")
            on_error(msg)
            return

        log(f"OK Flask port {flask_port} found")
        
        import webapp.app as myapp
        app_thread = threading.Thread(target=myapp.app.run, kwargs={"debug": False, "port": flask_port})
        app_thread.daemon = True
        app_thread.start()

        log(f"""
uil-dl 1.0.0-beta-2 is now running.
access it through your browser at: http://127.0.0.1:{flask_port}
downloads directory: {downloads_dir_path.as_uri()}
log file: {(data_path / "uil-dl.log").as_uri()}
                """)

        # wait for the app to start
        sleep(1.5)

        url = f"http://127.0.0.1:{flask_port}"
        on_ready(url)

    except Exception as e:
        log(f"xx An error occurred during initialization: {e}")
        on_error(str(e))


def shutdown():
    import sys
    log("\n\nShutting down. See you next time!")
    sys.exit(0)


if __name__ == "__main__":
    LOCKFILEPATH = data_path / ".uil-dl.lock"

    try:
        LOCK_FILE = LOCKFILEPATH.open("w")
        portalocker.lock(LOCK_FILE, portalocker.LOCK_EX | portalocker.LOCK_NB)
    except portalocker.LockException:
        print("xx another instance of uil-dl is running. exiting...")
        sys.exit(1)

    try:
        # i don't want analytics data
        # init analytics here to avoid side-effects at import time
        # webapp.analytics.init(data_path)

        # create tkinter UI
        root = tk.Tk()
        root.title('UIL-DL 1.0 Beta 2')
        root.configure(bg=UI_BG, highlightthickness=0)
        # set icon (best-effort)
        try:
            icon_path = (Path(__file__).resolve().parent / 'assets' / 'icon.png')
            if icon_path.exists():
                root.iconphoto(True, tk.PhotoImage(file=icon_path.as_posix()))
        except Exception:
            pass

        # ttk theme and styles
        style = ttk.Style(root)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TFrame', background=UI_BG)
        style.configure('Surface.TFrame', background=UI_SURFACE)
        style.configure('Panel.TFrame', background=UI_PANEL)
        style.configure('TLabel', background=UI_BG, foreground=UI_TEXT)
        style.configure('Subtle.TLabel', background=UI_BG, foreground=UI_MUTED)
        style.configure('Header.TLabel', background=UI_SURFACE, foreground=UI_TEXT,
                        font=('Helvetica', 22, 'bold'))
        style.configure('StatusBar.TLabel', background=UI_SURFACE, foreground=UI_MUTED,
                        padding=(16,6), font=('Helvetica', 9))
        style.configure('Card.TFrame', background=UI_SURFACE)
        style.configure('Url.TEntry', fieldbackground=UI_SURFACE, foreground=UI_TEXT,
                        background=UI_SURFACE, bordercolor=UI_BORDER, lightcolor=UI_BORDER, darkcolor=UI_BORDER)
        style.map('Url.TEntry', fieldbackground=[('readonly', UI_SURFACE)],
                  foreground=[('disabled', UI_MUTED)])
        style.configure('Primary.TButton', background=UI_ACCENT, foreground='white',
                        font=('Helvetica', 11, 'bold'), padding=(14,8))
        style.map('Primary.TButton', background=[('active', UI_ACCENT_HOVER), ('disabled', UI_SECONDARY)],
                   foreground=[('disabled', UI_MUTED)])
        style.configure('Secondary.TButton', background=UI_SECONDARY, foreground=UI_TEXT,
                        font=('Helvetica', 11, 'bold'), padding=(14,8))
        style.map('Secondary.TButton', background=[('active', UI_SECONDARY_HOVER), ('disabled', UI_PANEL)],
                   foreground=[('disabled', UI_MUTED)])
        root.columnconfigure(0, weight=0)
        root.rowconfigure(3, weight=0)

        # ui variables
        status_var = tk.StringVar(value='initializing...')
        url_var = tk.StringVar(value='')

        # layout - modern header with gradient-like effect
        header_container = tk.Frame(root, bg=UI_BG)
        header_container.grid(row=0, column=0, sticky='we', padx=0, pady=0)
        header_container.columnconfigure(0, weight=1)
        
        # subtle top border
        top_accent = tk.Frame(header_container, bg=UI_ACCENT, height=2)
        top_accent.grid(row=0, column=0, sticky='we')
        
        title_row = ttk.Frame(header_container, style='Surface.TFrame')
        title_row.grid(row=1, column=0, sticky='we', padx=0, pady=0)
        title_row.columnconfigure(1, weight=1)
        
        # modern icon/badge area
        icon_container = ttk.Frame(title_row, style='Surface.TFrame', width=60)
        icon_container.grid(row=0, column=0, sticky='ns', padx=(20, 0), pady=16)
        icon_container.grid_propagate(False)
        
        # circular badge effect
        badge_outer = tk.Frame(icon_container, bg=UI_ACCENT, width=32, height=32)
        badge_outer.place(relx=0.5, rely=0.5, anchor='center')
        badge_outer.grid_propagate(False)
        badge_inner = tk.Label(badge_outer, text='U', fg='white', bg=UI_ACCENT, 
                              font=('Helvetica', 14, 'bold'))
        badge_inner.place(relx=0.5, rely=0.5, anchor='center')
        
        title_content = ttk.Frame(title_row, style='Surface.TFrame')
        title_content.grid(row=0, column=1, sticky='we', padx=(10, 20), pady=16)
        
        heading = ttk.Label(title_content, text='UIL-DL', style='Header.TLabel', 
                          font=('SF Pro Display', 22, 'bold') if 'SF Pro Display' in root.tk.call('font', 'families') 
                          else ('Helvetica', 22, 'bold'))
        heading.grid(row=0, column=0, sticky='w')
        
        version_label = ttk.Label(title_content, text='v1.0.0-beta-2', style='Subtle.TLabel',
                                font=('Helvetica', 10))
        version_label.grid(row=1, column=0, sticky='w', pady=(2, 0))

        # main content area with padding
        content_frame = ttk.Frame(root, style='TFrame')
        content_frame.grid(row=1, column=0, sticky='we', padx=24, pady=(16, 0))
        content_frame.columnconfigure(0, weight=1)
        
        desc = ttk.Label(content_frame,
                        text='UIL Downloader desktop app. Launches a local server and opens in your browser.',
                        style='Subtle.TLabel', font=('Helvetica', 12), wraplength=600, justify='left')
        desc.grid(row=0, column=0, sticky='w', pady=(0, 20))

        # status with icon
        status_frame = ttk.Frame(content_frame, style='TFrame')
        status_frame.grid(row=1, column=0, sticky='w', pady=(0, 16))
        
        status_indicator = tk.Label(status_frame, text='●', fg=UI_MUTED, bg=UI_BG, font=('Helvetica', 10))
        status_indicator.grid(row=0, column=0, sticky='w')
        
        status_lbl = ttk.Label(status_frame, textvariable=status_var, 
                             font=('Helvetica', 12))
        status_lbl.grid(row=0, column=1, sticky='w', padx=(6, 0))

        # modern url input card
        url_card = ttk.Frame(content_frame, style='Card.TFrame')
        url_card.grid(row=2, column=0, sticky='we', pady=(0, 20))
        url_card.columnconfigure(1, weight=1)
        
        url_caption = ttk.Label(url_card, text='Server URL', style='Subtle.TLabel', 
                              font=('Helvetica', 10, 'bold'))
        url_caption.grid(row=0, column=0, sticky='w', padx=(16, 12), pady=(12, 4))
        
        url_entry = ttk.Entry(
            url_card,
            textvariable=url_var,
            width=50,
            state='readonly',
            font=('Monaco', 11) if 'Monaco' in root.tk.call('font', 'families') else ('Courier', 11),
            style='Url.TEntry'
        )
        url_entry.grid(row=1, column=0, columnspan=2, sticky='we', padx=16, pady=(0, 12))

        def copy_url():
            val = url_var.get().strip()
            if val:
                root.clipboard_clear()
                root.clipboard_append(val)
                root.update()

        def open_in_browser():
            url = url_var.get().strip()
            if url:
                webbrowser.open(url)

        # helpers
        def adjust_window_to_content():
            """resize window to fit current content and keep resizing disabled"""
            try:
                root.update_idletasks()
                req_w = root.winfo_reqwidth() + 24
                req_h = root.winfo_reqheight() + 24
                root.minsize(req_w, req_h)
                root.geometry(f"{req_w}x{req_h}")
                root.resizable(False, False)
            except Exception:
                pass

        def ensure_button_contrast(btn):
            """ensure readable text on white backgrounds for ttk buttons"""
            try:
                style_obj = ttk.Style()
                stylename = btn.cget('style') or 'TButton'
                bg_now = str(style_obj.lookup(stylename, 'background', ('!disabled',)))
                if bg_now.lower() in ('white', '#ffffff', ''):
                    style_obj.configure(stylename, foreground='black')
            except Exception:
                pass

        # modern button group
        btn_container = ttk.Frame(content_frame, style='TFrame')
        btn_container.grid(row=3, column=0, sticky='w', pady=(0, 24))
        
        def create_modern_button(parent, text, command, style='primary', state='disabled'):
            """create a modern styled button with hover effects"""
            if style == 'primary':
                stylename = 'Primary.TButton'
            else:
                stylename = 'Secondary.TButton'

            btn = ttk.Button(
                parent,
                text=text,
                command=command,
                style=stylename,
                state=state,
                cursor='hand2' if state != 'disabled' else 'arrow'
            )

            ensure_button_contrast(btn)
            return btn
        
        open_btn = create_modern_button(btn_container, 'Open in Browser', open_in_browser, 'primary')
        open_btn.pack(side='left', padx=(0, 12))
        
        copy_btn = create_modern_button(btn_container, 'Copy URL', copy_url, 'secondary')
        copy_btn.pack(side='left', padx=(0, 12))

        def open_logs_dir():
            logs_path = (data_path / 'uil-dl.log').parent
            try:
                subprocess.run(['open', logs_path.as_posix()], check=False)
            except Exception:
                webbrowser.open(logs_path.as_uri())

        logs_btn = create_modern_button(btn_container, 'Open Logs', open_logs_dir, 'secondary', 'normal')
        logs_btn.pack(side='left')

        # collapsible details section
        details_container = ttk.Frame(root, style='TFrame')
        details_container.grid(row=2, column=0, sticky='nsew', padx=24, pady=(0, 20))
        root.rowconfigure(2, weight=0)
        details_visible = tk.BooleanVar(value=False)

        def toggle_details():
            if details_visible.get():
                details_frame.grid_remove()
                details_toggle.config(text='▶ Show Details')
                details_visible.set(False)
            else:
                details_frame.grid()
                details_toggle.config(text='▼ Hide Details')
                details_visible.set(True)
            adjust_window_to_content()

        details_toggle = ttk.Button(
            details_container, 
            text='▶ Show Details', 
            command=toggle_details,
            style='Secondary.TButton'
        )
        details_toggle.grid(row=0, column=0, sticky='w')

        details_frame = ttk.Frame(details_container, style='Card.TFrame')
        details_frame.grid(row=1, column=0, sticky='nsew', pady=(8, 0))
        details_container.rowconfigure(1, weight=1)
        details_container.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        details_frame.columnconfigure(0, weight=1)

        # modern scrollable text area
        details_scroll = tk.Scrollbar(details_frame, bg=UI_PANEL, troughcolor=UI_SURFACE, 
                                     highlightthickness=0, bd=0)
        details_scroll.grid(row=0, column=1, sticky='ns', padx=(0, 1), pady=1)
        details_text_local = tk.Text(
            details_frame, 
            wrap='word', 
            fg=UI_TEXT, 
            bg=UI_SURFACE,
            insertbackground=UI_ACCENT, 
            selectbackground=UI_ACCENT,
            selectforeground='white',
            height=8, 
            bd=0, 
            highlightthickness=0,
            font=('Monaco', 10) if 'Monaco' in root.tk.call('font', 'families') else ('Courier', 10),
            padx=12,
            pady=8
        )
        details_text_local.grid(row=0, column=0, sticky='nsew')
        details_scroll.config(command=details_text_local.yview)
        details_text_local.config(yscrollcommand=details_scroll.set, state='disabled')

        # set reference for logger appends and start collapsed by default
        details_text = details_text_local
        details_frame.grid_remove()

        # modern status bar
        status_bar = ttk.Label(root, text='', style='StatusBar.TLabel', anchor='w')
        status_bar.grid(row=3, column=0, sticky='we')

        def refresh_status():
            uptime = int(time.time() - app_start_time)
            mins, secs = divmod(uptime, 60)
            hrs, mins = divmod(mins, 60)
            up_str = f"{hrs:d}h {mins:d}m {secs:d}s"
            enabled, reason = webapp.analytics.analytics_enabled_verbose()
            analytics_str = 'on' if enabled else f'off ({reason})'
            port_str = str(current_port) if current_port else '—'
            status_text = (
                f"analytics: {analytics_str}    "
                f"version: {APP_VERSION}    "
                f"uptime: {up_str}    "
                f"port: {port_str}    "
                f"data: {data_path.as_posix()}"
            )
            status_bar.config(text=status_text)
            root.after(1000, refresh_status)

        refresh_status()

        def on_ready(url: str):
            global current_url, current_port
            status_var.set('Ready')
            url_var.set(url)
            current_url = url
            try:
                current_port = int(url.rsplit(':', 1)[1])
            except Exception:
                current_port = None
            
            # update status indicator
            status_indicator.config(text='●', fg=UI_SUCCESS)
            
            # enable buttons (ttk uses 'state' tuple management)
            open_btn.state(['!disabled'])
            copy_btn.state(['!disabled'])

            adjust_window_to_content()
            
            try:
                if messagebox.askyesno('UIL-DL', 'Open in your browser now?'):
                    open_in_browser()
            except Exception:
                pass

        def on_error(msg: str):
            status_var.set(f'Error: {msg}')
            status_indicator.config(text='●', fg=UI_ERROR)
            try:
                messagebox.showerror('UIL-DL', f'Failed to start: {msg}')
            finally:
                root.after(100, root.destroy)

        # start background initialization
        def bg_task():
            start_flask_in_background(lambda u: root.after(0, lambda: on_ready(u)),
                                      lambda m: root.after(0, lambda: on_error(m)))

        t = threading.Thread(target=bg_task)
        t.daemon = True
        t.start()

        # initial fit-to-content sizing (resizing remains disabled)
        try:
            adjust_window_to_content()
        except Exception:
            pass

        # start ui loop (blocks)
        root.mainloop()

        # after window closed
        shutdown()

    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        print(f"An unexpected error occurred in the main thread: {e}")
        shutdown()
    finally:
        portalocker.unlock(LOCK_FILE)
        LOCK_FILE.close()
        try:
            LOCKFILEPATH.unlink()
        except FileNotFoundError:
            pass
        print("OK lock file released")
