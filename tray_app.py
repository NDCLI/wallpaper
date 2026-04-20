import pystray
from PIL import Image, ImageDraw
import threading
import logging

class TrayApp:
    def __init__(self, wallpaper_manager, gui_app, title="OC 4K Wallpaper App"):
        self.wm = wallpaper_manager
        self.app = gui_app
        self.title = title
        self.icon = None

    def create_image(self):
        import os
        import config
        icon_path = os.path.join(config.BASE_DIR, "icon.png")
        if os.path.exists(icon_path):
            try:
                # Resize để tối ưu cho icon nhỏ (chống lỗi tràn memory pystray)
                img = Image.open(icon_path)
                img.thumbnail((128, 128))
                return img
            except:
                pass
            
        # Fallback ảnh mặc định nếu mất file
        width = 64
        height = 64
        color1 = "#2c3e50"
        color2 = "#ecf0f1"
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill=color2)
        return image

    def on_settings(self, icon, item):
        logging.info("Người dùng mở Setting GUI.")
        # Ctk must be interacted with in main thread safely
        self.app.after(0, self.app.deiconify)
        self.app.after(0, self.app.lift)

    def on_next(self, icon, item):
        threading.Thread(target=self.wm.next_wallpaper, daemon=True).start()

    def on_quit(self, icon, item):
        logging.info("Người dùng chọn Menu: Quit.")
        icon.stop()
        self.app.after(0, self.app.quit)

    def setup(self):
        menu = pystray.Menu(
            pystray.MenuItem('Next Wallpaper', self.on_next),
            pystray.MenuItem('Cài Đặt (Mở GUI)', self.on_settings),
            pystray.MenuItem('Thoát (Quit)', self.on_quit)
        )
        self.icon = pystray.Icon("wallpaper_change", self.create_image(), self.title, menu)

    def run(self):
        if not self.icon:
            self.setup()
        self.icon.run()
