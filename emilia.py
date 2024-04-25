import os
import asyncio
import threading
import torch
import time
import re
import json
import sys
import subprocess
import webbrowser
import datetime
import sounddevice as sd
import google.generativeai as genai
import speech_recognition as sr
from gpytranslate import Translator
from characterai import aiocai
from num2words import num2words
from PyQt6.QtWidgets import QHBoxLayout, QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QMenu, QColorDialog, QFileDialog
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QPalette
from PyQt6.QtCore import QLocale

locale = QLocale.system().name()

if not os.path.exists('voice.pt'):
    if locale == "ru_RU":
        print("Идёт загрузка модели SileroTTS RU")
        print("")
        torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt',
                                    "voice.pt")
        print("_____________________________________________________")
        print("ГОТОВО, ПРОСТИТЕ")
    else:
        print("The SileroTTS EN model is being loaded")
        print("")
        torch.hub.download_url_to_file('https://models.silero.ai/models/tts/en/v3_en.pt',
                                    "voice.pt")
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

translations = load_translations(f"locales/{locale}.json")

ver = "2.1.1"
build = "242504"
pre = "True"
if pre == "True":
    version = "pre" + ver
else:
    version = ver
local_file = 'voice.pt'
sample_rate = 48000
put_accent = True
put_yo = True
devmode = "false"

def numbers_to_words(text):
    def _conv_num(match):
        if locale == "ru_RU":
            return num2words(int(match.group()), lang='ru')
        else:
            return num2words(int(match.group()), lang='en')
    return re.sub(r'\b\d+\b', _conv_num, text)

if os.path.exists('config.json'):
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        aitype = config.get('aitype', '')
        if aitype == "gemini":
            aitype = "gemini"
        else:
            aitype = "charai"
        theme = config.get('theme', '')
        if theme == "dark":
            guitheme = 'Fusion'
        else:
            guitheme = 'windowsvista'
        backcolor = config.get('backgroundcolor', "")
        buttoncolor = config.get('buttoncolor', "")
        buttontextcolor = config.get('buttontextcolor', "")
        labelcolor = config.get('labelcolor', "")
        deviceft = config.get('devicefortorch', '')
        if deviceft == "cpu":
            devicefortorch = deviceft
        else:
            devicefortorch = 'cuda'
else:
    guitheme = 'windowsvista'
    theme = "white"
    aitype = "charai"
    devicefortorch = 'cuda'
    backcolor = ""
    buttoncolor = ""
    buttontextcolor = ""
    labelcolor = ""
device = torch.device(devicefortorch)
#Иконки
if pre == "True":
    emiliaicon = './images/premilia.png'
else:
    emiliaicon = './images/emilia.png'
googleicon = './images/google.png'
charaiicon = './images/charai.png'
if guitheme == 'Fusion':
    themeicon = './images/sun.png'
    githubicon = './images/github_white.png'
else:
    themeicon = './images/moon.png'
    githubicon = './images/github.png'

