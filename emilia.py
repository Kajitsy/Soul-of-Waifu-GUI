import os
import asyncio
import threading
import torch
import time
import zipfile, requests
import re
import json
import sys
import webbrowser
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('emilia.app')
import pyvts, random
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import sounddevice as sd
import google.generativeai as genai
import speech_recognition as sr
from gpytranslate import Translator
from characterai import aiocai, sendCode, authUser
from num2words import num2words
from PyQt6.QtWidgets import QComboBox, QCheckBox, QHBoxLayout, QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QPalette
from PyQt6.QtCore import QLocale

ver = "2.2"
build = "20240609"
pre = True
if pre == True:
    version = "pre" + ver
else:
    version = ver
local_file = 'voice.pt'
sample_rate = 48000
put_accent = True
put_yo = True

def writeconfig(variable, value, configfile = 'config.json'):
        try:
            with open(configfile, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        data.update({variable: value})
        with open(configfile, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def getconfig(value, def_value = "", configfile = 'config.json'):
    if os.path.exists(configfile):
        with open(configfile, 'r') as configfile:
            config = json.load(configfile)
            return config.get(value, def_value)
    else:
        return def_value

# Global Variables
autoupdate_enable = getconfig('autoupdate_enable', 'True')
lang = getconfig('language', QLocale.system().name())
aitype = getconfig('aitype', 'charai')
vtubeenable = getconfig('vtubeenable', "False")
torchdevice = getconfig('devicefortorch', 'cuda')
theme = getconfig('theme')
if theme == "dark":
    theme = 'Fusion'
else:
    theme = 'windowsvista'
backcolor = getconfig('backgroundcolor')
buttoncolor = getconfig('buttoncolor')
buttontextcolor = getconfig('buttontextcolor')
labelcolor = getconfig('labelcolor')

# Icons
if pre == True:
    emiliaicon = './images/premilia.png'
else:
    emiliaicon = './images/emilia.png'
googleicon = './images/google.png'
charaiicon = './images/charai.png'
refreshicon = './images/refresh.png'
if theme == 'Fusion':
    githubicon = './images/github_white.png'
    changelang = './images/change_language_white.png'
    keyboardicon = './images/keyboard_white.png'
    inputicon = './images/input_white.png'
    charediticon = './images/open_char_editor_white.png'
else:
    githubicon = './images/github.png'
    changelang = './images/change_language.png'
    keyboardicon = './images/keyboard.png'
    inputicon = './images/input.png'
    charediticon = './images/open_char_editor.png'

if not os.path.exists('voice.pt'):
    if lang == "ru_RU":
        print("Идёт загрузка модели SileroTTS RU")
        print("")
        try:
            torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt', "voice.pt")
        except:
            torch.hub.download_url_to_file('https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/tts_models/v4_ru.pt', "voice.pt")
        print("_____________________________________________________")
        print("ГОТОВО, ПРОСТИТЕ")
    else:
        print("The SileroTTS EN model is being loaded")
        print("")
        try:
            torch.hub.download_url_to_file('https://models.silero.ai/models/tts/en/v3_en.pt', "voice.pt")
        except:
            torch.hub.download_url_to_file('https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/tts_models/v3_en.pt', "voice.pt")
        print("_____________________________________________________")
        print("DONE, SORRY")

def load_translations(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Translation file not found: {filename}\nUsing en_US.json")
        with open("locales/en_US.json", "r", encoding="utf-8") as f:
            return json.load(f)

def tr(context, text):
    if context in translations and text in translations[context]:
        return translations[context][text]
    else:
        return text

translations = load_translations(f"locales/{lang}.json")

class EEC():
    """
    EMC - Emilia Emotes Core
    """

    plugin_info = {
        "plugin_name": "Emilia VTube",
        "developer": "kajitsy",
        "authentication_token_path": "./token.txt"
    }

    myvts = pyvts.vts(plugin_info)

    async def VTubeConnect(self):
        """
        Подключение к Vtube Studio
        """
        try:
            await self.myvts.connect()
            try:
                await self.myvts.read_token()
                await self.myvts.request_authenticate()
            except:
                await self.myvts.request_authenticate_token()
                await self.myvts.write_token()
                await self.myvts.request_authenticate()
            self.myvts.load_icon(emiliaicon)
        except:
            writeconfig('vtubeenable', 'False')

    async def SetCustomParameter(self, name, value=50, min=-100, max=100):
        """
        Лучше всего использовать для создания параметров плагина

        CustomParameter("EmiEyeX", -100, 100, 0)
        """

        try:
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(name, min, max, value)
            )
        except:
            await self.VTubeConnect()
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(name, min, max, value)
            )
        await self.myvts.close()

    async def DelCustomParameter(self, name):
        """
        Лучше всего использовать для создания параметров плагина

        CustomParameter("EmiEyeX", -100, 100, 0)
        """

        try:
            await self.myvts.request(
                self.myvts.vts_request.requestDeleteCustomParameter(name)
            )
        except:
            await self.VTubeConnect()
            await self.myvts.request(
                self.myvts.vts_request.requestDeleteCustomParameter(name)
            )
        await self.myvts.close()

    def RandomBetween(self, a, b):
        """
        Просто случайное число, не более.

        RandomBetween(-90, -75)
        """
        return random.randint(a, b)

    async def AddVariables(self):
        """
        Создаёт все нужные переменные
        """

        parameters = ["EmiFaceAngleX", "EmiFaceAngleY", "EmiFaceAngleZ",
                      "EmiEyeOpenLeft", "EmiEyeOpenRight",
                      "EmiEyeX", "EmiEyeY", "EmiMountSmile", "EmiMountX"]
        for param in parameters:
            await self.SetCustomParameter(param)

    async def DelVariables(self):
        """
        Удаляет все нужные переменные
        """

        parameters = ["EmiFaceAngleX", "EmiFaceAngleY", "EmiFaceAngleZ",
                      "EmiEyeOpenLeft", "EmiEyeOpenRight",
                      "EmiEyeX", "EmiEyeY", "EmiMountSmile", "EmiMountX"]
        for param in parameters:
            await self.DelCustomParameter(param)

    async def UseEmote(self, emote):
        """
        Управляет значениями переменных, беря их и их значение из Emotes.json
        """

        def getemotes(emote):
            with open("Emotes.json", "r") as f:
                emotes_data = json.load(f)
            emote_data = emotes_data[emote]
            return emote_data

        emote_data = getemotes(emote)
        rndm = EEC().RandomBetween
        names = []
        values = []
        for parameter_name, parameter_value in emote_data.items():
            if parameter_name == "EyesOpen":
                eyesopen_value = eval(parameter_value)
                values.append(eyesopen_value)
                values.append(eyesopen_value)
                names.append("EmiEyeOpenRight")
                names.append("EmiEyeOpenLeft")
            else:
                names.append(parameter_name)
                value = eval(parameter_value)
                values.append(value)

        await self.VTubeConnect()
        for i, name in enumerate(names):
            value = values[i]
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(
                    parameter=name,
                    min=0,
                    max=100,
                    default_value=value
                )
            )
        await self.myvts.close()

