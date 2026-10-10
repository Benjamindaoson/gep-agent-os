"""Minimal opt-in Windows tray companion. GEP itself remains web-first."""
from __future__ import annotations
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox,filedialog
import webbrowser
from .sync import (read_settings,save_settings,set_token,get_token,clear_token,
                   validate_server,sync_once)
from .collector import ActivityWatchCollector

class CompanionUI:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title("GEP Windows Companion")
        self.root.geometry("560x535")
        self.root.protocol("WM_DELETE_WINDOW",self.hide)
        self.terminating=threading.Event()
        self.running=False
        self.config=read_settings()
        self.server=tk.StringVar(value=self.config["server"])
        self.secret=tk.StringVar()
        self.note=tk.StringVar(value="Activity tracking is optional and paused by default.")
        self.make_ui()
        self.tray=None
        self.start_tray()
        if self.config["enabled"]:
            self.run_background()

    def make_ui(self):
        area=tk.Frame(self.root,padx=22,pady=15);area.pack(fill="both",expand=True)
        tk.Label(area,text="GEP Companion",font=("Segoe UI",19,"bold")).pack(anchor="w")
        tk.Label(area,text="Only aggregated app durations and chosen Git metadata.\nNo screenshots, typing, window titles or browser URLs.",
                 justify="left",wraplength=500).pack(anchor="w",pady=(6,15))
        tk.Label(area,text="GEP HTTPS website").pack(anchor="w")
        tk.Entry(area,textvariable=self.server).pack(fill="x",pady=(1,10))
        tk.Label(area,text="Device token (create in GEP web portal)").pack(anchor="w")
        tk.Entry(area,textvariable=self.secret,show="*").pack(fill="x")
        actions=tk.Frame(area);actions.pack(fill="x",pady=9)
        tk.Button(actions,text="Pair device",command=self.pair).pack(side="left")
        tk.Button(actions,text="Open GEP",command=self.open_site).pack(side="left",padx=8)
        tk.Label(area,text="Git projects (optional, names and status only)").pack(anchor="w",pady=(10,1))
        self.paths=tk.Listbox(area,height=4)
        self.paths.pack(fill="x")
        self.populate_paths()
        projects=tk.Frame(area);projects.pack(fill="x",pady=8)
        tk.Button(projects,text="Add repository",command=self.add_path).pack(side="left")
        tk.Button(projects,text="Remove selected",command=self.remove_path).pack(side="left",padx=8)
        buttons=tk.Frame(area);buttons.pack(fill="x",pady=(13,6))
        tk.Button(buttons,text="Start / resume",command=self.start_sync).pack(side="left")
        tk.Button(buttons,text="Sync now",command=self.manual_sync).pack(side="left",padx=6)
        tk.Button(buttons,text="Pause",command=self.pause_sync).pack(side="left")
        tk.Button(buttons,text="Disconnect",command=self.disconnect).pack(side="left",padx=6)
        tk.Label(area,textvariable=self.note,wraplength=490,justify="left",fg="#315c88").pack(anchor="w",pady=12)
        tk.Label(area,text="Close hides this window. Quit from the tray menu to stop background sync.",
                 wraplength=490,justify="left").pack(anchor="w")

    def populate_paths(self):
        self.paths.delete(0,tk.END)
        for path in self.config["git_paths"]:self.paths.insert(tk.END,path)

    def add_path(self):
        path=filedialog.askdirectory(title="Select a Git repository")
        if path and path not in self.config["git_paths"]:
            self.config["git_paths"].append(path);save_settings(self.config);self.populate_paths()

    def remove_path(self):
        for index in reversed(self.paths.curselection()):
            self.config["git_paths"].pop(index)
        save_settings(self.config);self.populate_paths()

    def pair(self):
        try:
            server=validate_server(self.server.get().strip())
            set_token(self.secret.get().strip())
            self.config["server"]=server
            self.config["last_sync_ms"]=0
            save_settings(self.config)
            self.secret.set("")
            self.note.set("Paired. Click Start to allow ongoing app-duration sync.")
        except Exception as exc:messagebox.showerror("GEP",str(exc))

    def open_site(self):
        if self.server.get().startswith("https://"):webbrowser.open(self.server.get())

    def start_sync(self):
        try:
            self.config["server"]=validate_server(self.server.get().strip())
            if not get_token():raise ValueError("Pair a device first")
            self.config["enabled"]=True
            save_settings(self.config)
            self.run_background()
            self.note.set("Sync enabled. Keeping the Companion running in the background.")
        except Exception as exc:messagebox.showerror("GEP",str(exc))

    def pause_sync(self):
        self.config["enabled"]=False
        save_settings(self.config)
        self.note.set("Paused. No activity will be uploaded.")

    def manual_sync(self):
        if not self.config["enabled"]:
            self.note.set("Select Start / resume before collecting.")
            return
        threading.Thread(target=self._sync,daemon=True).start()

    def _sync(self):
        try:
            report=sync_once()
            message=f"Cloud acknowledged {report['accepted']} records."
        except Exception as exc:
            message="Sync unavailable: "+str(exc)[:140]
        self.root.after(0,lambda:self.note.set(message))

    def run_background(self):
        if self.running:return
        self.running=True
        def loop():
            while not self.terminating.is_set():
                if read_settings()["enabled"]:
                    self._sync()
                if self.terminating.wait(900):break
        threading.Thread(target=loop,daemon=True).start()

    def disconnect(self):
        self.pause_sync();clear_token()
        self.config["server"]=""
        self.config["last_sync_ms"]=0
        save_settings(self.config)
        self.server.set("")
        self.note.set("Disconnected locally. Revoke the device token in GEP web portal.")

    def show(self,*_):
        self.root.after(0,lambda:(self.root.deiconify(),self.root.lift()))
    def hide(self):
        if self.tray:self.root.withdraw()
        else:self.root.iconify()
    def quit(self,*_):
        self.terminating.set()
        if self.tray:self.tray.stop()
        self.root.after(0,self.root.destroy)
    def start_tray(self):
        try:
            import pystray
            from PIL import Image,ImageDraw
            im=Image.new("RGB",(64,64),"#173d6b")
            ImageDraw.Draw(im).ellipse((12,12,52,52),outline="white",width=5)
            self.tray=pystray.Icon("GEP",im,"GEP Companion",
                 menu=pystray.Menu(
                     pystray.MenuItem("Open GEP Companion",self.show),
                     pystray.MenuItem("Quit",self.quit)))
            threading.Thread(target=self.tray.run,daemon=True).start()
        except Exception:
            self.tray=None
    def run(self):self.root.mainloop()

def main():
    CompanionUI().run()

if __name__=="__main__":main()
