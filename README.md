# Mass App Uninstaller

A lightning-fast, highly modern batch uninstaller for Debian-based systems. Quickly view and bulk-remove applications from your system with an elegant GTK3 (Adwaita) interface.

![Release](https://img.shields.io/badge/Release-v1.0-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Debian%20%7C%20Ubuntu%20%7C%20Mint-green.svg)

## Features

- 🎨 **Native Adwaita UI**: Built perfectly in `PyGObject` (GTK3) for a flawless, native desktop experience on GNOME and similar desktop environments.
- 🧹 **Intelligent Package Categorization**: Safely separates your user-facing GUI desktop applications from background/CLI tools, filtering out critical system components so you don't break your OS.
- 📖 **Real-World Naming**: Automatically parses `.desktop` files to present applications with their actual, human-readable names (e.g., "Disk Usage Analyzer" instead of `baobab`).
- 🔑 **Password Persistence**: Uses `pkexec` to securely batch-uninstall all selected applications while only prompting for your password *once*.
- 🔍 **Live Search Filtering**: Find exactly what you want to remove instantly.

## Installation & Usage

### Method 1: `.deb` Package (Recommended)
1. Download the `mass-uninstaller_1.0-1_all.deb` file from the Releases page.
2. Install it by double-clicking the file or running:
   ```bash
   sudo apt install ./mass-uninstaller_1.0-1_all.deb
   ```
3. The app will appear in your system's application menu. You can launch it by searching for **Mass App Uninstaller**.

### Method 2: Portable Archive (`.tar.gz`)
1. Download the latest `MassUninstaller-v1.0.tar.gz`.
2. Extract the archive to your desired location.
3. Double-click the `Mass Uninstaller.desktop` file to launch it directly.

Alternatively, run from the terminal:
```bash
python3 uninstaller.py
```

### Dependencies
*(Note: If you use the `.deb` package, APT will automatically install these dependencies for you!)*
- `python3`
- `python3-apt`
- `python3-gi` (PyGObject)

*(Note: The provided `launch.sh` will attempt to automatically install dependencies via `apt-get` if they are missing.)*

## Architecture

This application queries the APT cache using `python3-apt`. It cross-references installed package paths against `/usr/share/applications/` to determine if a package is a "GUI Application", and parses the `Name=` field of `.desktop` files to obtain clean display names. Any manual packages that are not marked as GUI apps are displayed in the "CLI Packages" tab.

When uninstalling, the script aggregates the selected `pkg` names and executes:
`pkexec apt-get remove -y <packages>`

## License

MIT License.