class AutoUpdate():
    def check_for_updates(self):
        try:
            response = requests.get("https://raw.githubusercontent.com/Kajitsy/Emilia/emilia/autoupdate.json")
            response.raise_for_status()
            updates = response.json()

            if pre == True:
                if "latest_prerealease" in updates:
                    latest_prerealease = updates["latest_prerealease"]
                    if int(latest_prerealease["build"]) > int(build):
                        self.download_and_update_script(latest_prerealease["url"], latest_prerealease["build"])
                        return
                if "latest_release" in updates:
                    latest_release = updates["latest_release"]
                    if int(latest_release["build"]) > int(build):
                        self.download_and_update_script(latest_release["url"], latest_release["build"])
                        return
            else:
                if "latest_release" in updates:
                    latest_release = updates["latest_release"]
                    if int(latest_release["build"]) > int(build):
                        self.download_and_update_script(latest_release["url"], latest_release["build"])
                        return
        except requests.exceptions.RequestException as e:
            print(f"{tr('Errors', 'UpdateCheckError')} {e}")
            writeconfig('autoupdate_enable', 'False')

    def download_and_update_script(self, url, build):
        print(tr('AutoUpdate', 'upgradeto'))
        try:
            response = requests.get(url)
            response.raise_for_status()

            with open(f"Emilia_{build}.zip", "wb") as f:
                f.write(response.content)

            with zipfile.ZipFile(f"Emilia_{build}.zip", "r") as zip_ref:
                zip_ref.extractall(".")

            os.remove(f"Emilia_{build}.zip")

            print(f"{tr('AutoUpdate', 'emiliaupdated')} {build}!")
            os.execv(sys.executable, ['python'] + sys.argv)
        except requests.exceptions.RequestException as e:
            print(f"{tr('Errors', 'UpdateDownloadError')} {e}")
            writeconfig('autoupdate_enable', 'False')
        except zipfile.BadZipFile as e:
            print(f"{tr('Errors', 'BadZipFile')} {e}")
            writeconfig('autoupdate_enable', 'False')

class OptionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emilia: Options")
        self.setWindowIcon(QIcon(emiliaicon))
        self.setFixedWidth(225)
        self.setMinimumHeight(150)

        layout = QVBoxLayout()

        autoupdatelayout = QHBoxLayout()
        self.autoupdate = QCheckBox()
        if autoupdate_enable == "True":
            self.autoupdate.setChecked(True)
        self.autoupdate.stateChanged.connect(self.autoupdatechange)

        autoupdatelayout.addWidget(QLabel("Auto Update"))
        autoupdatelayout.addWidget(self.autoupdate)
        layout.addLayout(autoupdatelayout)

        langlayout = QHBoxLayout()
        self.languagechange = QComboBox()
        if lang == "ru_RU":
            self.languagechange.addItems(["Russian", "English"])
        else:
            self.languagechange.addItems(["English", "Russian"])
        self.languagechange.currentTextChanged.connect(lambda: self.langchange())

        langlayout.addWidget(QLabel("Select Language"))
        langlayout.addWidget(self.languagechange)
        layout.addLayout(langlayout)


        aitypelayout = QHBoxLayout()
        self.aitypechange = QComboBox()
        if aitype == "charai":
            self.aitypechange.addItems(["Character.AI", "Google Gemini"])
        elif aitype == "gemini":
            self.aitypechange.addItems(["Google Gemini", "Character.AI"])
        self.aitypechange.currentTextChanged.connect(lambda: self.aichange())


        torchdevicelayout = QHBoxLayout()
        self.torchdeviceselect = QComboBox()
        if torchdevice == "cuda":
            self.torchdeviceselect.addItems(["GPU", "CPU"])
        elif torchdevice == "cpu":
            self.torchdeviceselect.addItems(["CPU", "GPU"])
        self.torchdeviceselect.currentTextChanged.connect(lambda: self.torchdevicechange())

        torchdevicelayout.addWidget(QLabel("Voice generation device: "))
        torchdevicelayout.addWidget(self.torchdeviceselect)
        layout.addLayout(torchdevicelayout)


        vtubelayout = QHBoxLayout()
        self.vtubecheck = QCheckBox()
        if vtubeenable == "True":
            self.vtubecheck.setChecked(True)
        self.vtubecheck.stateChanged.connect(self.vtubechange)

        vtubelayout.addWidget(QLabel("VTube Model"))
        vtubelayout.addWidget(self.vtubecheck)
        layout.addLayout(vtubelayout)

        self.setLayout(layout)

    def vtubechange(self, state):
        if state == 2:
            writeconfig('vtubeenable', "True")
        else:
            writeconfig('vtubeenable', "False")

    def autoupdatechange(self, state):
        if state == 2:
            writeconfig('autoupdate_enable', "True")
        else:
            writeconfig('autoupdate_enable', "False")

    def restartneed(self):
        msg = QMessageBox()
        msg.setWindowTitle("Restart Need")
        text = "You have changed the setting that requires a restart, A RESTART IS REQUIRED"
        msg.setText(text)
        msg.exec()

    def torchdevicechange(self):
        value = self.torchdeviceselect.currentText()
        if value == "GPU":
            writeconfig('devicefortorch', "cuda")
        elif value == "CPU":
            writeconfig('devicefortorch', "cpu")

    def aichange(self):
        value = self.aitypechange.currentText()
        if value == "Character.AI":
            writeconfig('aitype', "charai")
        elif value == "Google Gemini":
            writeconfig('aitype', "gemini")
        self.restartneed()
        os.execv(sys.executable, ['python'] + sys.argv)

    def langchange(self):
        value = self.languagechange.currentText()
        if value == "Russian":
            writeconfig('language', "ru_RU")
        elif value == "English":
            writeconfig('language', "en_US")
        self.restartneed()
        os.execv(sys.executable, ['python'] + sys.argv)

class FirstLaunch(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia")
        self.setFixedWidth(300)
        self.setMinimumHeight(100)

        self.layout = QVBoxLayout()

        # First Page

        self.first_launch_notification_label = QLabel(tr('FirstLaunch', 'first_launch_notification_label'))
        if pre:
            self.first_launch_notification_label.setText(f"{self.first_launch_notification_label.text()}\n{tr('FirstLaunch', 'pre_first_launch_notification_label')}")
        self.first_launch_notification_label.setWordWrap(True)

        self.first_launch_notification_button_yes = QPushButton(tr('FirstLaunch', 'first_launch_notification_button_yes'))
        self.first_launch_notification_button_yes.clicked.connect(lambda: self.second_page())

        self.first_launch_notification_button_no = QPushButton(tr('FirstLaunch', 'first_launch_notification_button_no'))
        self.first_launch_notification_button_no.clicked.connect(lambda: self.first_launch_button_no())

        fphlayout = QHBoxLayout()
        fphlayout.addWidget(self.first_launch_notification_button_yes)
        fphlayout.addWidget(self.first_launch_notification_button_no)

        self.layout.addWidget(self.first_launch_notification_label)
        self.layout.addLayout(fphlayout)

        # Second Page

        self.characterai_button = QPushButton(tr('FirstLaunch', 'characterai_button'))
        self.characterai_button.clicked.connect(lambda: self.use_characterai())

        self.gemini_button = QPushButton(tr('FirstLaunch', 'gemini_button'))
        self.gemini_button.clicked.connect(lambda: self.use_gemini())

        self.sphlayout = QHBoxLayout()
        self.sphlayout.addWidget(self.characterai_button)
        self.sphlayout.addWidget(self.gemini_button)

        # Use Char.AI

        self.ready_button = QPushButton(tr('FirstLaunch', 'ready_button'))
        self.ready_button.clicked.connect(lambda: self.enterscharaidata())

        # Use Gemini

        self.geminiapikey = QLineEdit()

        self.gemapikeyready_button = QPushButton(tr('FirstLaunch', 'ready_button'))
        self.gemapikeyready_button.clicked.connect(lambda: self.entervoice())

        # Enter CharAI Data

        self.CharAIDataready_button = QPushButton(tr('FirstLaunch', 'ready_button'))
        self.CharAIDataready_button.clicked.connect(lambda: self.ShowMoreFeatures())

        # Enter Voice

        self.voiceentry = QLineEdit()
        self.voiceentry.setPlaceholderText(tr('MainWindow', 'voices'))

        self.voiceready_button = QPushButton("Relaunch!")
        self.voiceready_button.clicked.connect(lambda: self.afterentervoice())

        # Page with Additional features

        self.usevtubemodel = QCheckBox("Use VTube Model")
        self.usevtubemodel.stateChanged.connect(self.usesvtubemodel)

        self.enableautoupdate = QCheckBox("Enable Auto Update")
        self.enableautoupdate.stateChanged.connect(self.enablesautoupdate)

        self.relaunch_button2 = QPushButton("Relaunch!")
        self.relaunch_button2.clicked.connect(lambda: os.execv(sys.executable, ['python'] + sys.argv))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.layout)

    def enablesautoupdate(self, state):
        if state == 2:
            writeconfig('autoupdate_enable', "True")
        else:
            writeconfig('autoupdate_enable', "False")

    def usesvtubemodel(self, state):
        if state == 2:
            writeconfig('vtubeenable', "True")
            msg = QMessageBox()
            msg.setWindowTitle("Emilia")
            msg.setWindowIcon(QIcon(emiliaicon))
            text = "Attention, using Emilia together with the VTube model can greatly slow down the generation of responses"
            msg.setText(text)
            msg.exec()
        else:
            writeconfig('vtubeenable', "False")

    def ShowMoreFeatures(self):
        self.first_launch_notification_label.setText("Pay attention to the additional functions of Emilia")
        self.CharAIDataready_button.setVisible(False)
        self.voiceready_button.setVisible(False)
        self.voiceentry.setVisible(False)
        self.layout.addWidget(self.usevtubemodel)
        self.layout.addWidget(self.enableautoupdate)
        self.layout.addWidget(self.relaunch_button2)

    def afterentervoice(self):
        writeconfig('speaker', self.voiceentry.text())
        self.ShowMoreFeatures()

    def entervoice(self):
        writeconfig('token', self.geminiapikey.text(), 'geminiconfig.json')
        self.first_launch_notification_label.setText("Enter the name of the desired voice")
        self.gemapikeyready_button.setVisible(False)
        self.layout.addWidget(self.voiceentry)
        self.layout.addWidget(self.voiceready_button)

    def enterscharaidata(self):
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'enterscharaidata'))
        self.ready_button.setVisible(False)
        self.geminiapikey.setVisible(False)
        self.layout.addWidget(self.CharAIDataready_button)
        self.character_editor = CharacterEditor()
        self.character_editor.show()

    def use_gemini(self):
        writeconfig('aitype', 'gemini')
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'use_gemini'))
        webbrowser.open("https://aistudio.google.com/app/apikey")
        self.characterai_button.setVisible(False)
        self.gemini_button.setVisible(False)
        self.layout.addWidget(self.geminiapikey)
        self.layout.addWidget(self.gemapikeyready_button)

    def use_characterai(self):
        writeconfig('aitype', 'charai')
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'use_characterai'))
        self.characterai_button.setVisible(False)
        self.gemini_button.setVisible(False)
        self.layout.addWidget(self.ready_button)
        self.auth_window = EmiliaAuth()
        self.auth_window.show()

    def second_page(self):
        self.first_launch_notification_label.setText(tr('FirstLaunch', 'second_page'))
        self.first_launch_notification_button_yes.setVisible(False)
        self.first_launch_notification_button_no.setVisible(False)
        self.layout.addLayout(self.sphlayout)

    def first_launch_button_no(self):
        writeconfig('aitype', 'charai')
        os.execv(sys.executable, ['python'] + sys.argv)

class CharacterEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Character Editor")
        self.setFixedWidth(300)

        self.name_label = QLabel(tr("CharEditor", "charname"))
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("Emilia...")

        self.id_label = QLabel(tr("MainWindow", "characterid"))
        self.id_entry = QLineEdit()
        self.id_entry.setPlaceholderText("ID...")

        self.voice_label = QLabel(tr("MainWindow", "voice"))
        self.voice_entry = QLineEdit()
        self.voice_entry.setPlaceholderText(tr("MainWindow", "voices"))

        self.addchar_button = QPushButton(tr("CharEditor", "addchar"))
        self.addchar_button.clicked.connect(lambda: self.addchar())

        self.delchar_button = QPushButton(tr("CharEditor", "delchar"))
        self.delchar_button.clicked.connect(lambda: self.delchar())

        if backcolor != "":
            self.set_background_color(QColor(backcolor))
        if buttoncolor != "":
            self.set_button_color(QColor(buttoncolor))
        if labelcolor != "":
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor != "":
            self.set_button_text_color(QColor(buttontextcolor))

        layout = QVBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_entry)
        layout.addWidget(self.id_label)
        layout.addWidget(self.id_entry)
        layout.addWidget(self.voice_label)
        layout.addWidget(self.voice_entry)
        layout.addWidget(self.addchar_button)
        layout.addWidget(self.delchar_button)
        self.setLayout(layout)

    def addchar(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        data.update({self.name_entry.text(): {"name": self.name_entry.text(), "char": self.id_entry.text(), "voice": self.voice_entry.text()}})
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def delchar(self):
        name = self.name_entry.text()
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        if name in data:
            del data[name]
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            msg = QMessageBox()
            if pre == True:
                msg.setWindowTitle(tr("CharEditor", "error") + build)
            else:
                msg.setWindowTitle(tr("CharEditor", "error"))
            msg.setWindowIcon(QIcon(emiliaicon))
            text = tr("CharEditor", "notavchar")
            msg.setText(text)
            msg.exec()
            self.central_widget.setLayout(self.layout)

class EmiliaAuth(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Getting Token")
        self.setFixedWidth(300)
        self.setMinimumHeight(100)

        self.email_label = QLabel(tr("GetToken","youremail"))
        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("example@example.com")

        self.getlink_button = QPushButton(tr("GetToken", "sendemail"))
        self.getlink_button.clicked.connect(lambda: self.getlink())

        self.link_label = QLabel(tr("GetToken", "linkfromemail"))
        self.link_entry = QLineEdit()
        self.link_entry.setPlaceholderText("https...")

        self.gettoken_button = QPushButton(tr("GetToken", "gettoken"))
        self.gettoken_button.clicked.connect(lambda: self.gettoken())

        self.link_label.setVisible(False)
        self.link_entry.setVisible(False)
        self.gettoken_button.setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_entry)
        layout.addWidget(self.getlink_button)
        layout.addWidget(self.link_label)
        layout.addWidget(self.link_entry)
        layout.addWidget(self.gettoken_button)
        self.setLayout(layout)

    def getlink(self):
        sendCode(self.email_entry.text())
        self.link_label.setVisible(True)
        self.link_entry.setVisible(True)
        self.gettoken_button.setVisible(True)

    def gettoken(self):
        try:
            token = authUser(self.link_entry.text(), self.email_entry.text())
            self.link_label.setVisible(False)
            self.link_entry.setVisible(False)
            self.gettoken_button.setVisible(False)
            self.email_entry.setVisible(False)
            self.getlink_button.setVisible(False)
            self.email_label.setText(tr("GetToken", "yourtoken") + token + tr("GetToken", "saveincharaiconfig"))
            writeconfig('client', token, 'charaiconfig.json')
        except {Exception} as e:
            msg = QMessageBox()
            msg.setWindowTitle(tr("Errors", "Label"))
            msg.setWindowIcon(QIcon(emiliaicon))
            text = tr("Errors", "other") + e
            msg.setText(text)
            msg.exec()

class Emilia(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia")
        self.setFixedWidth(300)
        self.setMinimumHeight(250)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()

        if aitype == "gemini":
            self.token_label = QLabel(tr("MainWindow", "geminitoken"))

            self.token_entry = QLineEdit()
            self.token_entry.setPlaceholderText(tr("MainWindow", "token"))
            self.token_entry.setText(getconfig('token', configfile='geminiconfig.json'))

            layout.addWidget(self.token_label)
            layout.addWidget(self.token_entry)

            genai.configure(api_key=self.token_entry.text())
        elif aitype == "charai":
            hlayout = QHBoxLayout()

            self.char_label = QLabel(tr("MainWindow", "characterid"))
            self.char_label.setWordWrap(True)

            self.char_entry = QLineEdit()
            self.char_entry.setPlaceholderText("ID...")
            self.char_entry.setText(getconfig('char', configfile='charaiconfig.json'))

            self.client_label = QLabel(tr("MainWindow", "charactertoken"))
            self.client_label.setWordWrap(True)

            self.client_entry = QLineEdit()
            self.client_entry.setPlaceholderText(tr("MainWindow", "token"))
            self.client_entry.setText(getconfig('client', configfile='charaiconfig.json'))

            hlayout.addWidget(self.char_label)
            hlayout.addWidget(self.char_entry)
            hlayout.addWidget(self.client_label)
            hlayout.addWidget(self.client_entry)

            layout.addLayout(hlayout)
        self.speaker_label = QLabel(tr("MainWindow", "voice"))
        self.speaker_entry = QLineEdit()
        self.speaker_entry.setPlaceholderText(tr("MainWindow", "voices"))
        self.speaker_entry.setText(getconfig('speaker'))

        self.microphone = ""
        self.selected_device_index = ""

        if backcolor != "":
            self.set_background_color(QColor(backcolor))
        if buttoncolor != "":
            self.set_button_color(QColor(buttoncolor))
        if labelcolor != "":
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor != "":
            self.set_button_text_color(QColor(buttontextcolor))

        self.save_button = QPushButton(tr("MainWindow", "save"))
        if aitype == "charai":
            self.save_button.clicked.connect(lambda: self.charsetupconfig())
        elif aitype == "gemini":
            self.save_button.clicked.connect(lambda: self.geminisetupconfig())

        self.vstart_button = QPushButton(tr("MainWindow", "start"))
        self.vstart_button.clicked.connect(lambda: self.start_main("voice"))

        self.user_input = QLabel("")
        self.user_input.setWordWrap(True)

        self.user_aiinput = QLineEdit()
        self.user_aiinput.setPlaceholderText(tr("MainWindow", "textmodeinput"))
        self.user_aiinput.setVisible(False)

        self.tstart_button = QPushButton(tr("MainWindow", "starttext"))
        self.tstart_button.clicked.connect(lambda: self.start_main("text"))
        self.tstart_button.setVisible(False)

        self.ai_output = QLabel("")
        self.ai_output.setWordWrap(True)

        layout.addWidget(self.speaker_label)
        layout.addWidget(self.speaker_entry)
        layout.addWidget(self.save_button)
        layout.addWidget(self.vstart_button)
        layout.addWidget(self.user_input)
        layout.addWidget(self.user_aiinput)
        layout.addWidget(self.tstart_button)
        layout.addWidget(self.ai_output)
        self.central_widget.setLayout(layout)

        # MenuBar
        self.menubar = self.menuBar()
        self.emi_menu = self.menubar.addMenu('&Emilia')

        if aitype == "charai":
            self.gettokenaction = QAction(QIcon(charaiicon), tr("MainWindow", 'gettoken'), self)
        elif aitype == "gemini":
            self.gettokenaction = QAction(QIcon(googleicon), tr("MainWindow", 'gettoken'), self)
        self.gettokenaction.triggered.connect(lambda: self.gettoken())

        self.changethemeaction = QAction(tr("MainWindow", 'changetheme'), self)
        self.changethemeaction.triggered.connect(lambda: self.change_theme())

        self.optionsopenaction = QAction("Options")
        self.optionsopenaction.triggered.connect(lambda: self.optionsopen())

        self.visibletextmode = QAction(QIcon(keyboardicon), tr("MainWindow", 'usetextmode'), self)
        self.visibletextmode.triggered.connect(lambda: self.modehide("text"))

        self.visiblevoicemode = QAction(QIcon(inputicon), tr("MainWindow", 'usevoicemode'), self)
        self.visiblevoicemode.triggered.connect(lambda: self.modehide("voice"))
        self.visiblevoicemode.setVisible(False)

        self.recognizer = sr.Recognizer()
        self.mic_list = [
            mic_name for mic_name in sr.Microphone.list_microphone_names()
            if any(keyword in mic_name.lower() for keyword in ["microphone", "mic", "input"])
        ]

        self.inputdeviceselect = QMenu(tr("MainWindow", 'inputdevice'), self)

        for index, mic_name in enumerate(self.mic_list):
            action = QAction(mic_name, self)
            action.triggered.connect(lambda checked, i=index: self.set_microphone(i))
            self.inputdeviceselect.addAction(action)

        self.outputdeviceselect = QMenu(tr("MainWindow", 'outputdevice'), self)

        self.unique_devices = {}
        for dev in sd.query_devices():
            if dev["max_output_channels"] > 0 and dev["name"] not in self.unique_devices:
                self.unique_devices[dev["name"]] = dev

        for index, (name, device) in enumerate(self.unique_devices.items()):
            action = QAction(name, self)
            action.triggered.connect(lambda checked, i=index: self.set_output_device(i))
            self.outputdeviceselect.addAction(action)

        if aitype == "charai":
            self.charselect = self.menubar.addMenu(tr("MainWindow", 'charchoice'))
            self.chareditopen = QAction(QIcon(charediticon), tr("MainWindow", 'openchareditor'), self)
            self.chareditopen.triggered.connect(lambda: CharacterEditor().show())

            self.charrefreshlist = QAction(QIcon(refreshicon), "Refresh Characters")
            self.charrefreshlist.triggered.connect(lambda: self.addcharsinmenubar())

            self.charselect.addAction(self.chareditopen)
            self.charselect.addAction(self.charrefreshlist)

            self.addcharsinmenubar()

        if theme == 'windowsvista' and aitype == "charai":
            self.spacer = self.menubar.addMenu(tr("MainWindow", "spacerwincharai"))
        elif theme == 'windowsvista' and aitype == "gemini":
            self.spacer = self.menubar.addMenu(tr("MainWindow", "spacerwingemini"))
        elif theme == 'Fusion' and aitype == "charai":
            self.spacer = self.menubar.addMenu(tr("MainWindow", "spacerfusioncharai"))
        elif theme == 'Fusion' and aitype == "gemini":
            self.spacer = self.menubar.addMenu(tr("MainWindow", "spacerfusiongemini"))
        self.spacer.setEnabled(False)
        self.ver_menu = self.menubar.addMenu(tr("MainWindow", 'version') + version)

        self.issues = QAction(QIcon(githubicon), tr("MainWindow", 'BUUUG'), self)
        self.issues.triggered.connect(self.issuesopen)

        self.aboutemi = QAction(QIcon(emiliaicon), tr("MainWindow", 'aboutemi'), self)
        self.aboutemi.triggered.connect(self.about)

        self.emi_menu.addAction(self.gettokenaction)
        self.emi_menu.addAction(self.visibletextmode)
        self.emi_menu.addAction(self.visiblevoicemode)
        self.emi_menu.addAction(self.changethemeaction)
        self.emi_menu.addAction(self.optionsopenaction)
        self.emi_menu.addMenu(self.outputdeviceselect)
        self.emi_menu.addMenu(self.inputdeviceselect)
        self.ver_menu.addAction(self.issues)
        self.ver_menu.addAction(self.aboutemi)

    def optionsopen(self):
        window = OptionWindow()
        window.show()

    def autoupdatechange(self, value):
        self.disableautoupdate.triggered.disconnect()
        if value == "True":
            self.disableautoupdate.setText(tr("MainWindow", 'disableautoupdate'))
            self.disableautoupdate.triggered.connect(lambda: self.autoupdatechange("False"))
        else:
            self.disableautoupdate.setText(tr("MainWindow", 'enableautoupdate'))
            self.disableautoupdate.triggered.connect(lambda: self.autoupdatechange("True"))
        writeconfig('autoupdate_enable', value)

    def vtubechange(self, value):
        self.changevtube.triggered.disconnect()
        if value == "True":
            self.changevtube.setText(tr("MainWindow", 'vtubedisable'))
            self.changevtube.triggered.connect(lambda: self.vtubechange("False"))
        else:
            self.changevtube.setText(tr("MainWindow", 'vtubeenable'))
            self.changevtube.triggered.connect(lambda: self.vtubechange("True"))
        writeconfig('vtubeenable', value)

    def addcharsinmenubar(self):
        if os.path.exists('config.json'):
            def open_json(char, speaker):
                self.char_entry.setText(char)
                self.speaker_entry.setText(speaker)
            def create_action(key, value):
                def action_func():
                    open_json(value['char'], value['voice'])
                action = QAction(f'&{key}', self)
                action.triggered.connect(action_func)
                return action
            try:
                with open('data.json', 'r', encoding='utf-8') as file:
                    data = json.load(file)
            except FileNotFoundError:
                data = {}
            except json.JSONDecodeError:
                data = {}
            for key, value in data.items():
                action = create_action(key, value)
                self.charselect.addAction(action)

    def set_microphone(self, index):
        self.microphone = sr.Microphone(device_index=index)

    def set_output_device(self, index):
        device = list(self.unique_devices.values())[index]
        sd.default.device = device["index"]
        self.selected_device_index = index

    def set_background_color(self, color):
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        self.setPalette(palette)

    def set_button_text_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_button_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QPushButton {{
                background-color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def set_label_color(self, color):
        current_style_sheet = self.styleSheet()
        new_style_sheet = f"""
            QLabel {{
                color: {color.name()};
            }}
        """
        self.setStyleSheet(current_style_sheet + new_style_sheet)

    def styles_reset(self):
        self.setStyleSheet("")

    def devicechange(self, device):
        writeconfig('devicefortorch', device)

    def langchange(self, lang):
        writeconfig('language', lang)
        os.remove("voice.pt")
        os.execv(sys.executable, ['python'] + sys.argv)

    def gettoken(self):
        if aitype == "charai":
            self.auth_window = EmiliaAuth()
            self.auth_window.show()
        elif aitype == "gemini":
            webbrowser.open("https://aistudio.google.com/app/apikey")

    def issuesopen(self):
        webbrowser.open("https://github.com/Kajitsy/Emilia/issues")

    def modehide(self, mode):
        if mode == "text":
            self.visiblevoicemode.setVisible(True)
            self.visibletextmode.setVisible(False)
            self.tstart_button.setVisible(True)
            self.user_aiinput.setVisible(True)
            self.vstart_button.setVisible(False)
        elif mode == "voice":
            self.visiblevoicemode.setVisible(False)
            self.visibletextmode.setVisible(True)
            self.tstart_button.setVisible(False)
            self.user_aiinput.setVisible(True)
            self.vstart_button.setVisible(False)

    def geminiuse(self):
        writeconfig('aitype', 'gemini')
        os.execv(sys.executable, ['python'] + sys.argv)

    def charaiuse(self):
        writeconfig('aitype', 'charai')
        os.execv(sys.executable, ['python'] + sys.argv)

    def change_theme(self):
        if theme == 'windowsvista':
            githubicon = './images/github.png'
            changelang = './images/change_language.png'
            keyboardicon = './images/keyboard.png'
            inputicon = './images/input.png'
            charediticon = './images/open_char_editor.png'
            self.setStyle('Fusion')
            writeconfig('theme', 'Fusion')
        else:
            githubicon = './images/github_white.png'
            changelang = './images/change_language_white.png'
            keyboardicon = './images/keyboard_white.png'
            inputicon = './images/input_white.png'
            charediticon = './images/open_char_editor_white.png'
            self.setStyle('windowsvista')
            writeconfig('theme', 'windowsvista')
        self.visibletextmode.setIcon(QIcon(keyboardicon))
        self.visiblevoicemode.setIcon(QIcon(inputicon))
        self.changelanguage.setIcon(QIcon(changelang))
        self.issues.setIcon(QIcon(githubicon))
        if aitype == 'charai':
            self.chareditopen.setIcon(QIcon(charediticon))

    def about(self):
        msg = QMessageBox()
        if pre == True:
            msg.setWindowTitle(tr("About", "aboutemi") + build)
        else:
            msg.setWindowTitle(tr("About", "aboutemi"))
        msg.setWindowIcon(QIcon(emiliaicon))
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        msg.setIconPixmap(pixmap)
        language = tr("About", "languagefrom")
        whatsnew = tr("About", "newin") + version + tr("About", "whatsnew")
        otherversions = tr("About", "viewallreleases")
        text = tr("About", "emiopenproject") + version + tr("About", "usever") + language + whatsnew + otherversions
        msg.setText(text)
        msg.exec()

    def reading_chat_history(self):
      with open('chat_history.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
      return data

    def writing_chat_history(self, text):
        try:
            with open('chat_history.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        dtime = "%m-%d %H:%M:%S"
        data.update({datetime.datetime.now().strftime(dtime): text})

        with open('chat_history.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def silero_tts(self, text):
        model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        model.to(torch.device(torchdevice))
        audio = model.apply_tts(text=text,
                                speaker=self.speaker_entry.text(),
                                sample_rate=sample_rate,
                                put_accent=put_accent,
                                put_yo=put_yo)
        return audio

    def chating(self, textinchat):
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=[])
        chat.send_message(f"Here's our chat history: {self.reading_chat_history()}")
        for chunk in chat.send_message(textinchat):
            continue
        return chunk.text

    def numbers_to_words(self, text):
        try:
            def _conv_num(match):
                if lang == "ru_RU":
                    return num2words(int(match.group()), lang='ru')
                else:
                    return num2words(int(match.group()), lang='en')

            return re.sub(r'\b\d+\b', _conv_num, text)
        except Exception as e:
            print(tr("MainWinow", 'noncriterror') + {e})
            return text

    async def main(self):
        while True:
            if vtubeenable == "True":
                await EEC().UseEmote("Listening")
            recognizer = sr.Recognizer()
            self.user_input.setText(tr("Main", "speakup"))
            if self.microphone != "":
                with self.microphone as source:
                    audio = recognizer.listen(source)
            else:
                with sr.Microphone() as source:
                    audio = recognizer.listen(source)
            try:
                if lang == "ru_RU":
                    msg1 = recognizer.recognize_google(audio, language="ru-RU")
                else:
                    msg1 = recognizer.recognize_google(audio, language="en-US")
            except sr.UnknownValueError:
                self.user_input.setText(tr("Main", "sayagain"))
                continue
            self.user_input.setText(tr("Main", "user") + msg1)
            self.ai_output.setText(tr("Main", "emigen"))
            if vtubeenable == "True":
                await EEC().UseEmote("Thinks")
            if aitype == "charai":
                token = aiocai.Client(self.client_entry.text())
                chatid = await token.get_chat(self.char_entry.text())
                async with await token.connect() as chat:
                    messagenotext = await chat.send_message(self.char_entry.text(), chatid.chat_id, msg1)
                    message = messagenotext.text
            elif aitype == "gemini":
                try:
                    message = self.chating(msg1)
                    self.writing_chat_history(f"User: {msg1}")
                    self.writing_chat_history(f"AI: {message}")
                except Exception as e:
                    if e.code == 400 and "User location is not supported" in e.message:
                        self.ai_output.setText(tr("Errors", 'Gemini 400'))
            if lang == "ru_RU":
                translation = await Translator().translate(message, targetlang="ru")
                nums = self.numbers_to_words(translation.text)
            else:
                nums = self.numbers_to_words(message.text)
            if vtubeenable == "True":
                await EEC().UseEmote("VoiceGen")
            self.ai_output.setText(tr("Main", "emimessage") + translation.text)
            if vtubeenable == "True":
                await EEC().UseEmote("Says")
            audio = self.silero_tts(nums)
            if self.selected_device_index != "":
                device = list(self.unique_devices.values())[self.selected_device_index]
                sd.play(audio, sample_rate, device=device["index"])
            else:
                sd.play(audio, sample_rate)
            time.sleep(len(audio - 5) / sample_rate)
            sd.stop()
            if vtubeenable == "True":
                await EEC().UseEmote("AfterSays")

    async def maintext(self):
        if self.user_aiinput.text() == "":
            self.user_aiinput.setText("It's actually empty here")
        else:
            if vtubeenable == "True":
                await EEC().UseEmote("Thinks")
            self.user_input.setText(tr("Main", "user"))
            msg1 = self.user_aiinput.text()
            self.ai_output.setText(tr("Main", "emigen"))
            if aitype == "charai":
                token = aiocai.Client(self.client_entry.text())
                chatid = await token.get_chat(self.char_entry.text())
                async with await token.connect() as chat:
                    messagenotext = await chat.send_message(self.char_entry.text(), chatid.chat_id, msg1)
                    message = messagenotext.text
            elif aitype == "gemini":
                try:
                    message = self.chating(msg1)
                    self.writing_chat_history(f"User: {msg1}")
                    self.writing_chat_history(f"AI: {message}")
                except Exception as e:
                    if e.code == 400 and "User location is not supported" in e.message:
                        self.ai_output.setText(tr("Errors", 'Gemini 400'))
            if lang == "ru_RU":
                translation = await Translator().translate(message, targetlang="ru")
                nums = self.numbers_to_words(translation.text)
            else:
                nums = self.numbers_to_words(message.text)
            if vtubeenable == "True":
                await EEC().UseEmote("VoiceGen")
            audio = self.silero_tts(nums)
            self.ai_output.setText(tr("Main", "emimessage") + translation.text)
            await EEC().UseEmote("Says")
            if self.selected_device_index != "":
                device = list(self.unique_devices.values())[self.selected_device_index]
                sd.play(audio, sample_rate, device=device["index"])
            else:
                sd.play(audio, sample_rate)
            time.sleep(len(audio - 5) / sample_rate)
            sd.stop()
            if vtubeenable == "True":
                await EEC().UseEmote("Listening")

    def start_main(self, mode):
        if self.speaker_entry == "":
            self.ai_output.setText(tr("Errors", "nonvoice"))
        else:
            if mode == "voice":
                threading.Thread(target=lambda: asyncio.run(self.main())).start()
                for i in range(self.layout.count()):
                    widget = self.layout.itemAt(i).widget()
                    widget.setVisible(False)
                self.user_input.setVisible(True)
                self.ai_output.setVisible(True)
            elif mode == "text":
                threading.Thread(target=lambda: asyncio.run(self.maintext())).start()

    def charsetupconfig(self):
        writeconfig('char', self.char_entry.text(), 'charaiconfig.json')
        writeconfig('client', self.client_entry.text(), 'charaiconfig.json')
        writeconfig('speaker', self.speaker_entry.text())

    def geminisetupconfig(self):
        token = self.token_entry.text()
        writeconfig('token', token, 'geminiconfig.json')
        writeconfig('speaker', self.speaker_entry.text())
        genai.configure(api_key=token)

if __name__ == "__main__":
    if autoupdate_enable != "False":
        AutoUpdate().check_for_updates()
    app = QApplication(sys.argv)
    app.setStyle(theme)
    if not os.path.exists('config.json'):
        window = FirstLaunch()
    else:
        window = Emilia()
    if vtubeenable == "True":
        asyncio.run(EEC().VTubeConnect())
    window.show()
    sys.exit(app.exec())