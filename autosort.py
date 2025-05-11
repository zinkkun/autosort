import sys
import os
import json
import shutil
import logging
import time
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                           QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit,
                           QListWidget, QMessageBox, QFileDialog, QHBoxLayout,
                           QCheckBox, QDialog)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rule_dialog import RuleDialog
from startup import add_to_startup, remove_from_startup, is_in_startup

# 로깅 설정
logging.basicConfig(
    filename='autosort.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_resource_path(relative_path):
    """리소스 파일의 절대 경로를 반환합니다."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class Config:
    def __init__(self):
        self.settings = QSettings('AutoSort', 'AutoSort')
        self.watch_folders = self.settings.value('watch_folders', [])
        self.rules = self.settings.value('rules', [])
        self.startup = self.settings.value('startup', False, type=bool)
        # 규칙 리스트 타입 보정
        for rule in self.rules:
            if 'include_keywords' in rule and not isinstance(rule['include_keywords'], list):
                rule['include_keywords'] = [k.strip() for k in str(rule['include_keywords']).split(',') if k.strip()]
            if 'exclude_keywords' in rule and not isinstance(rule['exclude_keywords'], list):
                rule['exclude_keywords'] = [k.strip() for k in str(rule['exclude_keywords']).split(',') if k.strip()]
        
    def save(self):
        self.settings.setValue('watch_folders', self.watch_folders)
        self.settings.setValue('rules', self.rules)
        self.settings.setValue('startup', self.startup)
        
    def add_watch_folder(self, folder):
        if folder not in self.watch_folders:
            self.watch_folders.append(folder)
            self.save()
            
    def remove_watch_folder(self, folder):
        if folder in self.watch_folders:
            self.watch_folders.remove(folder)
            self.save()
            
    def add_rule(self, rule):
        self.rules.append(rule)
        self.save()
        
    def remove_rule(self, index):
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
            self.save()

class FileHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        
    def on_created(self, event):
        if event.is_directory:
            # 폴더 생성 후 여러 번 내부 파일 스캔
            for _ in range(3):
                time.sleep(0.5)
                for root, dirs, files in os.walk(event.src_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        self._process_file(file_path)
            return
        self._process_file(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            # 폴더 이동 후 여러 번 내부 파일 스캔
            for _ in range(3):
                time.sleep(0.5)
                for root, dirs, files in os.walk(event.dest_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        self._process_file(file_path)
            return
        self._process_file(event.dest_path)

    def _process_file(self, file_path):
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        logging.info(f"파일 감지: {file_path} (확장자: {file_ext})")
        if file_ext not in ['.stl', '.pts', '.stl.nested']:
            logging.info(f"지원하지 않는 확장자: {file_ext}")
            return

        # 1. 모든 규칙의 제외 키워드를 한 번에 모아서 검사 (for문으로 하나씩 검사)
        all_exclude_keywords = []
        for rule in self.config.rules:
            all_exclude_keywords += [k.strip().lower() for k in rule.get('exclude_keywords', []) if k.strip()]
        file_name_l = file_name.lower()
        file_path_l = file_path.lower()
        for keyword in all_exclude_keywords:
            if keyword in file_name_l or keyword in file_path_l:
                logging.info(f"최상위 제외 키워드 '{keyword}'에 걸려 복사하지 않음: {file_path}")
                return

        # 2. 포함 키워드가 있는 규칙들만 따로 추출
        include_rules = [rule for rule in self.config.rules if rule.get('include_keywords') and any(k.strip() for k in rule.get('include_keywords', []))]
        for rule in include_rules:
            if self._match_rule(file_name, rule, file_path=file_path):
                target_dir = rule['target_dir']
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                shutil.copy2(file_path, os.path.join(target_dir, file_name))
                logging.info(f"복사 완료(포함키워드): {file_path} -> {os.path.join(target_dir, file_name)}")
                return

        # 3. 포함/제외 키워드 모두 없는(기본) 규칙 적용
        for rule in self.config.rules:
            if (not rule.get('include_keywords') or not any(k.strip() for k in rule.get('include_keywords', []))) and (not rule.get('exclude_keywords') or not any(k.strip() for k in rule.get('exclude_keywords', []))):
                target_dir = rule['target_dir']
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                shutil.copy2(file_path, os.path.join(target_dir, file_name))
                logging.info(f"복사 완료(기본): {file_path} -> {os.path.join(target_dir, file_name)}")
                return

    def _match_exclude(self, file_name, rule, file_path=None):
        exclude_keywords = [k.strip().lower() for k in rule.get('exclude_keywords', []) if k.strip()]
        file_name_l = file_name.lower()
        file_path_l = file_path.lower() if file_path else ''
        if exclude_keywords:
            if any(keyword in file_name_l for keyword in exclude_keywords):
                return True
            if file_path and any(keyword in file_path_l for keyword in exclude_keywords):
                return True
        return False

    def _match_rule(self, file_name, rule, file_path=None):
        include_keywords = [k.strip().lower() for k in rule.get('include_keywords', []) if k.strip()]
        exclude_keywords = [k.strip().lower() for k in rule.get('exclude_keywords', []) if k.strip()]
        file_name_l = file_name.lower()
        file_path_l = file_path.lower() if file_path else ''
        logging.info(f"파일명: {file_name_l}, 포함키워드: {include_keywords}, 제외키워드: {exclude_keywords}, 경로: {file_path_l}")
        if include_keywords:
            if not any(keyword in file_name_l for keyword in include_keywords):
                logging.info("포함 키워드 불일치")
                return False
        if exclude_keywords:
            if any(keyword in file_name_l for keyword in exclude_keywords):
                logging.info("제외 키워드(파일명) 일치")
                return False
            if file_path and any(keyword in file_path_l for keyword in exclude_keywords):
                logging.info("제외 키워드(경로) 일치")
                return False
        return True

class AutoSortApp(QWidget):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.init_ui()
        self.setup_tray()
        self.start_monitoring()
        
    def init_ui(self):
        self.setWindowTitle('AutoSort')
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        # 시작 프로그램 등록 체크박스
        self.startup_checkbox = QCheckBox('Windows 시작 시 자동 실행')
        self.startup_checkbox.setChecked(self.config.startup)
        self.startup_checkbox.stateChanged.connect(self.toggle_startup)
        layout.addWidget(self.startup_checkbox)
        
        # 감시 폴더 설정
        self.watch_folder_list = QListWidget()
        self.watch_folder_list.addItems(self.config.watch_folders)
        layout.addWidget(QLabel('감시 폴더:'))
        layout.addWidget(self.watch_folder_list)
        
        # 폴더 추가/제거 버튼
        folder_buttons = QHBoxLayout()
        add_folder_btn = QPushButton('폴더 추가')
        remove_folder_btn = QPushButton('폴더 제거')
        add_folder_btn.clicked.connect(self.add_watch_folder)
        remove_folder_btn.clicked.connect(self.remove_watch_folder)
        folder_buttons.addWidget(add_folder_btn)
        folder_buttons.addWidget(remove_folder_btn)
        layout.addLayout(folder_buttons)
        
        # 규칙 설정
        self.rule_list = QListWidget()
        for rule in self.config.rules:
            include_keywords = ', '.join(rule.get('include_keywords', [])) if rule.get('include_keywords', []) else '없음'
            exclude_keywords = ', '.join(rule.get('exclude_keywords', [])) if rule.get('exclude_keywords', []) else '없음'
            self.rule_list.addItem(f"포함: {include_keywords} | 제외: {exclude_keywords} -> {rule['target_dir']}")
        layout.addWidget(QLabel('규칙:'))
        layout.addWidget(self.rule_list)
        
        # 규칙 추가/제거 버튼
        rule_buttons = QHBoxLayout()
        add_rule_btn = QPushButton('규칙 추가')
        remove_rule_btn = QPushButton('규칙 제거')
        add_rule_btn.clicked.connect(self.add_rule)
        remove_rule_btn.clicked.connect(self.remove_rule)
        rule_buttons.addWidget(add_rule_btn)
        rule_buttons.addWidget(remove_rule_btn)
        layout.addLayout(rule_buttons)
        
        self.setLayout(layout)
        
    def setup_tray(self):
        try:
            self.tray_icon = QSystemTrayIcon(self)
            icon_path = get_resource_path('icon.png')
            logging.info(f"아이콘 경로: {icon_path}")
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
                logging.info("아이콘 설정 완료")
            else:
                logging.warning(f"아이콘 파일을 찾을 수 없습니다: {icon_path}")
            
            tray_menu = QMenu()
            show_action = QAction('보기', self)
            quit_action = QAction('종료', self)
            show_action.triggered.connect(self.show)
            quit_action.triggered.connect(self.quit_app)
            
            tray_menu.addAction(show_action)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            logging.info("시스템 트레이 아이콘 설정 완료")
        except Exception as e:
            logging.error(f"시스템 트레이 설정 중 오류 발생: {str(e)}")
        
    def start_monitoring(self):
        try:
            if hasattr(self, 'observer'):
                self.observer.stop()
                self.observer.join()
                
            self.observer = Observer()
            for folder in self.config.watch_folders:
                if os.path.exists(folder):
                    self.observer.schedule(FileHandler(self.config), folder, recursive=False)
                    logging.info(f"폴더 감시 시작: {folder}")
            self.observer.start()
            logging.info("파일 감시 시작")
        except Exception as e:
            logging.error(f"파일 감시 시작 중 오류 발생: {str(e)}")
        
    def add_watch_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '감시할 폴더 선택')
        if folder:
            self.config.add_watch_folder(folder)
            self.watch_folder_list.addItem(folder)
            self.start_monitoring()  # 감시 재시작
            
    def remove_watch_folder(self):
        current = self.watch_folder_list.currentRow()
        if current >= 0:
            folder = self.watch_folder_list.item(current).text()
            self.config.remove_watch_folder(folder)
            self.watch_folder_list.takeItem(current)
            self.start_monitoring()  # 감시 재시작
            
    def add_rule(self):
        dialog = RuleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            rule = dialog.get_rule()
            if rule['target_dir']:  # 대상 폴더가 선택된 경우에만 추가
                self.config.add_rule(rule)
                include_keywords = ', '.join(rule['include_keywords']) if rule['include_keywords'] else '없음'
                exclude_keywords = ', '.join(rule['exclude_keywords']) if rule['exclude_keywords'] else '없음'
                self.rule_list.addItem(f"포함: {include_keywords} | 제외: {exclude_keywords} -> {rule['target_dir']}")
        
    def remove_rule(self):
        current = self.rule_list.currentRow()
        if current >= 0:
            self.config.remove_rule(current)
            self.rule_list.takeItem(current)
            
    def quit_app(self):
        self.observer.stop()
        self.observer.join()
        QApplication.quit()
        
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def toggle_startup(self, state):
        if state == Qt.Checked:
            if add_to_startup():
                self.config.startup = True
                self.config.save()
            else:
                self.startup_checkbox.setChecked(False)
                QMessageBox.warning(self, '오류', '시작 프로그램 등록에 실패했습니다.')
        else:
            if remove_from_startup():
                self.config.startup = False
                self.config.save()
            else:
                self.startup_checkbox.setChecked(True)
                QMessageBox.warning(self, '오류', '시작 프로그램 제거에 실패했습니다.')

if __name__ == '__main__':
    try:
        logging.info("프로그램 시작")
        app = QApplication(sys.argv)
        ex = AutoSortApp()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        raise 
        raise 