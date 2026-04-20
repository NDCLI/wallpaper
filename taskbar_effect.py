import ctypes
import traceback

class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId", ctypes.c_int)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENT_POLICY)),
        ("SizeOfData", ctypes.c_size_t)
    ]

def set_transparent(mode=1):
    """
    Sử dụng Undocumented API SetWindowCompositionAttribute để ép Windows gỡ bỏ nền.
    mode 1: Tàng hình hoàn toàn (Clear 100%)
    mode 2: Kính mờ (Blur/Acrylic)
    mode 0: Tắt (Để Windows tự lo)
    """
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW("Shell_TrayWnd", None)
        if not hwnd:
            return False

        policy = ACCENT_POLICY()
        
        if mode == 1:
            policy.AccentState = 2 # ACCENT_ENABLE_TRANSPARENTGRADIENT
            policy.AccentFlags = 2
            # 0x00000000 là trong suốt tuyệt đối (100% Clear)
            policy.GradientColor = 0x00000000
        elif mode == 2:
            policy.AccentState = 3 # ACCENT_ENABLE_BLURBEHIND
            policy.AccentFlags = 2
            policy.GradientColor = 0x00000000
        else:
            policy.AccentState = 0 # ACCENT_DISABLED (Default)

        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19 # WCA_ACCENT_POLICY
        data.Data = ctypes.pointer(policy)
        data.SizeOfData = ctypes.sizeof(policy)

        user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
        
        return True
    except Exception:
        return False

if __name__ == "__main__":
    import sys
    if "--clear" in sys.argv:
        set_transparent(1)
    elif "--blur" in sys.argv:
        set_transparent(2)
    elif "--off" in sys.argv:
        set_transparent(0)
