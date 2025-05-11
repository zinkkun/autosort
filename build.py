import PyInstaller.__main__
import os

# 아이콘 파일이 있는지 확인
icon_path = 'icon.ico'
if not os.path.exists(icon_path):
    print('경고: icon.ico 파일이 없습니다. 기본 아이콘이 사용됩니다.')

PyInstaller.__main__.run([
    'autosort.py',
    '--onefile',
    '--windowed',
    '--name=AutoSort',
    '--icon=' + icon_path if os.path.exists(icon_path) else '',
    '--add-data=icon.png;.' if os.path.exists('icon.png') else '',
    '--hidden-import=PyQt5',
    '--hidden-import=watchdog',
    '--clean',
    '--noconfirm'
]) 