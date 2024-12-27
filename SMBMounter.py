#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import getpass
from pathlib import Path

class SMBMounter:
    def __init__(self, root):
        self.root = root
        self.root.title("SMB Share Mounter")

        # Configuration
        self.default_server = "lagrange"
        self.server = self.default_server
        self.username = getpass.getuser()
        self.smb_links = Path.home() / "SMBLinks"
        self.credentials_dir = Path.home() / ".credentials"

        # Default shares if detection fails
        self.default_shares = {
            "photo": {"mounted": False},
            "music": {"mounted": False},
            "video": {"mounted": False},
            "commun": {"mounted": False}
        }

        # Create main container
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create server input form
        self.create_server_form()

        # Initialize shares as empty
        self.shares = {}

    def create_server_form(self):
        """Creates the server input form"""
        form_frame = ttk.Frame(self.main_container)
        form_frame.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))

        # Server label and entry
        ttk.Label(
            form_frame,
            text="Server:",
            font=('Helvetica', 10)
        ).pack(side=tk.LEFT, padx=5)

        self.server_entry = ttk.Entry(form_frame, width=30)
        self.server_entry.pack(side=tk.LEFT, padx=5)
        self.server_entry.insert(0, self.default_server)

        # Connect button
        ttk.Button(
            form_frame,
            text="Connect",
            command=self.connect_to_server
        ).pack(side=tk.LEFT, padx=5)

    def connect_to_server(self):
        """Connects to the specified server and detects shares"""
        new_server = self.server_entry.get().strip()
        if not new_server:
            messagebox.showerror("Error", "Please enter a server name")
            return

        self.server = new_server

        # Clear previous widgets if they exist
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

        # Detect shares on the new server
        self.shares = self.detect_shares()

        # Create necessary directories
        self.setup_directories()

        # Create interface
        self.create_widgets()

        # Check mount status
        self.check_mounted_shares()

    def setup_directories(self):
        """Creates necessary directories"""
        self.smb_links.mkdir(parents=True, exist_ok=True)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_dir.chmod(0o700)

    def detect_shares(self):
        """Detects available shares on the server"""
        shares = {}
        try:
            cmd = ["smbclient", "-L", self.server, "-N"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "Disk" in line and not "$" in line:
                        share_name = line.split()[0].strip()
                        shares[share_name] = {"mounted": False}

                if not shares:
                    messagebox.showwarning(
                        "Warning",
                        f"No shares found on {self.server}\nUsing default shares list"
                    )
                    shares = self.default_shares.copy()
            else:
                messagebox.showerror(
                    "Error",
                    f"Unable to list shares on {self.server}:\n{result.stderr}\nUsing default shares list"
                )
                shares = self.default_shares.copy()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error while detecting shares: {str(e)}\nUsing default shares list"
            )
            shares = self.default_shares.copy()

        return shares

    def create_widgets(self):
        """Creates the main interface widgets"""
        self.main_frame = ttk.Frame(self.main_container)
        self.main_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Header with refresh button
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(
            header_frame,
            text=f"Available shares on {self.server}",
            font=('Helvetica', 10, 'bold')
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            header_frame,
            text="↻",
            width=3,
            command=self.refresh_shares
        ).pack(side=tk.LEFT, padx=5)

        # Checkboxes for shares
        self.check_vars = {}
        for idx, share in enumerate(self.shares, start=1):
            self.check_vars[share] = tk.BooleanVar()
            cb = ttk.Checkbutton(
                self.main_frame,
                text=f"Share \\{share}",
                variable=self.check_vars[share]
            )
            cb.grid(row=idx, column=0, sticky=tk.W, pady=2)

        # Action buttons
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.grid(row=len(self.shares) + 2, column=0, columnspan=2, pady=10)

        ttk.Button(
            btn_frame,
            text="Mount Selected",
            command=self.mount_selected
        ).grid(row=0, column=0, padx=5)

        # Add new Unmount Selected button
        ttk.Button(
            btn_frame,
            text="Unmount Selected",
            command=self.unmount_selected
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            btn_frame,
            text="Unmount All",
            command=self.unmount_all
        ).grid(row=0, column=2, padx=5)

    def refresh_shares(self):
        """Refreshes the list of available shares"""
        # Save current mount states
        mounted_states = {share: self.shares[share]["mounted"]
                         for share in self.shares if share in self.check_vars}

        # Detect shares again
        self.shares = self.detect_shares()

        # Recreate widgets
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

        self.create_widgets()

        # Restore mount states
        for share, mounted in mounted_states.items():
            if share in self.check_vars:
                self.check_vars[share].set(mounted)

    def mount_selected(self):
        """Mounts selected shares"""
        for share, var in self.check_vars.items():
            if var.get():
                self.mount_share(share)
        self.check_mounted_shares()

    def mount_share(self, share):
        """Mounts a specific share"""
        try:
            cmd = ["gio", "mount", f"smb://{self.server}/{share}"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                endpoint = Path(f"/run/user/{os.getuid()}/gvfs/smb-share:server={self.server},share={share}")
                link_path = self.smb_links / share

                if endpoint.exists():
                    if link_path.exists():
                        link_path.unlink()
                    link_path.symlink_to(endpoint)

                messagebox.showinfo("Success", f"Share {share} mounted successfully in {self.smb_links}")
                return True
            else:
                messagebox.showerror("Error", f"Error mounting {share}\n{result.stderr}")
                return False

        except Exception as e:
            messagebox.showerror("Error", str(e))
            return False

    def unmount_selected(self):
        """Unmounts only the selected shares"""
        for share, var in self.check_vars.items():
            if var.get():
                self.unmount_share(share)
        self.check_mounted_shares()

    def unmount_share(self, share):
        """Unmounts a specific share"""
        try:
            # Remove symbolic link
            link_path = self.smb_links / share
            if link_path.exists():
                link_path.unlink()

            # Unmount share
            cmd = ["gio", "mount", "-u", f"smb://{self.server}/{share}"]
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error unmounting {share}: {str(e)}")
            return False

    def check_mounted_shares(self):
        """Checks which shares are currently mounted"""
        for share in self.shares:
            link_path = self.smb_links / share
            self.shares[share]["mounted"] = link_path.exists()

if __name__ == "__main__":
    root = tk.Tk()
    app = SMBMounter(root)
    root.mainloop()