class BackgroundEditor(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowIcon(QIcon(emiliaicon))
        self.setWindowTitle("Emilia: Customization")
        self.setFixedWidth(100)
        self.setMinimumHeight(100)
        self.main_window = main_window

        self.color_label = QLabel(tr("EmiCustom","backcolor"))
        self.color_button = QPushButton(tr("EmiCustom", "pickbackcolor"))
        self.color_button.clicked.connect(self.choose_color)

        self.button_color_label = QLabel(tr("EmiCustom", "buttonbackcolor"))
        self.button_text_color_button = QPushButton(tr("EmiCustom", "pickbuttonbackcolor"))
        self.button_text_color_button.clicked.connect(self.choose_button_color)
        self.button_color_button = QPushButton(tr("EmiCustom", "pickbuttontextcolor"))
        self.button_color_button.clicked.connect(self.choose_button_text_color)

        self.label_color_label = QLabel(tr("EmiCustom", "labelcolor"))
        self.label_color_button = QPushButton(tr("EmiCustom", "picktextcolor"))
        self.label_color_button.clicked.connect(self.choose_label_color)

        self.label_all_reset = QLabel(" ")
        self.button_all_reset = QPushButton(tr("EmiCustom", "ALLRESET"))
        self.button_all_reset.clicked.connect(self.allreset)

        layout = QVBoxLayout()
        layout.addWidget(self.button_color_label)
        layout.addWidget(self.button_color_button)
        layout.addWidget(self.button_text_color_button)
        layout.addWidget(self.label_color_label)
        layout.addWidget(self.label_color_button)
        layout.addWidget(self.color_label)
        layout.addWidget(self.color_button)
        layout.addWidget(self.label_all_reset)
        layout.addWidget(self.button_all_reset)
        self.setLayout(layout)

        self.current_color = QColor("#ffffff")
        self.current_button_color = QColor("#ffffff") 
        self.current_label_color = QColor("#000000") 

    def writeconfig(self, value, pup):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        data.update({value: pup})
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        self.main_window.set_background_color(color) 
        self.writeconfig("backgroundcolor", color.name())

    def choose_button_color(self):
        color1 = QColorDialog.getColor(self.current_button_color, self)
        self.main_window.set_button_color(color1)
        self.writeconfig("buttoncolor", color1.name())

    def choose_button_text_color(self):
        color3 = QColorDialog.getColor(self.current_button_color, self)
        self.main_window.set_button_text_color(color3)
        self.writeconfig("buttontextcolor", color3.name())

    def choose_label_color(self):
        color2 = QColorDialog.getColor(self.current_label_color, self)
        self.main_window.set_label_color(color2)
        self.writeconfig("labelcolor", color2.name())

    def allreset(self):
        self.main_window.styles_reset()
        self.writeconfig("backgroundcolor", "")
        self.writeconfig("labelcolor", "")
        self.writeconfig("buttontextcolor", "")
        self.writeconfig("buttoncolor", "")

class EmiliaGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emilia")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        global tstart_button, user_aiinput, vstart_button, visibletextmode, visiblevoicemode, issues
        if aitype == "gemini":
            token_label = QLabel(tr("MainWindow", "geminitoken"))
            self.layout.addWidget(token_label)
            self.token_entry = QLineEdit()
            self.layout.addWidget(self.token_entry)
            self.token_entry.setPlaceholderText(tr("MainWindow", "token"))
        elif aitype == "charai":
            hlayout = QHBoxLayout()
            char_label = QLabel(tr("MainWindow", "characterid"))
            char_label.setWordWrap(True)
            hlayout.addWidget(char_label)
            self.char_entry = QLineEdit()
            hlayout.addWidget(self.char_entry)
            self.char_entry.setPlaceholderText("ID...")
            client_label = QLabel(tr("MainWindow", "charactertoken"))
            client_label.setWordWrap(True)
            hlayout.addWidget(client_label)
            self.client_entry = QLineEdit()
            hlayout.addWidget(self.client_entry)
            self.client_entry.setPlaceholderText(tr("MainWindow", "token"))
            self.layout.addLayout(hlayout)
        speaker_label = QLabel(tr("MainWindow", "voice"))
        self.layout.addWidget(speaker_label)
        self.speaker_entry = QLineEdit()
        self.layout.addWidget(self.speaker_entry)
        self.speaker_entry.setPlaceholderText(tr("MainWindow", "voices"))

        self.load_config()
        if backcolor != "":
            self.set_background_color(QColor(backcolor))
        if buttoncolor != "":
            self.set_button_color(QColor(buttoncolor))
        if labelcolor != "":
            self.set_label_color(QColor(labelcolor))
        if buttontextcolor != "":
            self.set_button_text_color(QColor(buttontextcolor))

        save_button = QPushButton(tr("MainWindow", "save"))
        if aitype == "charai":
            save_button.clicked.connect(lambda: self.charsetupconfig(self.char_entry, self.client_entry, self.speaker_entry))
        elif aitype == "gemini": 
            save_button.clicked.connect(lambda: self.geminisetupconfig(self.token_entry, self.speaker_entry))
        self.layout.addWidget(save_button)

        vstart_button = QPushButton(tr("MainWindow", "start"))
        vstart_button.clicked.connect(lambda: self.start_main("voice"))
        self.layout.addWidget(vstart_button)

        self.user_input = QLabel("")
        self.user_input.setWordWrap(True)
        self.layout.addWidget(self.user_input)
        
        user_aiinput = QLineEdit()
        user_aiinput.setPlaceholderText(tr("MainWindow", "textmodeinput"))
        self.layout.addWidget(user_aiinput)
        user_aiinput.setVisible(False)

        tstart_button = QPushButton(tr("MainWindow", "starttext"))
        tstart_button.clicked.connect(lambda: self.start_main("text"))
        self.layout.addWidget(tstart_button)
        tstart_button.setVisible(False)

        self.ai_output = QLabel("")
        self.ai_output.setWordWrap(True)
        self.layout.addWidget(self.ai_output)

        self.central_widget.setLayout(self.layout)
        menubar = self.menuBar()
        emi_menu = menubar.addMenu('&Emilia')

        if aitype == "charai":
            getcharaitoken = QAction(QIcon(charaiicon), tr("MainWindow", 'gettoken'), self)
        elif aitype == "gemini":
            getcharaitoken = QAction(QIcon(googleicon), tr("MainWindow", 'gettoken'), self)
        getcharaitoken.triggered.connect(lambda: self.gettoken())

        changethemeaction = QAction(QIcon(themeicon), tr("MainWindow", 'changetheme'), self)
        if guitheme == 'Fusion':
            changethemeaction.triggered.connect(lambda: self.change_theme("white"))
        else:
            changethemeaction.triggered.connect(lambda: self.change_theme("dark"))
        emi_menu.addAction(changethemeaction)

        visibletextmode = QAction(tr("MainWindow", 'usetextmode'), self)
        emi_menu.addAction(visibletextmode)

        visiblevoicemode = QAction(tr("MainWindow", 'usevoicemode'), self)
        emi_menu.addAction(visiblevoicemode)
        visiblevoicemode.setVisible(False)

        deviceselect = QMenu(tr("MainWindow", 'voicegendevice'), self)
        emi_menu.addMenu(deviceselect)

        usecpumode = QAction(tr("MainWindow", 'usecpu'), self)
        usecpumode.triggered.connect(lambda: self.devicechange('cpu'))
        deviceselect.addAction(usecpumode)

        usegpumode = QAction(tr("MainWindow", 'usegpu'), self)
        usegpumode.triggered.connect(lambda: self.devicechange('cuda'))
        deviceselect.addAction(usegpumode)

        serviceselect = QMenu(tr("MainWindow", 'changeai'), self)
        emi_menu.addMenu(serviceselect)

        usegemini = QAction(QIcon(googleicon), tr("MainWindow", 'usegemini'), self)
        usegemini.triggered.connect(lambda: self.geminiuse(self.speaker_entry))
        serviceselect.addAction(usegemini)

        usecharai = QAction(QIcon(charaiicon), tr("MainWindow", 'usecharacterai'), self)
        usecharai.triggered.connect(lambda: self.charaiuse(self.speaker_entry))
        serviceselect.addAction(usecharai)

        if aitype == "charai":
            emi_menu.addAction(getcharaitoken)
            usecharai.setEnabled(False)
            usegemini.setEnabled(True)
            charselect = menubar.addMenu(tr("MainWindow", 'charchoice'))
            chareditopen = QAction(tr("MainWindow", 'openchareditor'), self)
            chareditopen.triggered.connect(lambda: subprocess.call(["python", "charedit.py"]))
            charselect.addAction(chareditopen)
            if os.path.exists('config.json'):
                def create_action(key, value):
                    def action_func():
                        self.open_json(value['char'])
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
                    charselect.addAction(action)
        elif aitype == "gemini":
            usegemini.setEnabled(False)
            usecharai.setEnabled(True)

        if guitheme == 'windowsvista':
            spacer = menubar.addMenu(tr("MainWindow", "spacerwin"))
        else:
            spacer = menubar.addMenu(tr("MainWindow", "spacer"))
        spacer.setEnabled(False)

        ver_menu = menubar.addMenu(tr("MainWindow", 'version') + version)
        debug = QAction(QIcon('./images/emilia.png'), '&Debug', self)
        debug.triggered.connect(self.debugfun)
        ver_menu.addAction(debug)

        visibletextmode.triggered.connect(lambda: self.modehide("voice"))
        visiblevoicemode.triggered.connect(lambda: self.modehide("text"))

        open_background_editor_action = QAction(tr("MainWindow", 'customcolors'), self)
        open_background_editor_action.triggered.connect(self.open_background_editor)

        emi_menu.addAction(open_background_editor_action)
        issues = QAction(QIcon(githubicon), tr("MainWindow", 'BUUUG'), self)
        issues.triggered.connect(self.issuesopen)
        emi_menu.addAction(issues)

        aboutemi = QAction(QIcon(emiliaicon), tr("MainWindow", 'aboutemi'), self)
        aboutemi.triggered.connect(self.about)
        emi_menu.addAction(aboutemi)

    def open_background_editor(self):
        self.background_editor = BackgroundEditor(self)
        self.background_editor.setFixedWidth(200)
        self.background_editor.setMinimumHeight(100)
        self.background_editor.show()

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

    def open_json(self, value):
        global char
        char = value
        self.char_entry.setText(value)
    
    def devicechange(self, device):
        global devicefortorch
        devicefortorch = device
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        data.update({"devicefortorch": device})
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def gettoken(self):
        if aitype == "charai":
            subprocess.call(["python", "auth.py"])
        elif aitype == "gemini":
            webbrowser.open("https://aistudio.google.com/app/apikey")
        self.load_config()

    def issuesopen(self):
        webbrowser.open("https://github.com/Kajitsy/Emilia/issues")

    def modehide(self, mode):
        if mode == "text":
            visiblevoicemode.setVisible(False)
            visibletextmode.setVisible(True)
            tstart_button.setVisible(False)
            user_aiinput.setVisible(False)
            vstart_button.setVisible(True)
        elif mode == "voice":
            visibletextmode.setVisible(False)
            visiblevoicemode.setVisible(True)
            vstart_button.setVisible(False)
            tstart_button.setVisible(True)
            user_aiinput.setVisible(True)   

    def geminiuse(self, speaker_entry):
        global aitype
        aitype = "gemini"
        self.globalsetupconfig(speaker_entry)
        os.execv(sys.executable, ['python'] + sys.argv)

    def charaiuse(self, speaker_entry):
        global aitype
        aitype = "charai"
        self.globalsetupconfig(speaker_entry)
        os.execv(sys.executable, ['python'] + sys.argv)

    def change_theme(self, theme):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
             data = {}
        data.update({"theme": theme})
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.execv(sys.executable, ['python'] + sys.argv)

    def about(self):
        msg = QMessageBox()
        if pre == "True":
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
        self.central_widget.setLayout(self.layout)

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
        data.update(datetime.datetime.now().strftime(dtime) + text)

        with open('chat_history.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def chating(self, textinchat):
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=[])
        chat.send_message(tr("Main", "sendchating") + self.reading_chat_history())
        for chunk in chat.send_message(textinchat):
            continue
        return chunk.text

    async def main(self):
        while True:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.user_input.setText(tr("Main", "speakup"))
                audio = recognizer.listen(source)
            try:
                msg1 = recognizer.recognize_google(audio, language="ru-RU")
            except sr.UnknownValueError:
                self.user_input.setText(tr("Main", "sayagain"))
                continue
            self.user_input.setText(tr("Main", "user") + msg1)
            self.ai_output.setText(tr("Main", "emigen"))
            if aitype == "charai":
                token = aiocai.Client(client)
                chatid = await token.get_chat(char)
                async with await token.connect() as chat:
                    messagenotext = await chat.send_message(char, chatid.chat_id, msg1)
                    message = messagenotext.text
            elif aitype == "gemini":
                message = self.chating(msg1)
                self.writing_chat_history({"User: ": msg1})
                self.writing_chat_history({"AI: ": message})
            if locale == "ru_RU":
                translation = await Translator().translate(message, targetlang="ru")
                nums = numbers_to_words(translation.text)
            else:
                nums = numbers_to_words(message.text)
            model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
            model.to(device)
            audio = model.apply_tts(text=nums,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=put_accent,
                                    put_yo=put_yo)
            self.ai_output.setText(tr("Main", "emimessage") + translation.text)
            sd.play(audio, sample_rate)
            time.sleep(len(audio - 5) / sample_rate)
            sd.stop()
        
    async def maintext(self):
        self.user_input.setText(tr("Main", "user"))
        msg1 = user_aiinput.text()
        self.ai_output.setText(tr("Main", "emigen"))
        if aitype == "charai":
            token = aiocai.Client(client)
            chatid = await token.get_chat(char)
            async with await token.connect() as chat:
                messagenotext = await chat.send_message(char, chatid.chat_id, msg1)
                message = messagenotext.text
        elif aitype == "gemini":
            message = self.chating(msg1)
            self.writing_chat_history({"User: ": msg1})
            self.writing_chat_history({"AI: ": message})
        if locale == "ru_RU":
            translation = await Translator().translate(message, targetlang="ru")
            nums = numbers_to_words(translation.text)
        else:
            nums = numbers_to_words(message.text)
        nums = numbers_to_words(translation.text)
        model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        model.to(device)
        audio = model.apply_tts(text=nums,
                                speaker=speaker,
                                sample_rate=sample_rate,
                                put_accent=put_accent,
                                put_yo=put_yo)
        self.ai_output.setText(tr("Main", "emimessage") + translation.text)
        sd.play(audio, sample_rate)
        time.sleep(len(audio - 5) / sample_rate)
        sd.stop()

    def start_main(self, mode):
        if mode == "voice":
            threading.Thread(target=lambda: asyncio.run(self.main())).start()
            for i in range(self.layout.count()):
                widget = self.layout.itemAt(i).widget()
                widget.setVisible(False)
                self.user_input.setVisible(True)
                self.ai_output.setVisible(True)
        elif mode == "text":
            threading.Thread(target=lambda: asyncio.run(self.maintext())).start()

    def load_config(self):
        global speaker, char, client, token, devicefortorch
        if aitype == "charai":
            if os.path.exists('charaiconfig.json'):
                with open('charaiconfig.json', 'r') as config_file:
                    config = json.load(config_file)
                    char = config.get('char', '')
                    client = config.get('client', '')
                    self.char_entry.setText(char)
                    self.client_entry.setText(client)
        elif aitype == "gemini":
            if os.path.exists('geminiconfig.json'):
                with open('geminiconfig.json', 'r') as config_file:
                    config = json.load(config_file)
                    token = config.get('token', '')
                    self.token_entry.setText(token)
                    genai.configure(api_key=token)
        if os.path.exists('config.json'):
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
                speaker = config.get('speaker', '')
                devicefortorch = config.get('devicefortorch', '')
                self.speaker_entry.setText(speaker)

    def charsetupconfig(self, char_entry, client_entry, speaker_entry):
        global char, client
        char = char_entry.text()
        client = client_entry.text()
        config = {
            "char": char,
            "client": client
        }

        with open('charaiconfig.json', 'w') as config_file:
            json.dump(config, config_file)
        self.globalsetupconfig(speaker_entry)

    def geminisetupconfig(self, token_entry, speaker_entry):
        global token, aitype
        token = token_entry.text()
        config = {
            "token": token
        }
        with open('geminiconfig.json', 'w') as config_file:
            json.dump(config, config_file)
        self.globalsetupconfig(speaker_entry)
        genai.configure(api_key=token)

    def globalsetupconfig(self, speaker_entry):
        global speaker, aitype, devicefortorch
        speaker = speaker_entry.text()
        config = {
            "speaker": speaker,
            "aitype": aitype,
            "theme": theme,
            "devicefortorch": devicefortorch
        }

        with open('config.json', 'w') as config_file:
            json.dump(config, config_file)
    
    def debugfun(self):
        global version, devmode
        devmode = "true"
        version = "Debug"
        self.setWindowTitle("Emilia Debug")
        msg = QMessageBox()
        msg.setStyleSheet("QMessageBox {background-color: red; text-color}")
        msg.setWindowTitle("Emilia Error")
        msg.setWindowIcon(QIcon(emiliaicon))
        pixmap = QPixmap(emiliaicon).scaled(64, 64)
        msg.setIconPixmap(pixmap)
        text = tr("Debug", "debig") + "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nNo?\n" + locale
        msg.setText(text)
        msg.exec()
        self.central_widget.setLayout(self.layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(guitheme)
    window = EmiliaGUI()
    window.setFixedWidth(300)
    window.setMinimumHeight(250)
    window.setWindowIcon(QIcon(emiliaicon))
    window.show()
    sys.exit(app.exec())