import sys
import os
import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, QFileDialog, QSlider, QLabel, QPushButton, QComboBox, QCheckBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from datetime import datetime
import json
from mutagen.mp3 import MP3

# Инициализация pygame для работы с аудио
pygame.mixer.init()

class MP3Player(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MP3 Player with Spectrum")
        self.setGeometry(300, 300, 600, 200)
        # Инициализация переменных
        self.is_playing = False
        self.current_song = None
        self.song_list = []  # Список MP3 файлов
        self.song_info = {}  # Словарь с информацией о файле (для сортировки)
        self.folder_path = 'C:\\Users\\PC2\\Music'
        self.sort_choice = "По имени" # Переменная для хранения текущего выбора сортировки
        self.reverse_sorted  = False
        self.load_preferences()  # Загружаем выбранную сортировку из файла
        
        # Создание интерфейса
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # Создание разделителя (QSplitter) для разделения окна на две части
        splitter = QSplitter(Qt.Horizontal)

        # Левый список файлов
        self.file_list_widget = QListWidget()
        self.file_list_widget.setIconSize(QSize(10, 50))  # Размер иконок в списке
        self.file_list_widget.itemClicked.connect(self.on_file_selected)
        self.load_mp3_files()  # Загружаем файлы MP3 в список

         # Кнопки для сортировки
        sort_layout = QVBoxLayout()
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItem("По имени")
        self.sort_by_combo.addItem("По дате")
        self.sort_by_combo.addItem("По длительности")
        self.sort_by_combo.setCurrentText(self.sort_choice)  # Восстанавливаем выбранную сортировку
        self.sort_by_combo.currentIndexChanged.connect(self.sort_files)
        sort_layout.addWidget(self.sort_by_combo)
        
        # Кнопка для пересортировки
        self.sort_reverse_button = QPushButton("Реверс")
        self.sort_reverse_button.clicked.connect(self.reverse_sort)
        sort_layout.addWidget(self.sort_reverse_button)

        # Добавляем QCheckBox для отслеживания состояния переворота списка
        self.reverse_checkbox = QCheckBox("Перевернуть список")
        self.reverse_checkbox.setChecked(self.reverse_sorted)  # Восстанавливаем состояние переворота
        self.reverse_checkbox.stateChanged.connect(self.update_reverse_sorted)
        sort_layout.addWidget(self.reverse_checkbox)

        # Правый контейнер с элементами управления
        right_layout = QVBoxLayout()

        # Кнопки для воспроизведения/паузы (внизу по центру)
        self.play_button = QPushButton()
        self.play_button.setIcon(QIcon(r'src\icon\play_icon.png'))  # Убедитесь, что иконки существуют
        self.play_button.clicked.connect(self.toggle_play)
        self.play_button.setIconSize(QSize(25, 25))  # Размер иконки

        self.pause_button = QPushButton()
        self.pause_button.setIcon(QIcon(r'src\icon\pause_icon.png'))  # Убедитесь, что иконки существуют
        self.pause_button.clicked.connect(self.toggle_play)
        self.pause_button.setIconSize(QSize(25, 25))  # Размер иконки


        # Слайдер для регулировки громкости
        self.volume_label = QLabel("Громкость:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)  # Начальная громкость на 100%
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        # Добавляем элементы управления в правую часть
        right_layout.addWidget(self.sort_by_combo)
        right_layout.addWidget(self.sort_reverse_button)
        right_layout.addWidget(self.play_button)
        right_layout.addWidget(self.volume_label)
        right_layout.addWidget(self.volume_slider)
        
        

        sort_layout.addWidget(self.file_list_widget)
        splitter.addWidget(self.file_list_widget)

        # Добавляем левую и правую части в splitter
        splitter.addWidget(self.file_list_widget)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_preferences(self):
        """Загружает настройки (сортировка и перевернутый список) из файла."""
        try:
            with open('preferences.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sort_choice = data.get('sort_choice', self.sort_choice)
                self.reverse_sorted = data.get('reverse_sorted', self.reverse_sorted)
                print(self.sort_choice, self.reverse_sorted)
        except FileNotFoundError:
            # Если файл не найден, устанавливаем значения по умолчанию
            self.sort_choice = 'По имени'
            self.reverse_sorted = False

    def save_preferences(self):
        """Сохраняет настройки (сортировка и перевернутый список) в файл."""
        with open('preferences.json', 'w', encoding='utf-8') as f:
            json.dump({
                'sort_choice': self.sort_choice,
                'reverse_sorted': self.reverse_sorted
            }, f)

 
    def load_mp3_files(self):
        """Загружает все MP3 файлы из папки."""
          # Укажите путь к папке с MP3 файлами
        if not os.path.exists(self.folder_path):
            print("Папка не существует")
            return
        
        # Получаем список файлов в папке
        for file_name in os.listdir(self.folder_path):
            if file_name.endswith(".mp3") or file_name.endswith(".MP3"):
                file_path = os.path.join(self.folder_path, file_name)
                file_info = os.stat(file_path)
                file_date = datetime.fromtimestamp(file_info.st_mtime)
                # Добавляем информацию о файле для дальнейшей сортировки
                self.song_info[file_name] = {'path': file_path, 'date': file_date, 'duration': self.get_mp3_duration(file_path)}
                self.song_list.append(file_name)

        self.update_file_list()

    def get_mp3_duration(self, file_path):
        """Возвращает длительность MP3 файла в секундах."""
        try:
            audio = MP3(file_path)
            return audio.info.length 
        except Exception as e:
            print(f"Не удалось получить длительность файла {file_path}: {e}")
            return 0


    def update_file_list(self):
        """Обновляет отображаемый список файлов."""
        self.file_list_widget.clear()
        for song in self.song_list:
            self.file_list_widget.addItem(song)

    def sort_files(self):
        """Сортирует файлы по выбранному атрибуту."""
        self.sort_choice = self.sort_by_combo.currentText()
        self.save_preferences()


        if self.sort_choice == "По имени":
            self.song_list.sort()
        elif self.sort_choice == "По дате":
            # Сортировка по дате изменения
            self.song_list.sort(key=lambda song: self.song_info[song]['date'])
        elif self.sort_choice == "По длительности":
            self.song_list.sort(key=lambda song: self.song_info[song]['duration'])

        # Если список перевернут, инвертируем его
        if self.reverse_sorted:
            self.song_list.reverse()

        self.update_file_list()

    def reverse_sort(self):
        """Пересортировать (реверсировать) файлы по текущему порядку."""
        self.reverse_sorted = not self.reverse_sorted  # Переключаем состояние переворота
        self.reverse_checkbox.setChecked(self.reverse_sorted)  # Обновляем состояние флажка
        self.save_preferences()  # Сохраняем предпочтения
        self.sort_files()  # Пересортируем список с учетом нового состояния переворота

    def update_reverse_sorted(self):
        """Обновляет состояние переменной переворота при изменении флажка."""
        self.reverse_sorted = self.reverse_checkbox.isChecked()
        self.save_preferences()  # Сохраняем предпочтения
        self.sort_files()  # Пересортируем список с учетом нового состояния переворота

    def on_file_selected(self, item):
        """Обработчик выбора файла из списка."""
        self.current_song = item.text()
        pygame.mixer.music.load(self.song_info[self.current_song]['path'])

    def toggle_play(self):
        """Переключение между воспроизведением и паузой."""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.play_button.setIcon(QIcon(r'src\icon\play_icon.png'))  # Иконка Play
            self.pause_button.setIcon(QIcon(r'src\icon\pause_icon.png'))  # Иконка Pause
        else:
            pygame.mixer.music.play()
            self.play_button.setIcon(QIcon(r'src\icon\pause_icon.png'))  # Иконка Pause
            self.pause_button.setIcon(QIcon(r'src\icon\play_icon.png'))  # Иконка Play
        self.is_playing = not self.is_playing

    def set_volume(self):
        """Регулировка громкости воспроизведения."""
        volume = self.volume_slider.value() / 100
        pygame.mixer.music.set_volume(volume)
        
# Основной цикл приложения
if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MP3Player()
    player.show()
    sys.exit(app.exec_())
