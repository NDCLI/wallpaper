import os

# Đường dẫn file danh sách (Bây giờ hỗ trợ cả link online HOẶC file txt cục bộ)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ONLINE_LIST_URL = os.path.join(BASE_DIR, "wallpapers.txt")

# Thư mục lưu cấu hình và cache
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".oc_wallpaper_cache")
# Thư mục thư viện ảnh người dùng tải về
LIBRARY_DIR = os.path.join(os.path.expanduser("~"), "Pictures", "OC_Wallpaper_Library")

# API Keys (Người dùng cần điền key của mình vào đây)
# Register at: https://www.pexels.com/api/
PEXELS_API_KEY = "aKXop4NFvGrvJIF5k1zA2LOjYolXPIz6GR7bVcRF4TOfHJzjTS69eWQi" 
# Register at: https://unsplash.com/developers
UNSPLASH_ACCESS_KEY = "ZgGs_ainQ2SWczyrPJFH-NJ4ABCIV8kWpBeu2_n87sA"

# Chu kỳ thay đổi hình nền (phút)
UPDATE_INTERVAL_MINUTES = 1

# Số lượng file tối đa trong cache
MAX_CACHE_FILES = 50

# Cấu hình hiển thị
THUMBNAIL_SIZE = (280, 180)

# Taskbar trong suốt
TASKBAR_TRANSPARENT = True
