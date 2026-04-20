import customtkinter as ctk
import threading
import os
import logging
import requests
from io import BytesIO
from PIL import Image, ImageTk
from config import CACHE_DIR, LIBRARY_DIR, THUMBNAIL_SIZE

class WallpaperAppGUI(ctk.CTk):
    def __init__(self, wallpaper_manager):
        super().__init__()

        self.wm = wallpaper_manager
        self.wm.set_gui_callback(self.update_status)

        self.title("Wallpaper change")
        self.geometry("1100x850")
        
        # Override the native Close (X) button
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Cấu hình grid hệ thống
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # TabView
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_home = self.tabview.add("Trang chủ")
        self.tab_search = self.tabview.add("Khám phá (Pexels & Unsplash)")
        self.tab_library = self.tabview.add("Thư viện của tôi")

        self.setup_home_tab()
        self.setup_search_tab()
        self.setup_library_tab()

        # Thanh trạng thái dưới cùng
        self.lbl_status = ctk.CTkLabel(self, text="Sẵn sàng...", text_color="gray", font=("Arial", 12))
        self.lbl_status.grid(row=1, column=0, pady=(0, 10))

    def setup_home_tab(self):
        # Nội dung cũ được chuyển vào đây và sắp xếp lại
        self.tab_home.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(self.tab_home, text="WALLPAPER CHANGE", font=("Inter", 28, "bold"))
        lbl_title.pack(pady=(40, 20))

        self.btn_next = ctk.CTkButton(self.tab_home, text="ĐỔI HÌNH NỀN NGẪU NHIÊN", font=("Inter", 16, "bold"), 
                                     height=60, command=self.on_next_click)
        self.btn_next.pack(pady=10, padx=150, fill="x")

        # Khung cài đặt
        setting_frame = ctk.CTkFrame(self.tab_home, fg_color="transparent")
        setting_frame.pack(pady=20, padx=50, fill="x")

        self.btn_folder = ctk.CTkButton(setting_frame, text="Mở Cache", width=150, command=self.open_cache_folder)
        self.btn_folder.grid(row=0, column=0, padx=10, pady=10)

        self.btn_lib = ctk.CTkButton(setting_frame, text="Mở Thư viện (Library)", width=150, command=self.open_library_folder)
        self.btn_lib.grid(row=0, column=1, padx=10, pady=10)

        self.btn_reload = ctk.CTkButton(setting_frame, text="Tải lại Config", width=150, command=self.on_reload_click)
        self.btn_reload.grid(row=0, column=2, padx=10, pady=10)

        # Switches
        import config
        self.autostart_var = ctk.StringVar(value="on" if self.check_autostart_enabled() else "off")
        self.chk_autostart = ctk.CTkSwitch(self.tab_home, text="Khởi động cùng Windows", 
                                          command=self.toggle_autostart, variable=self.autostart_var, onvalue="on", offvalue="off")
        self.chk_autostart.pack(pady=10)

        self.taskbar_var = ctk.StringVar(value="on" if config.TASKBAR_TRANSPARENT else "off")
        self.chk_taskbar = ctk.CTkSwitch(self.tab_home, text="Taskbar tàng hình (100% Clear)", 
                                          command=self.toggle_taskbar, variable=self.taskbar_var, onvalue="on", offvalue="off")
        self.chk_taskbar.pack(pady=10)

        self.btn_hide = ctk.CTkButton(self.tab_home, text="Ẩn xuống khay hệ thống", fg_color="#e74c3c", hover_color="#c0392b", command=self.hide_window)
        self.btn_hide.pack(pady=(40, 20))

    def setup_search_tab(self):
        self.tab_search.grid_columnconfigure(0, weight=1)
        self.tab_search.grid_rowconfigure(1, weight=1)

        # Cụm tìm kiếm
        search_frame = ctk.CTkFrame(self.tab_search, fg_color="transparent")
        search_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Nhập từ khóa (vD: Space, Nature, Cyberpunk...)", height=40)
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.search_entry.bind("<Return>", lambda e: self.on_search_click())

        self.source_option = ctk.CTkOptionMenu(search_frame, values=["All", "Pexels", "Unsplash"], width=120, height=40)
        self.source_option.grid(row=0, column=1, padx=(0, 10))

        self.btn_search = ctk.CTkButton(search_frame, text="TÌM KIẾM", width=100, height=40, font=("Inter", 13, "bold"), command=self.on_search_click)
        self.btn_search.grid(row=0, column=2)

        # Cụm kết quả hiển thị dạng lưới (Grid)
        self.scroll_frame = ctk.CTkScrollableFrame(self.tab_search, label_text="Kết quả tìm kiếm")
        self.scroll_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.scroll_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.search_results = []

    def setup_library_tab(self):
        self.tab_library.grid_columnconfigure(0, weight=1)
        self.tab_library.grid_rowconfigure(1, weight=1)

        # Thanh điều khiển thư viện
        lib_ctrl_frame = ctk.CTkFrame(self.tab_library, fg_color="transparent")
        lib_ctrl_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        lbl_lib = ctk.CTkLabel(lib_ctrl_frame, text="DANH SÁCH ẢNH ĐÃ TẢI VỀ", font=("Inter", 16, "bold"))
        lbl_lib.pack(side="left", padx=10)

        self.btn_refresh_lib = ctk.CTkButton(lib_ctrl_frame, text="LÀM MỚI (REFRESH)", width=150, command=self.refresh_library)
        self.btn_refresh_lib.pack(side="right", padx=10)

        self.lib_scroll_frame = ctk.CTkScrollableFrame(self.tab_library, label_text="Thư viện cục bộ")
        self.lib_scroll_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.lib_scroll_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Tự động load lần đầu
        self.refresh_library()

    def refresh_library(self):
        for child in self.lib_scroll_frame.winfo_children():
            child.destroy()
        
        threading.Thread(target=self._load_library_worker, daemon=True).start()

    def _load_library_worker(self):
        if not os.path.exists(LIBRARY_DIR): return
        
        files = [f for f in os.listdir(LIBRARY_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        # Sắp xếp mới nhất lên đầu
        files.sort(key=lambda x: os.path.getmtime(os.path.join(LIBRARY_DIR, x)), reverse=True)
        
        self.after(0, lambda: self._display_library(files))

    def _display_library(self, files):
        if not files:
            lbl_empty = ctk.CTkLabel(self.lib_scroll_frame, text="Thư viện trống. Hãy tìm và tải ảnh trong tab Khám phá!")
            lbl_empty.grid(row=0, column=0, columnspan=3, pady=50)
            return

        for i, filename in enumerate(files):
            row = i // 3
            col = i % 3
            filepath = os.path.join(LIBRARY_DIR, filename)
            
            card = ctk.CTkFrame(self.lib_scroll_frame, corner_radius=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            img_label = ctk.CTkLabel(card, text="Đang tải...", width=THUMBNAIL_SIZE[0], height=THUMBNAIL_SIZE[1], corner_radius=5)
            img_label.pack(pady=10, padx=10)
            
            lbl_name = ctk.CTkLabel(card, text=filename[:25] + "..." if len(filename) > 25 else filename, font=("Arial", 11), text_color="gray")
            lbl_name.pack()

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(pady=10)
            
            btn_set = ctk.CTkButton(btn_frame, text="Cài nền", width=90, height=30, command=lambda p=filepath: self.set_local_wallpaper(p))
            btn_set.grid(row=0, column=0, padx=5)
            
            btn_del = ctk.CTkButton(btn_frame, text="Xóa", fg_color="#c0392b", hover_color="#962d22", width=90, height=30, 
                                    command=lambda p=filepath: self.delete_from_lib(p))
            btn_del.grid(row=0, column=1, padx=5)

            # Load thumbnail từ file cục bộ
            threading.Thread(target=self._load_local_thumbnail, args=(filepath, img_label), daemon=True).start()

    def _load_local_thumbnail(self, path, label):
        try:
            img = Image.open(path)
            img.thumbnail(THUMBNAIL_SIZE)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=THUMBNAIL_SIZE)
            self.after(0, lambda: label.configure(image=ctk_img, text=""))
        except:
            self.after(0, lambda: label.configure(text="Lỗi hiển thị"))

    def set_local_wallpaper(self, path):
        success = self.wm.set_wallpaper(path)
        if success: self.update_status(f"Đã đặt hình nền từ thư viện: {os.path.basename(path)}")
        else: self.update_status("Lỗi khi cài hình nền.")

    def delete_from_lib(self, path):
        try:
            os.remove(path)
            self.update_status(f"Đã xóa ảnh: {os.path.basename(path)}")
            self.refresh_library()
        except Exception as e:
            self.update_status(f"Lỗi khi xóa: {e}")

    def on_search_click(self):
        query = self.search_entry.get()
        if not query: return
        
        source = self.source_option.get()
        self.update_status(f"Đang tìm kiếm '{query}' trên {source}...")
        
        # Xóa kết quả cũ
        for child in self.scroll_frame.winfo_children():
            child.destroy()
            
        self.btn_search.configure(state="disabled", text="ĐANG TÌM...")
        threading.Thread(target=self._search_thread_worker, args=(query, source), daemon=True).start()

    def _search_thread_worker(self, query, source):
        results = self.wm.search_images(query, source)
        self.after(0, lambda: self._display_results(results))

    def _display_results(self, results):
        self.btn_search.configure(state="normal", text="TÌM KIẾM")
        if not results:
            self.update_status("Không tìm thấy kết quả hoặc lỗi API Key.")
            return

        self.update_status(f"Tìm thấy {len(results)} ảnh.")
        
        for i, item in enumerate(results):
            row = i // 3
            col = i % 3
            
            card = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Label chứa ảnh (placeholder khi đang tải)
            img_label = ctk.CTkLabel(card, text="Đang tải...", width=THUMBNAIL_SIZE[0], height=THUMBNAIL_SIZE[1], corner_radius=5)
            img_label.pack(pady=10, padx=10)
            
            # Thông tin tác giả
            lbl_info = ctk.CTkLabel(card, text=f"{item['source']} | {item['author'][:20]}", font=("Arial", 11), text_color="gray")
            lbl_info.pack()

            # Nút chức năng
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(pady=10)
            
            btn_set = ctk.CTkButton(btn_frame, text="Cài nền", width=90, height=30, command=lambda url=item['full']: self.set_search_wallpaper(url))
            btn_set.grid(row=0, column=0, padx=5)
            
            btn_dl = ctk.CTkButton(btn_frame, text="Tải về", fg_color="#27ae60", hover_color="#2ecc71", width=90, height=30, 
                                   command=lambda url=item['full']: self.download_to_lib(url))
            btn_dl.grid(row=0, column=1, padx=5)

            # Tải thumbnail bất đồng bộ
            threading.Thread(target=self._load_thumbnail, args=(item['thumbnail'], img_label), daemon=True).start()

    def _load_thumbnail(self, url, label):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            
            # Resize để vừa card
            img.thumbnail(THUMBNAIL_SIZE)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=THUMBNAIL_SIZE)
            
            self.after(0, lambda: label.configure(image=ctk_img, text=""))
        except:
            self.after(0, lambda: label.configure(text="Lỗi tải ảnh"))

    def set_search_wallpaper(self, url):
        self.update_status("Đang tải và cài hình nền...")
        threading.Thread(target=lambda: self.wm.set_wallpaper(self.wm.download_image(url)), daemon=True).start()

    def download_to_lib(self, url):
        self.update_status("Đang tải ảnh về thư viện...")
        def _dl():
            path = self.wm.download_image(url, target_dir=LIBRARY_DIR)
            if path:
                self.update_status(f"Đã lưu vào Library: {os.path.basename(path)}")
            else:
                self.update_status("Lỗi khi tải về thư viện.")
        threading.Thread(target=_dl, daemon=True).start()

    # --- Các hàm cũ giữ nguyên logic ---
    def check_autostart_enabled(self):
        try:
            import winreg
            import sys
            pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "OC_4K_Wallpaper")
            winreg.CloseKey(key)
            return True
        except: return False

    def toggle_autostart(self):
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        import sys
        pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
        import config
        main_py = os.path.join(config.BASE_DIR, "main.pyw")
        cmd = f'"{pythonw_exe}" "{main_py}"'
        
        if self.autostart_var.get() == "on":
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "OC_4K_Wallpaper", 0, winreg.REG_SZ, cmd)
                winreg.CloseKey(key)
                self.update_status("Đã BẬT khởi động cùng Windows!")
            except: self.autostart_var.set("off")
        else:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, "OC_4K_Wallpaper")
                winreg.CloseKey(key)
                self.update_status("Đã TẮT khởi động cùng Windows!")
            except: pass

    def toggle_taskbar(self):
        import taskbar_effect
        import config
        is_on = (self.taskbar_var.get() == "on")
        config.TASKBAR_TRANSPARENT = is_on
        taskbar_effect.set_transparent(1 if is_on else 0)
        self.update_status(f"Taskbar tàng hình: {'BẬT' if is_on else 'TẮT'}")

    def hide_window(self):
        self.withdraw()

    def on_next_click(self):
        self.btn_next.configure(state="disabled", text="ĐANG ĐỔI...")
        threading.Thread(target=self._next_thread_worker, daemon=True).start()

    def _next_thread_worker(self):
        success = self.wm.next_wallpaper()
        state = "Hoàn tất!" if success else "Lỗi tải ảnh."
        self.update_status(state)
        self.btn_next.configure(state="normal", text="ĐỔI HÌNH NỀN NGẪU NHIÊN")

    def on_reload_click(self):
        threading.Thread(target=lambda: self.wm.fetch_list(), daemon=True).start()
        self.update_status("Đã nạp lại danh sách.")

    def update_status(self, message):
        self.after(0, lambda: self.lbl_status.configure(text=message))

    def open_cache_folder(self):
        os.startfile(CACHE_DIR)

    def open_library_folder(self):
        os.startfile(LIBRARY_DIR)

    def run(self):
        self.mainloop()
