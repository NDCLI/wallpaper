import os
import random
import ctypes
import requests
from urllib.parse import urlparse
import logging
import traceback
import hashlib
import threading
from config import CACHE_DIR, LIBRARY_DIR, ONLINE_LIST_URL, MAX_CACHE_FILES, PEXELS_API_KEY, UNSPLASH_ACCESS_KEY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ImageSource:
    def search(self, query):
        raise NotImplementedError

class PexelsSource(ImageSource):
    def search(self, query):
        if not PEXELS_API_KEY:
            return []
        try:
            headers = {"Authorization": PEXELS_API_KEY}
            params = {"query": query, "per_page": 20}
            url = "https://api.pexels.com/v1/search"
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for photo in data.get("photos", []):
                results.append({
                    "id": f"pexels_{photo['id']}",
                    "source": "Pexels",
                    "thumbnail": photo["src"]["medium"],
                    "full": photo["src"]["original"],
                    "author": photo["photographer"],
                    "url": photo["url"]
                })
            return results
        except Exception as e:
            logging.error(f"Pexels error: {e}")
            return []

class UnsplashSource(ImageSource):
    def search(self, query):
        if not UNSPLASH_ACCESS_KEY:
            return []
        try:
            params = {"query": query, "per_page": 20, "client_id": UNSPLASH_ACCESS_KEY}
            url = "https://api.unsplash.com/search/photos"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for photo in data.get("results", []):
                results.append({
                    "id": f"unsplash_{photo['id']}",
                    "source": "Unsplash",
                    "thumbnail": photo["urls"]["small"],
                    "full": photo["urls"]["full"],
                    "author": photo["user"]["name"],
                    "url": photo["links"]["html"]
                })
            return results
        except Exception as e:
            logging.error(f"Unsplash error: {e}")
            return []

class WallpaperManager:
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.library_dir = LIBRARY_DIR
        self.online_list_url = ONLINE_LIST_URL
        self.wallpapers = []
        self.current_url = None
        self.gui_callback = None
        
        self.sources = {
            "Pexels": PexelsSource(),
            "Unsplash": UnsplashSource()
        }
        
        for d in [self.cache_dir, self.library_dir]:
            if not os.path.exists(d):
                os.makedirs(d)
                logging.info(f"Đã tạo thư mục: {d}")
            
    def set_gui_callback(self, callback):
        '''Callback để gửi thông báo cho GUI (cập nhật trạng thái)'''
        self.gui_callback = callback
        
    def _notify(self, msg):
        if self.gui_callback:
            self.gui_callback(msg)

    def search_images(self, query, source_name="All"):
        results = []
        threads = []
        
        def run_search(name, src):
            res = src.search(query)
            results.extend(res)

        if source_name == "All" or source_name not in self.sources:
            for name, src in self.sources.items():
                t = threading.Thread(target=run_search, args=(name, src))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
        else:
            results = self.sources[source_name].search(query)
            
        return results
            
    def fetch_list(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
            if self.online_list_url.startswith("http"):
                logging.info(f"Đang tải danh sách từ: {self.online_list_url}")
                response = requests.get(self.online_list_url, headers=headers, timeout=10)
                response.raise_for_status()
                text_data = response.text
            else:
                logging.info(f"Đang tải danh sách từ file local: {self.online_list_url}")
                if os.path.exists(self.online_list_url):
                    with open(self.online_list_url, 'r', encoding='utf-8') as f:
                        text_data = f.read()
                else:
                    text_data = ""
                    logging.warning("File danh sách không tồn tại.")
            
            urls = [line.strip() for line in text_data.split('\n') if line.strip() and line.strip().startswith('http')]
            
            if urls:
                self.wallpapers = urls
                logging.info(f"Đã tải {len(self.wallpapers)} liên kết hình ảnh.")
                threading.Thread(target=self.preload_all, daemon=True).start()
                return True
            else:
                logging.warning("Danh sách rỗng.")
                return False
        except Exception as e:
            logging.error(f"Lỗi khi tải danh sách: {e}")
            return False

    def get_random_wallpaper_url(self):
        if not self.wallpapers:
            self.fetch_list()
        if self.wallpapers:
            choices = [w for w in self.wallpapers if w != self.current_url]
            if not choices:
                choices = self.wallpapers
            chosen = random.choice(choices)
            self.current_url = chosen
            return chosen
        return None

    def preload_all(self):
        logging.info("Bắt đầu tiến trình tải sẵn toàn bộ ảnh...")
        self._notify("Đang tải trước bộ nhớ đệm...")
        import time
        for url in self.wallpapers:
            self.download_image(url, quiet=True)
            time.sleep(1)
        self._notify("Đã tải xong toàn bộ vào ổ cứng!")
        
    def download_image(self, url, quiet=False, target_dir=None):
        try:
            target_dir = target_dir or self.cache_dir
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            if '?' in filename:
                filename = filename.split('?')[0]
            if not filename or '.' not in filename:
                url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
                filename = f"image_{url_hash}.jpg"
                
            filepath = os.path.join(target_dir, filename)
            
            if os.path.exists(filepath):
                if not quiet:
                    self._notify(f"Sử dụng file sẵn có: {filename}")
                return filepath
                
            if not quiet:
                self._notify("Đang tải ảnh 4K...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
            
            if not quiet:
                self._notify("Tải ảnh thành công!")
            if target_dir == self.cache_dir:
                self._cleanup_cache()
            return filepath
        except Exception as e:
            logging.error(f"Lỗi khi tải ảnh: {e}")
            if not quiet:
                self._notify("Lỗi khi tải ảnh!")
            return None

    def set_wallpaper(self, filepath):
        try:
            abs_path = os.path.abspath(filepath)
            result = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
            if result:
                logging.info(f"Đã đặt hình nền: {abs_path}")
                import config
                import taskbar_effect
                if getattr(config, 'TASKBAR_TRANSPARENT', False):
                    taskbar_effect.set_transparent(1)
                return True
            return False
        except Exception as e:
            logging.error(f"Lỗi set hình nền: {e}")
            return False

    def next_wallpaper(self):
        url = self.get_random_wallpaper_url()
        if url:
            filepath = self.download_image(url)
            if filepath:
                return self.set_wallpaper(filepath)
        return False

    def _cleanup_cache(self):
        try:
            files = [os.path.join(self.cache_dir, f) for f in os.listdir(self.cache_dir)]
            files = [f for f in files if os.path.isfile(f)]
            files.sort(key=os.path.getctime)
            while len(files) > MAX_CACHE_FILES:
                os.remove(files.pop(0))
        except Exception as e:
            logging.error(f"Lỗi khi xoá cache: {e}")

if __name__ == "__main__":
    import sys
    if "--next" in sys.argv:
        wm = WallpaperManager()
        wm.next_wallpaper()
