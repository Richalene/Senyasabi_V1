import os

with open('senyasabi/screens/dashboard/dashboard.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_imp = '''from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget'''
new_imp = '''import os
from PySide6.QtGui import QCloseEvent, QFontDatabase
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget'''

assert old_imp in code, 'old_imp not found'
code = code.replace(old_imp, new_imp, 1)

font_func = '''

def _ensure_cherry_bomb_font():
    font_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "resources", "font", "CherryBombOne-Regular.ttf"
    )
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)
'''

code = code.replace('from backend import auth_service, dashboard_service', 'from backend import auth_service, dashboard_service' + font_func, 1)

old_init = '''        self.ui = Ui_Dashboard()
        self.ui.setupUi(self)
        self.ui.titlePanel.resize(300, 60)
        self.ui.btnBack.setGeometry(1280, 150, 110, 42)
        self.ui.btnBack = BackButton.replace(self.ui.btnBack)
        self.ui.streakPanel.hide()
        self.ui.lblCurrentStreak.setObjectName("replacedCurrentStreak")
        self.ui.btnMenu.hide()
        self.ui.btnMenu.setEnabled(False)
        self.ui.btnMenu.setObjectName("replacedMenu")
        self.header = SenyaSabiHeader(self)
        self.header.anchor_to_canvas(self.size())
        install_page_menu(self, header=self.header)
        self.ui.lblCurrentStreak = self.header.streak_label
        self.ui.btnMenu = self.header.menu_button
        self.ui.lblCurrentStreak.setObjectName("lblCurrentStreak")
        self.ui.btnMenu.setObjectName("btnMenu")
        self.ui.badgeCard.resize(240, 180)
        self.ui.badgeTitle.setGeometry(9, 67, 220, 24)
        self.ui.lblLatestBadge.setGeometry(9, 100, 220, 60)
        self.ui.lblLatestBadge.setWordWrap(True)
        icons = {'quizImage': '?', 'lessonsImage': 'Aa', 'modulesImage': '10',
                 'leaderboardImage': '1', 'minigamesImage': 'Play', 'badgeImage': '★'}
        for name, text in icons.items():
            label = getattr(self.ui, name)
            label.setText(text)
            label.setToolTip('')
        self.ui.imgStatsChart.setText('Your progress will appear here as you complete learning activities.')
        self.ui.imgStatsChart.setWordWrap(True)
        for name in ('legendDot1', 'legendDot2', 'legendDot3', 'legendDot4', 'legendDot5', 'legendDot6'):
            getattr(self.ui, name).hide()'''

new_init = '''        _ensure_cherry_bomb_font()
        self.ui = Ui_Dashboard()
        self.ui.setupUi(self)
        self.ui.titlePanel.hide()
        self.ui.btnBack = BackButton.replace(self.ui.btnBack)
        self.ui.streakPanel.hide()
        self.ui.lblCurrentStreak.setObjectName("replacedCurrentStreak")
        self.ui.btnMenu.hide()
        self.ui.btnMenu.setEnabled(False)
        self.ui.btnMenu.setObjectName("replacedMenu")
        self.header = SenyaSabiHeader(self)
        self.header.anchor_to_canvas(self.size())
        install_page_menu(self, header=self.header)
        self.ui.lblCurrentStreak = self.header.streak_label
        self.ui.btnMenu = self.header.menu_button
        self.ui.lblCurrentStreak.setObjectName("lblCurrentStreak")
        self.ui.btnMenu.setObjectName("btnMenu")
        self.ui.lblLatestBadge.setWordWrap(True)'''

assert old_init in code, 'old_init not found'
code = code.replace(old_init, new_init, 1)

old_render = '''        completed_count = max(stats.get("lessons_completed", 0), lp_completed)
        self.ui.lblLessonsCompleted.setText(str(completed_count))'''
new_render = '''        completed_count = max(stats.get("lessons_completed", 0), lp_completed)
        self.ui.lblLessonsCompleted.setText(f"{completed_count}/7")'''
assert old_render in code, 'old_render not found'
code = code.replace(old_render, new_render, 1)

old_dash_init = '''        self.ui = Ui_main()
        self.ui.setupUi(self)'''
new_dash_init = '''        _ensure_cherry_bomb_font()
        self.ui = Ui_main()
        self.ui.setupUi(self)'''
assert old_dash_init in code, 'old_dash_init not found'
code = code.replace(old_dash_init, new_dash_init, 1)

old_home_render = '''        completed_count = max(stats.get("lessons_completed", 0), lp_completed)
        self.ui.lblLessonsCompleted.setText(str(completed_count))'''
new_home_render = '''        completed_count = max(stats.get("lessons_completed", 0), lp_completed)
        self.ui.lblLessonsCompleted.setText(f"{completed_count}/7")'''
assert old_home_render in code, 'old_home_render not found'
code = code.replace(old_home_render, new_home_render, 1)

with open('senyasabi/screens/dashboard/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('dashboard.py successfully updated.')

