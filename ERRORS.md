## [2026-04-18 10:38] - ModuleNotFoundError: 'schedule'

- **Type**: Process & Test Failure
- **Severity**: High
- **File**: main.py
- **Agent**: 123
- **Root Cause**: Quá trình pip install -r requirements.txt tru?c dó ch?y ng?m nhung b? l?i. Pillow==10.2.0 không tuong thích v?i Python 3.13 nên không th? build. Do dó, pip không cài d?t du?c các thu vi?n phía sau (trong dó có schedule).
- **Error Message**: 
  ``
  ModuleNotFoundError: No module named 'schedule'
  ``
- **Fix Applied**: S?a file equirements.txt b?ng cách g? b? phiên b?n c?ng (hard-coded versions), cho phép t?i >10.4.0 cho Pillow và cài d?t l?i b?ng dúng executable python3.13.exe.
- **Prevention**: Tránh s? d?ng version c?ng trong equirements.txt khi h? th?ng ngu?i dùng dùng Python version r?t m?i (nhu 3.13). Uu tiên toán t? >=.
- **Status**: Fixed
---
