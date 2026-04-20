import time
import threading
import schedule
import logging
from wallpaper_manager import WallpaperManager
from gui_app import WallpaperAppGUI
from tray_app import TrayApp
from config import UPDATE_INTERVAL_MINUTES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_scheduler(wm):
    logging.info("Đang áp dụng hình nền đầu tiên...")
    wm.next_wallpaper()
    logging.info(f"Đã lập lịch đổi hình nền mỗi {UPDATE_INTERVAL_MINUTES} phút.")
    schedule.every(UPDATE_INTERVAL_MINUTES).minutes.do(wm.next_wallpaper)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Lỗi Scheduler: {e}")
            time.sleep(5)

def run_taskbar_enforcer():
    import taskbar_effect
    import config
    import ctypes
    user32 = ctypes.windll.user32
    while True:
        try:
            if config.TASKBAR_TRANSPARENT:
                # Ép trong suốt liên tục để đề phòng Windows chèn lại màu khi mở Start
                hwnd = user32.FindWindowW("Shell_TrayWnd", None)
                if hwnd:
                    taskbar_effect.set_transparent(1)
            else:
                pass
            time.sleep(2)
        except:
            time.sleep(5)

def run_tray(wm, app):
    tray = TrayApp(wm, app)
    tray.run()

def main():
    wm = WallpaperManager()
    wm.fetch_list()
    
    # Khởi tạo Cửa sổ giao diện nhưng ẨN NGAY LẬP TỨC
    app = WallpaperAppGUI(wm)
    app.withdraw()
    
    # Khởi chạy Scheduler (Luồng nền)
    scheduler_thread = threading.Thread(target=run_scheduler, args=(wm,), daemon=True)
    scheduler_thread.start()
    
    # Khởi chạy Module chống Windows phục hồi màu Taskbar
    taskbar_thread = threading.Thread(target=run_taskbar_enforcer, daemon=True)
    taskbar_thread.start()
    
    # Khởi chạy System Tray Icon (Luồng nền)
    tray_thread = threading.Thread(target=run_tray, args=(wm, app), daemon=True)
    tray_thread.start()
    
    # Main thread độc chiếm vòng lặp của CustomTkinter để không bị crack
    app.run()

if __name__ == "__main__":
    main()
