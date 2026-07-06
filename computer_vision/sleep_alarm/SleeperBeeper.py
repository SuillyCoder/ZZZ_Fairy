import tkinter as tk
import cv2
from tkinter import font
from PIL import Image, ImageTk
from SleeperBeeperCam import SleeperBeeperCamera

class SleeperBeeper:
    def __init__(self, root):
        self.root = root
        self.root.title("Sleeper-Beeper")
        self.root.geometry("650x550")
        self.root.resizable(False, False)
        
        self.camera = None
        self.preview_active = False
        self.preview_cap = None
        
        # Title
        title_font = font.Font(family="Arial", size=32, weight="bold")
        title = tk.Label(root, text="SLEEPER-BEEPER", font=title_font)
        title.pack(pady=20)
        
        # Camera preview frame
        self.camera_frame = tk.Frame(root, width=460, height=300, bg="black", relief="solid", borderwidth=2)
        self.camera_frame.pack(pady=10)
        self.camera_frame.pack_propagate(False)
        
        # Canvas for video display
        self.camera_canvas = tk.Label(self.camera_frame, bg="black")
        self.camera_canvas.pack(fill="both", expand=True)
        
        # Buttons
        button_font = font.Font(family="Arial", size=14, weight="bold")
        
        self.run_open_btn = tk.Button(
            root,
            text="Start Program",
            font=button_font,
            bg="#1E5BA8",
            fg="white",
            width=18,
            height=2,
            command=self.run_while_open
        )
        self.run_open_btn.pack(padx=30, pady=30)
        
        # Start preview
        self.start_preview()
    
    def start_preview(self):
        """Start the camera preview in the GUI"""
        self.preview_active = True
        self.preview_cap = cv2.VideoCapture(0)
    
        if not self.preview_cap.isOpened():
            print("Cannot open camera for preview!")
            return
        
        print("Preview started successfully!")
        self.update_preview()

    def update_preview(self):
        """Update the camera preview frame"""
        if not self.preview_active or self.preview_cap is None:
            return
    
        ret, frame = self.preview_cap.read()
        if ret:
            frame = cv2.resize(frame, (460, 300))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.camera_canvas.imgtk = imgtk
            self.camera_canvas.configure(image=imgtk)
    
        self.root.after(33, self.update_preview)

    def stop_preview(self):
        """Stop the camera preview"""
        print("Stopping preview...")
        self.preview_active = False
        if self.preview_cap:
            self.preview_cap.release()
            self.preview_cap = None
    
    def run_while_open(self):
        """Run with OpenCV window visible"""
        print("Starting camera in window mode...")
        self.stop_preview()
        self.root.withdraw()
        
        # Pass callback so GUI restores when 'q' is pressed
        self.camera = SleeperBeeperCamera(on_stop_callback=self.restore_gui)
        if not self.camera.camera_start(show_window=True):
            print("Failed to start camera!")
            self.restore_gui()
    
    def restore_gui(self):
        """Restore the GUI and restart preview"""
        print("Restoring GUI...")
        self.root.deiconify()
        self.start_preview()
    
    def run_in_tray(self):
        """Run minimized (just minimize the detection window)"""
        print("Starting camera in minimized mode...")
        self.stop_preview()
        self.root.withdraw()
        
        # Start camera - when you press 'q' it will restore GUI
        self.camera = SleeperBeeperCamera(on_stop_callback=self.restore_gui)
        if not self.camera.camera_start(show_window=True):
            print("Failed to start camera!")
            self.restore_gui()
    
    def on_closing(self):
        """Handle window close"""
        self.stop_preview()
        if self.camera:
            self.camera.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SleeperBeeper(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()