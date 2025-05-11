from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QPushButton, QListWidget, QFileDialog)

class RuleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('규칙 추가')
        self.setGeometry(200, 200, 500, 400)
        
        layout = QVBoxLayout()
        
        # 포함 키워드
        layout.addWidget(QLabel('포함 키워드 (쉼표로 구분):'))
        self.include_keywords = QLineEdit()
        layout.addWidget(self.include_keywords)
        
        # 제외 키워드
        layout.addWidget(QLabel('제외 키워드 (쉼표로 구분):'))
        self.exclude_keywords = QLineEdit()
        layout.addWidget(self.exclude_keywords)
        
        # 대상 폴더
        folder_layout = QHBoxLayout()
        self.target_dir = QLineEdit()
        folder_layout.addWidget(self.target_dir)
        browse_btn = QPushButton('찾아보기')
        browse_btn.clicked.connect(self.browse_target_dir)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)
        
        # 버튼
        button_layout = QHBoxLayout()
        ok_button = QPushButton('확인')
        cancel_button = QPushButton('취소')
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def browse_target_dir(self):
        folder = QFileDialog.getExistingDirectory(self, '대상 폴더 선택')
        if folder:
            self.target_dir.setText(folder)
            
    def get_rule(self):
        include = [k.strip() for k in self.include_keywords.text().split(',') if k.strip()]
        exclude = [k.strip() for k in self.exclude_keywords.text().split(',') if k.strip()]
        return {
            'include_keywords': include,
            'exclude_keywords': exclude,
            'target_dir': self.target_dir.text()
        } 