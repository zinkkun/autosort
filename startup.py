import os
import sys
import winreg

def add_to_startup():
    # 실행 파일 경로
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 경우
        exe_path = sys.executable
    else:
        # 개발 중인 경우
        exe_path = os.path.abspath('autosort.py')
    
    # 시작 프로그램 레지스트리 키
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Run',
        0, winreg.KEY_SET_VALUE
    )
    
    try:
        winreg.SetValueEx(key, 'AutoSort', 0, winreg.REG_SZ, exe_path)
        return True
    except WindowsError:
        return False
    finally:
        winreg.CloseKey(key)

def remove_from_startup():
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Run',
        0, winreg.KEY_SET_VALUE
    )
    
    try:
        winreg.DeleteValue(key, 'AutoSort')
        return True
    except WindowsError:
        return False
    finally:
        winreg.CloseKey(key)

def is_in_startup():
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Run',
        0, winreg.KEY_READ
    )
    
    try:
        winreg.QueryValueEx(key, 'AutoSort')
        return True
    except WindowsError:
        return False
    finally:
        winreg.CloseKey(key) 