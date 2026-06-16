import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango
import apt
import subprocess
import threading
import os

class UninstallerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Mass App Uninstaller")
        self.set_default_size(900, 600)
        self.set_border_width(10)
        
        self.gui_packages_data = []  # List of dicts
        self.cli_packages_data = []

        # Main Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)

        # Header bar / Search
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(header_box, False, False, 0)
        
        title_lbl = Gtk.Label()
        title_lbl.set_markup("<span size='large' weight='bold'>Mass App Uninstaller</span>")
        title_lbl.set_xalign(0.0)
        header_box.pack_start(title_lbl, False, False, 0)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.connect("search-changed", self.on_search_changed)
        header_box.pack_end(self.search_entry, False, False, 0)

        # Notebook for Tabs
        self.notebook = Gtk.Notebook()
        main_box.pack_start(self.notebook, True, True, 0)

        # Tab 1: GUI Apps
        self.gui_listbox = Gtk.ListBox()
        self.gui_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        gui_scroll = Gtk.ScrolledWindow()
        gui_scroll.add(self.gui_listbox)
        self.notebook.append_page(gui_scroll, Gtk.Label(label="GUI Applications"))

        # Tab 2: CLI Apps
        self.cli_listbox = Gtk.ListBox()
        self.cli_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        cli_scroll = Gtk.ScrolledWindow()
        cli_scroll.add(self.cli_listbox)
        self.notebook.append_page(cli_scroll, Gtk.Label(label="CLI Packages"))

        # Bottom Bar
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(bottom_box, False, False, 0)
        
        self.loading_spinner = Gtk.Spinner()
        bottom_box.pack_start(self.loading_spinner, False, False, 0)
        
        self.loading_label = Gtk.Label(label="")
        bottom_box.pack_start(self.loading_label, False, False, 0)

        self.btn_uninstall = Gtk.Button(label="Uninstall Selected")
        self.btn_uninstall.get_style_context().add_class("destructive-action")
        self.btn_uninstall.connect("clicked", self.on_uninstall_clicked)
        self.btn_uninstall.set_sensitive(False)
        bottom_box.pack_end(self.btn_uninstall, False, False, 0)

        self.load_packages_async()

    def _get_desktop_name(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("Name="):
                        return line.strip().split("=", 1)[1]
        except:
            pass
        return None

    def load_packages_async(self):
        self.loading_spinner.start()
        self.loading_label.set_text("Fetching installed packages...")
        self.gui_packages_data = []
        self.cli_packages_data = []
        threading.Thread(target=self._load_packages_thread, daemon=True).start()

    def _load_packages_thread(self):
        try:
            cache = apt.Cache()
            for pkg in cache:
                if pkg.is_installed:
                    files = pkg.installed_files
                    is_gui = False
                    desktop_file = None
                    if files:
                        for f in files:
                            if f.startswith("/usr/share/applications/") and f.endswith(".desktop"):
                                is_gui = True
                                desktop_file = f
                                break
                    
                    if is_gui and desktop_file:
                        real_name = self._get_desktop_name(desktop_file)
                        if not real_name:
                            real_name = pkg.name.replace("-", " ").title()
                        desc = pkg.candidate.summary if pkg.candidate and pkg.candidate.summary else ""
                        self.gui_packages_data.append({
                            "name": real_name,
                            "pkg": pkg.name,
                            "desc": desc,
                            "selected": False
                        })
                    elif pkg.candidate.priority in ("optional", "extra") and not pkg.is_auto_installed and not pkg.name.startswith("lib"):
                        clean_name = pkg.name.replace("-", " ").title()
                        desc = pkg.candidate.summary if pkg.candidate and pkg.candidate.summary else ""
                        self.cli_packages_data.append({
                            "name": clean_name,
                            "pkg": pkg.name,
                            "desc": desc,
                            "selected": False
                        })
            
            self.gui_packages_data.sort(key=lambda x: x["name"].lower())
            self.cli_packages_data.sort(key=lambda x: x["name"].lower())
            GLib.idle_add(self._on_packages_loaded)
        except Exception as e:
            GLib.idle_add(self.show_error, f"Failed to load packages:\n{e}")

    def _on_packages_loaded(self):
        self.loading_spinner.stop()
        self.loading_label.set_text("")
        self.btn_uninstall.set_sensitive(True)
        self.render_lists()

    def render_lists(self):
        # Clear existing
        for child in self.gui_listbox.get_children():
            self.gui_listbox.remove(child)
        for child in self.cli_listbox.get_children():
            self.cli_listbox.remove(child)

        search_query = self.search_entry.get_text().lower()

        self._populate_listbox(self.gui_listbox, self.gui_packages_data, search_query)
        self._populate_listbox(self.cli_listbox, self.cli_packages_data, search_query)
        
        self.gui_listbox.show_all()
        self.cli_listbox.show_all()

    def _populate_listbox(self, listbox, data, search_query):
        for item in data:
            if search_query and search_query not in item["name"].lower() and search_query not in item["pkg"].lower():
                continue
            
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            hbox.set_margin_start(10)
            hbox.set_margin_end(10)
            hbox.set_margin_top(8)
            hbox.set_margin_bottom(8)
            
            # Checkbox + App Name (Left)
            check = Gtk.CheckButton(label=item["name"])
            check.set_active(item["selected"])
            check.connect("toggled", self.on_check_toggled, item)
            
            left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            left_box.set_size_request(280, -1)
            left_box.pack_start(check, False, False, 0)
            hbox.pack_start(left_box, False, False, 0)

            # Package Name (Center)
            lbl_pkg = Gtk.Label(label=f"({item['pkg']})")
            lbl_pkg.get_style_context().add_class("dim-label")
            lbl_pkg.set_xalign(0.5)
            
            center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            center_box.set_size_request(200, -1)
            center_box.pack_start(lbl_pkg, True, True, 0)
            hbox.pack_start(center_box, False, False, 0)

            # Description (Right)
            lbl_desc = Gtk.Label(label=item["desc"])
            lbl_desc.set_ellipsize(Pango.EllipsizeMode.END)
            lbl_desc.set_xalign(1.0)
            lbl_desc.get_style_context().add_class("dim-label")
            hbox.pack_start(lbl_desc, True, True, 0)

            row.add(hbox)
            listbox.add(row)

    def on_check_toggled(self, widget, item):
        item["selected"] = widget.get_active()

    def on_search_changed(self, entry):
        self.render_lists()

    def on_uninstall_clicked(self, widget):
        selected_pkgs = [item["pkg"] for item in self.gui_packages_data if item["selected"]] + \
                        [item["pkg"] for item in self.cli_packages_data if item["selected"]]
        
        if not selected_pkgs:
            self.show_error("Please select at least one package to uninstall.")
            return

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Are you sure you want to uninstall {len(selected_pkgs)} package(s)?"
        )
        dialog.format_secondary_text("This may require your password.")
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            self.execute_uninstall(selected_pkgs)

    def execute_uninstall(self, packages):
        self.btn_uninstall.set_sensitive(False)
        self.loading_spinner.start()
        self.loading_label.set_text("Uninstalling packages...")

        for child in self.gui_listbox.get_children():
            self.gui_listbox.remove(child)
        for child in self.cli_listbox.get_children():
            self.cli_listbox.remove(child)

        threading.Thread(target=self._run_pkexec, args=(packages,), daemon=True).start()

    def _run_pkexec(self, packages):
        try:
            cmd = ["pkexec", "apt-get", "remove", "-y"] + packages
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                GLib.idle_add(self._uninstall_success)
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                if result.returncode == 126:
                    error_msg = "Authentication cancelled or failed."
                GLib.idle_add(self._uninstall_failure, error_msg)
        except Exception as e:
            GLib.idle_add(self._uninstall_failure, str(e))

    def _uninstall_success(self):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Success"
        )
        dialog.format_secondary_text("Selected packages have been uninstalled successfully.")
        dialog.run()
        dialog.destroy()
        
        self.load_packages_async()

    def _uninstall_failure(self, error_msg):
        self.show_error(f"Uninstallation failed:\n{error_msg}")
        self.btn_uninstall.set_sensitive(True)
        self.loading_spinner.stop()
        self.loading_label.set_text("")
        self.render_lists()

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    win = UninstallerWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
