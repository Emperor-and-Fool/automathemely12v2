#!/usr/bin/env python3
# automathemely_tray.py
import os, sys, shutil, subprocess
from PyQt5 import QtWidgets, QtGui, QtCore

LOG_PATH = os.path.expanduser("~/.config/automathemely/.autothscheduler.log")
# fallback python launcher (edit if you want)
VENV_PY = os.path.expanduser("~/Pysolated/penv_automathemely12v2/bin/python")

def find_wrapper():
    w = shutil.which("automathemely")
    if w:
        return [w]
    # fallback to venv python -m bin.run --manage/restart
    return [VENV_PY, "-m", "bin.run"]

def last_log_line(path):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                return "(empty)"
            # read tail
            block = 1024
            data = b""
            while size > 0:
                read_size = min(block, size)
                f.seek(size - read_size)
                chunk = f.read(read_size)
                data = chunk + data
                if b"\n" in data:
                    break
                size -= read_size
            lines = data.splitlines()
            for l in reversed(lines):
                line = l.strip()
                if line:
                    try:
                        return line.decode("utf-8", errors="replace")
                    except Exception:
                        return repr(line)
    except FileNotFoundError:
        return "(log not found)"
    except Exception as e:
        return f"(error reading log: {e})"

class TrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon=None):
        icon = icon or QtGui.QIcon.fromTheme("applications-system")
        super().__init__(icon)
        self.menu = QtWidgets.QMenu()
        self.act_open = self.menu.addAction("Open Manager")
        self.act_restart = self.menu.addAction("Restart Scheduler")
        self.menu.addSeparator()
        self.act_show = self.menu.addAction("Show last log")
        self.menu.addSeparator()
        self.act_quit = self.menu.addAction("Quit")
        self.setContextMenu(self.menu)

        self.act_open.triggered.connect(self.open_manager)
        self.act_restart.triggered.connect(self.restart_scheduler)
        self.act_show.triggered.connect(self.show_last_log)
        self.act_quit.triggered.connect(QtWidgets.qApp.quit)

        self.last_line_action = self.menu.addAction("Last: (loading...)")
        self.last_line_action.setDisabled(True)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(30 * 1000)  # 30s
        self.timer.timeout.connect(self.update_last_line)
        self.timer.start()
        self.update_last_line()
        self.activated.connect(self.on_click)
        self.show()

    def run_cmd(self, args, wait=False):
        try:
            subprocess.Popen(args) if not wait else subprocess.run(args)
        except Exception as e:
            self.showMessage("AutomaThemely tray", f"Command failed: {e}")

    def open_manager(self):
        base = find_wrapper()
        cmd = base + ["--manage"] if len(base) == 1 else base + ["--manage"]
        self.run_cmd(cmd)

    def restart_scheduler(self):
        base = find_wrapper()
        cmd = base + ["--restart"] if len(base) == 1 else base + ["--restart"]
        self.run_cmd(cmd)
        self.showMessage("AutomaThemely", "Restart requested")

    def show_last_log(self):
        s = last_log_line(LOG_PATH)
        QtWidgets.QMessageBox.information(None, "Last log line", s)

    def update_last_line(self):
        s = last_log_line(LOG_PATH)
        tooltip = (s[:200] + "...") if len(s) > 200 else s
        self.setToolTip(tooltip)
        self.last_line_action.setText("Last: " + (s[:80] + "..." if len(s) > 80 else s))

    def on_click(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.show_last_log()

def main():
    app = QtWidgets.QApplication(sys.argv)
    # use repo icon if present
    ic = None
    repo_icon = os.path.join(os.path.dirname(__file__), "assets", "automathemely-icon.svg")
    if os.path.exists(repo_icon):
        ic = QtGui.QIcon(repo_icon)
    tray = TrayApp(icon=ic)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
