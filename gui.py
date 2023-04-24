import json
import os
# import urllib

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QButtonGroup, QMessageBox

from converter import Converter
from download_site import collect_data
from parse_site import get_properties
from utils import parse_url


class Ui_Dialog(object):

    def __init__(self):
        self.available_site = []

    def ask_folder_site(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(None, "Select Txt", "", "Txt Files (*.txt)")[0]
        self.file_name.setText(file_name)

    def event_get_site(self):
        sites = self.read_txt(self.file_name.text())
        if len(sites) == 0:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Список сайтов пуст\nНажмите ОК, чтобы закрыть")
            error.setIcon(QMessageBox.Warning)
            error.exec_()
        else:
            info = QMessageBox()
            info.setWindowTitle("Скачивание сайтов")
            time = len(sites) * 30
            info.setText("Примерное время скачивания: " + str(time) + "мин. Нажмите ОК для начала загрузки!")
            info.setIcon(QMessageBox.Warning)
            info.exec_()
            self.available_site = []
            for site in sites:
                protocol, domain, path = parse_url(site)
                flag_available = False
                if len(protocol) > 0 and len(domain):
                    flag_available = True
                    site = protocol + domain + path
                if flag_available:
                    print(site + ": Сайт введен корректно")
                    self.available_site.append(site)
                else:
                    print(site + ": Нет доступа к сайту. Проверьте корректность ссылки")
            for site in self.available_site:
                collect_data(site)

    def read_txt(self, txt_file_with_site):
        if len(txt_file_with_site) == 0:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Сначала выберите файл со списком сайтов!")
            error.setIcon(QMessageBox.Warning)
            error.exec_()
            return []
        else:
            file = open(txt_file_with_site, "r")
            sites = []
            try:
                while True:
                    site = file.readline()
                    if not site:
                        break
                    else:
                        sites.append(site.strip())
            finally:
                file.close()
            return sites

    def event_parse(self):
        info = QMessageBox()
        info.setWindowTitle("Парсинг")
        info.setText("Нажмите ОК,чтобы начать парсинг выгруженных сайтов.")
        info.exec_()
        if not os.path.exists("data"):
            os.mkdir("data")

        version = 0
        out_filename = os.path.join("data", "catalog")
        while os.path.exists(f"{out_filename}_v{version}.json"):
            version += 1

        sites = self.read_txt(self.file_name.text())
        sites = [parse_url(site)[1] for site in sites]
        sites = [site for site in sites if os.path.isdir(site)]

        # print(*sites, sep="\n")

        with open("data\\version.json", 'w') as f:
            json.dump({"version": version}, f)

        data = get_properties(sites)
        with open(f"{out_filename}_v{version}.json", 'w') as f:
            json.dump(data, f)

        print(f"Данные успешно собраны и сохранены в файл: {out_filename}_v{version}.json")
        print("parse")

    def event_convert(self):
        info = QMessageBox()
        info.setWindowTitle("Конвертация")
        info.setText("Подождите, идет конвертация файлов в Excel")
        json_file = ""
        if self.old_ver.isChecked():
            json_file = QtWidgets.QFileDialog.getOpenFileName(None, "Select JSON", "", "JSON Files (*.json)")[0]

        if self.new_ver.isChecked():
            with open("data/version.json", 'r', encoding='utf-8') as inputFile:
                parse_text = json.load(inputFile)
            json_file = "data/catalog_v" + str(parse_text['version']) + ".json"
        convert = Converter(json_file, "База_данных_")
        convert.run()
        info.exec_()


    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(312, 300)

        self.choose_file = QtWidgets.QPushButton(Dialog)
        self.choose_file.setGeometry(QtCore.QRect(20, 20, 271, 23))
        self.choose_file.setObjectName("choose_file")
        self.choose_file.setCheckable(True)
        self.choose_file.clicked.connect(self.ask_folder_site)

        self.file_name = QtWidgets.QLineEdit(Dialog)
        self.file_name.setGeometry(QtCore.QRect(120, 50, 171, 20))
        self.file_name.setAutoFillBackground(False)
        self.file_name.setReadOnly(True)
        self.file_name.setObjectName("file_name")

        self.file_name_lb = QtWidgets.QLabel(Dialog)
        self.file_name_lb.setGeometry(QtCore.QRect(20, 50, 101, 16))
        self.file_name_lb.setObjectName("file_name_lb")

        self.get_sites = QtWidgets.QPushButton(Dialog)
        self.get_sites.setGeometry(QtCore.QRect(20, 90, 271, 23))
        self.get_sites.setObjectName("get_sites")
        self.get_sites.setCheckable(True)
        self.get_sites.clicked.connect(self.event_get_site)

        self.parse_sites = QtWidgets.QPushButton(Dialog)
        self.parse_sites.setGeometry(QtCore.QRect(20, 130, 271, 23))
        self.parse_sites.setObjectName("parse_sites")
        self.parse_sites.setCheckable(True)
        self.parse_sites.clicked.connect(self.event_parse)

        self.work_excel = QtWidgets.QGroupBox(Dialog)
        self.work_excel.setGeometry(QtCore.QRect(10, 160, 291, 80))
        self.work_excel.setObjectName("work_excel")

        self.get_excel = QtWidgets.QPushButton(self.work_excel)
        self.get_excel.setGeometry(QtCore.QRect(10, 20, 271, 23))
        self.get_excel.setObjectName("get_excel")
        self.get_excel.setCheckable(True)
        self.get_excel.clicked.connect(self.event_convert)

        self.old_ver = QtWidgets.QRadioButton(self.work_excel)
        self.old_ver.setGeometry(QtCore.QRect(10, 50, 141, 17))
        self.old_ver.setChecked(True)
        self.old_ver.setObjectName("old_ver")

        self.new_ver = QtWidgets.QRadioButton(self.work_excel)
        self.new_ver.setGeometry(QtCore.QRect(160, 50, 121, 17))
        self.new_ver.setChecked(False)
        self.new_ver.setObjectName("new_ver")

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.old_ver)
        self.button_group.addButton(self.new_ver)

        self.line_1 = QtWidgets.QFrame(Dialog)
        self.line_1.setGeometry(QtCore.QRect(10, 240, 291, 16))
        self.line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_1.setObjectName("line_1")
        self.line_2 = QtWidgets.QFrame(Dialog)
        self.line_2.setGeometry(QtCore.QRect(10, 70, 291, 16))
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Парсер Базы данных"))
        self.choose_file.setText(_translate("Dialog", "Выберите файл с перечнем сайтов"))
        self.file_name.setText(_translate("Dialog", ""))
        self.file_name_lb.setText(_translate("Dialog", "Выбранный файл:"))
        self.get_sites.setText(_translate("Dialog", "Выгрузить сайты из списка"))
        self.parse_sites.setText(_translate("Dialog", "Парсинг загруженных сайтов"))
        self.work_excel.setTitle(_translate("Dialog", "Excel"))
        self.get_excel.setText(_translate("Dialog", "Получить таблицу Excel"))
        self.old_ver.setText(_translate("Dialog", "Выбрать ранние версии"))
        self.new_ver.setText(_translate("Dialog", "Последняя версия"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    Dialog.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
