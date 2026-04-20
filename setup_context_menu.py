import winreg
import os
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def setup_context_menu():
    # Sử dụng pythonw để chạy không hiển thị cửa sổ console
    pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pythonw_exe):
        pythonw_exe = sys.executable
    
    script_path = os.path.abspath("wallpaper_manager.py")
    
    # Context menu dưới Desktop
    key_path = r"DesktopBackground\Shell\OCWallpaper"
    
    print("\n[+] Đang cấu hình Windows Registry...")
    try:
        # Setup the UI button
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path)
        winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Next wallpaper")
        # Sử dụng icon mặc định của Windows (image frame) để đẹp hơn
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, "imageres.dll,-103")
        winreg.CloseKey(key)
        
        # Thiết lập lệnh sẽ chạy (command hook)
        command_key_path = key_path + r"\command"
        cmd_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_key_path)
        cmd_val = f'"{pythonw_exe}" "{script_path}" --next'
        winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, cmd_val)
        winreg.CloseKey(cmd_key)
        
        print(f"✅ Đã thêm THÀNH CÔNG nút Đổi hình nền (Next) vào chuột phải ở Desktop!")
        print(f"ℹ Lệnh thực thi đã cấu hình: {cmd_val}")
    except Exception as e:
        print(f"❌ Lỗi khi ghi vào Registry: {e}")
        
def remove_context_menu():
    key_path = r"DesktopBackground\Shell\OCWallpaper"
    print("\n[-] Đang xoá cấu hình Windows Registry...")
    try:
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path + r"\command")
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
        print("✅ Đã xoá thành công nút bấm khỏi cửa sổ Desktop!")
    except FileNotFoundError:
        print("✅ Không tìm thấy cài đặt trên hệ thống, không cần gỡ bỏ.")
    except Exception as e:
        print(f"❌ Lỗi khi xoá Registry (có thể đã gỡ bỏ): {e}")

if __name__ == "__main__":
    if sys.version_info[0] < 3:
        print("Requieres python 3")
        sys.exit()

    if not is_admin():
        print("❌ BẠN CHƯA CẤP QUYỀN ADMINISTRATOR!")
        print("Registry là hệ thống lõi. Hãy tắt cửa sổ hiện tại, bấm phím Win (Cửa sổ), gõ 'Powershell', chọn 'Run as Administrator'.")
        print("Sau đó dùng lệnh: cd đường_dẫn_thư_mục_này và gõ: python setup_context_menu.py")
        input("Nhấn Enter để thoát...")
        sys.exit(1)
        
    print("=== CÀI ĐẶT MENU CHUỘT PHẢI (DESKTOP) ===")
    print("1. Cài đặt nút 'Đổi hình nền' ra Desktop")
    print("2. Gỡ bỏ nút Desktop")
    print("------------------------------------------")
    try:
        choice = input("Nhập tuỳ chọn của bạn (1 hoặc 2): ")
        if choice == '1':
            setup_context_menu()
        elif choice == '2':
            remove_context_menu()
        else:
            print("Lựa chọn không hợp lệ.")
    except KeyboardInterrupt:
        pass
    input("\nNhấn Enter để thoát...")
