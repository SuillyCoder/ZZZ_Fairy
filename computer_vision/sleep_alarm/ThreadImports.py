import threading  # Add at top

def show_window_from_tray(self):
    """Show the main window from system tray"""
    self.tray_icon.stop()
    self.camera.stop()
    self.restore_gui()

def stop_from_tray(self):
    """Stop detection but keep tray running"""
    self.camera.stop()

def exit_app(self):
    """Exit the entire application"""
    if self.camera:
        self.camera.stop()
    self.tray_icon.stop()
    self.root.quit()