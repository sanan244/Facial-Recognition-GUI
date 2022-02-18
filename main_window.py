"""
This code is the main resource file for the GUI. This project aims to recognize faces
and store them on a local/remote database. Each face that is not recognized will be classified
'unknown' until the user enters the persons name. Additionally users will be able to search
the database for information about each person who has been recorded. There is a page that
allows the user to input information for a face that is not recognized. Upon entering this data
the face will be recognized and associated with that data. There is also a settings option
to specify what camera the user wishes to use( '0': webcam, or an IP camera address/Link). This gui may be
developed to integrate third party API's for various industries such as POS systems, customer account recognition, etc.

Distribution of this software is not permitted by the developer.
However, many libraries used for this project have varying licenses and should be reviewed.


For more information contact:

Author: Anthony Sanchez
sanchezanthony244@gmail.com
2020-22
"""
import os
import re
import sys

from cryptography.fernet import Fernet
import requests
import pathlib
import socket

import mysql.connector as mdb

# import some PyQt5 modules
from PyQt5.QtWidgets import QHBoxLayout
from qtwidgets import Toggle
from PyQt5.QtCore import Qt

# Email libraries
# Import the following module
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib

# import project files
from form_popup import *
from data_model import *
from detector import *

current_directory = str(pathlib.Path().resolve())
current_path = os.path.dirname(os.path.abspath(__file__))
print("Get path:", current_path)

# print(os.path.dirname(os.path.abspath(__file__)))
class MainWindow(QWidget):
        # class constructor
        def __init__(self):
            # Initialize database and cursor
            self.DBconnect()
            self.check_db_user_exists()
            # Session info
            self.current_account_id = None
            self.key = Fernet.generate_key()

            # call QWidget constructor
            super().__init__()
            # cosmetics
            self.setStyleSheet("color: #24a5ed;"
                               "background-color: #f0f0f0;"
                               # "border-style: solid;"
                               # "border-width: 2px;"
                               # "border-color: #ffffff"
                               )
            # self.setWindowOpacity(0.9)
            self.setWindowIcon(QtGui.QIcon(current_path + "/icon_512x512.png"))
            # self.label.setStyleSheet("border: 1px solid black;")
            # changing color of button
            # button.setStyleSheet("background-color : yellow")

            # self.ui.setupUi()
            self.setWindowTitle("Facial Recognition")
            # self.setFixedSize(900, 750)
            self.setGeometry(100, 100, 700, 700)

            # button styles for pages
            self.page_button_style = (
                """QPushButton{
                 background-color: white;
                 border-style: solid;
                 border-width:1px;
                 border-radius:15px;
                 border-color: white;
                 max-width:40px;
                 max-height:30px;
                 min-width:40px;
                 min-height:30px;
                 }
                 QPushButton::hover {
                 border-color: #24a5ed;
                }"""
            )
            self.regular_button_style = (
                """QPushButton{
                 background-color: white;
                 border-style: solid;
                 border-width:1px;
                 border-radius:7px;
                 border-color: white;
                 max-width:40px;
                 max-height:30px;
                 min-width:40px;
                 min-height:30px;
                 font: "Klavika";
                 font-size: 10px;
                 }
                 QPushButton::hover {
                 border-color: #24a5ed;
                }"""
            )
            self.valid_textbox = ("""
            background-color: white;
                 border-style: none;
                 border-width:1px;
                 border-radius:7px;
                 border-color: white;
                 max-width:175px;
                 min-width:175px;
            """)
            self.invalid_textbox = ("""
            background-color: white;
                 border-style: solid;
                 border-width:1px;
                 border-radius:7px;
                 border-color: red;
                 max-width:175px;
                 min-width:175px;
            """)
            Header_font = QtGui.QFont("Helvetica", 20)
            regular_font = QtGui.QFont("Helvetica", 13)
            label_style_header = ("""
                    font: "Klavika";
                    """)
            label_style_non_header = ("""
                    font: "Klavika";
                    """)

            # Initialize some variables and layout
            self.default_cam = None
            self.MainActive = False
            self.hbox1 = QHBoxLayout()
            # self.hbox1.setContentsMargins(5, 20, 50, 0)
            self.vbox1 = QVBoxLayout()
            self.vbox1.addStretch()
            self.vbox2 = QVBoxLayout()

            # login page
            self.login_label = QLabel("Login", self)
            self.login_label.setFont(Header_font)

            self.login_username = QLineEdit(placeholderText="Username")
            self.login_username.setStyleSheet(self.valid_textbox)

            self.login_password = QLineEdit(placeholderText="Password")
            self.login_password.setStyleSheet(self.valid_textbox)
            self.login_password.setEchoMode(QLineEdit.Password)

            self.login_button = QPushButton('Login', self)
            self.login_button.clicked.connect(self.on_login_button)
            self.login_button.setStyleSheet(self.regular_button_style)

            self.remember_device_label = QLabel("Remember this device", self)
            self.remember_device_label.setFont(regular_font)
            self.remember_this_device = Toggle(
                checked_color="#24a5ed",
            )
            self.remember_this_device.setFixedWidth(55)
            self.signupfromloginpage = QPushButton("Sign up", self)
            self.signupfromloginpage.clicked.connect(self.signuppageButtonpress)
            self.signupfromloginpage.setStyleSheet(self.regular_button_style)

            # sign up page
            self.signup_label = QLabel("Sign up")
            self.signup_label.setFont(Header_font)

            self.signup_password_rules = QLabel(
                "Password must be 8 characters long, \ncontain at least: \n1 Capitol, \n1 number, \n1 special character.",
                self)
            self.signup_password_rules.setFont(regular_font)

            self.signup_email = QLineEdit(placeholderText="email")
            self.signup_email.setStyleSheet(self.valid_textbox)

            self.create_username = QLineEdit(placeholderText="Create Username")
            self.create_username.setStyleSheet(self.valid_textbox)
            self.create_password = QLineEdit(placeholderText="Create Password")
            self.create_password.setStyleSheet(self.valid_textbox)
            self.create_password.setEchoMode(QLineEdit.Password)
            self.create_password_check = QLineEdit(placeholderText="Re-enter Password")
            self.create_password_check.setStyleSheet(self.valid_textbox)
            self.create_password_check.setEchoMode(QLineEdit.Password)

            self.signup_button = QPushButton("Sign up", self)
            self.signup_button.clicked.connect(self.on_signup_button)
            self.signup_button.setStyleSheet(self.regular_button_style)
            self.back_signuppage = QPushButton("Back", self)
            self.back_signuppage.setStyleSheet(self.regular_button_style)
            self.back_signuppage.clicked.connect(self.loginpageButtonpress)

            # page buttons
            self.home_btn = QtWidgets.QPushButton(self)
            self.home_btn.setIcon(QIcon(current_path + "/home.png"))
            self.home_btn.setStyleSheet(self.page_button_style)
            self.home_btn.setFixedWidth(40)
            self.home_btn.clicked.connect(self.homeButtonPress)
            self.vbox1.addWidget(self.home_btn)

            self.search_btn = QtWidgets.QPushButton(self)
            self.search_btn.setFixedWidth(40)
            self.search_btn.setIcon(QIcon(current_path + "/search_icon.png"))
            self.search_btn.setStyleSheet(self.page_button_style)
            self.search_btn.clicked.connect(self.searchButtonPress)
            self.vbox1.addWidget(self.search_btn)

            self.menu_bt = QPushButton(self)
            self.menu_bt.setStyleSheet(self.page_button_style)
            self.menu_bt.setIcon(QIcon(current_path + "/menu.png"))
            self.menu_bt.setFixedWidth(40)
            self.menu_bt.clicked.connect(self.menuButtonPress)
            self.vbox1.addWidget(self.menu_bt)
            self.menu_bt.show()

            self.setting_bt = QtWidgets.QPushButton(self)
            self.setting_bt.setStyleSheet(self.page_button_style)
            self.setting_bt.setIcon(QIcon(current_path + "/settingsicon.png"))
            self.setting_bt.setFixedWidth(40)
            self.setting_bt.clicked.connect(self.settingsButtonPress)

            self.vbox1.addWidget(self.setting_bt)
            self.vbox1.addStretch()

            self.image_label = QtWidgets.QLabel(self)
            self.image_label.setObjectName("image_label")

            self.image_label.resize(600, 450)
            # self.vbox3.addWidget(self.image_label, alignment=QtCore.Qt.AlignHCenter)

            self.label = QLabel('', self)
            self.label.setFont(Header_font)
            self.label.setStyleSheet(label_style_header)
            self.label.setObjectName("label")
            self.label.setText("Click the menu to update new faces!")
            # self.vbox2.addWidget(self.label, alignment=QtCore.Qt.AlignHCenter)

            self.search_textbox = QLineEdit(placeholderText="search")
            self.search_textbox.setStyleSheet("background-color : #ffffff")
            self.search_textbox.resize(200, 40)
            # self.hbox2.addWidget(self.search_textbox)

            self.enter_bt = QtWidgets.QPushButton(self)
            self.enter_bt.setText("Accept")
            self.enter_bt.setFixedWidth(80)
            self.enter_bt.setStyleSheet(self.regular_button_style)
            self.enter_bt.clicked.connect(self.on_enter)
            # self.hbox2.addWidget(self.enter_bt)

            self.table_style_model = QStandardItemModel()
            self.table_style_model.setHorizontalHeaderLabels(
                ['Name', 'Phone', 'Email', 'Birthdate', 'Address', 'Card', "Cvv"])
            self.table = QTableView()
            self.table.setStyleSheet("background-color : #ffffff")
            self.table.setModel(self.table_style_model)
            header = self.table.horizontalHeader()
            header.setDefaultAlignment(Qt.AlignHCenter)
            self.table.setGeometry(3, 4, 500, 450)
            # self.vbox2.addWidget(self.table)

            self.scroll = QtWidgets.QScrollArea()
            self.scroll.setStyleSheet(#"background-color : #24a5ed;"
                                      "background-color:transparent;"
                                      "")
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll.setWidgetResizable(True)
            # self.vbox2.addWidget(self.scroll)

            self.control_bt = QtWidgets.QPushButton(self)
            self.control_bt.setStyleSheet("""
            QPushButton{
                background-color: #FF0000;
                border-style: none;
                border-width:1px;
                border-radius:25px;
                border-color: red;
                max-width:50px;
                max-height:50px;
                min-width:50px;
                min-height:50px;
                color: black;
            }
            QPushButton::hover{
                border-style: solid;
                border-color: black;
                border-width:2px;
            }"""
                                          )
            self.control_bt.setText("Start")
            self.control_bt.clicked.connect(self.toggle_start_stop)

            # settings
            # menu
            self.toolbar = QToolBar("Settings")
            Account_action = QAction("Account", self)
            Account_action.triggered.connect(self.account_settingsButtonpress)
            self.toolbar.addAction(Account_action)
            Camera_action = QAction("Camera", self)
            Camera_action.triggered.connect(self.camera_settingsButtonpress)
            self.toolbar.addAction(Camera_action)
            Legal_action = QAction("Legal", self)
            Legal_action.triggered.connect(self.legal_settingsButtonpress)
            self.toolbar.addAction(Legal_action)
            self.toolbar.setStyleSheet("""
            QToolBar{
            }
            QToolButton{border-radius: 3px;
            background-color: white;
            }
            QToolButton::hover{border-color: #24a5ed;
            background-color:#f0f0f0;
            }""")
            # Account
            self.change_user_label = QLabel('Change Username', self)
            self.user_textbox = QLineEdit(placeholderText="Change Username")
            self.user_textbox.setStyleSheet("background-color : #ffffff")

            self.user_enter_bt = QtWidgets.QPushButton(self)
            self.user_enter_bt.setStyleSheet(self.regular_button_style)
            self.user_enter_bt.setText("Enter")
            self.user_enter_bt.setFixedWidth(80)
            self.user_enter_bt.clicked.connect(self.on_user_enterButton)

            self.change_pass_label = QLabel("Change Password", self)
            self.pass_textbox = QLineEdit(placeholderText="new password")
            self.pass_textbox.setStyleSheet("background-color : #ffffff")

            self.pass_check_textbox = QLineEdit(placeholderText="old password")
            self.pass_check_textbox.setStyleSheet("background-color : #ffffff")

            self.pass_enter_bt = QtWidgets.QPushButton(self)
            self.pass_enter_bt.setStyleSheet(self.regular_button_style)
            self.pass_enter_bt.setText("Enter")
            self.pass_enter_bt.setFixedWidth(80)
            self.pass_enter_bt.clicked.connect(self.on_pass_enterButton)

            self.sign_out_button = QPushButton("Sign Out", self)
            self.sign_out_button.clicked.connect(self.on_sign_out_button)
            self.sign_out_button.setStyleSheet(self.regular_button_style)

            # Camera settings page
            # Radio button(s) for settings page
            self.r1 = QRadioButton("Webcam")
            # self.r1.setChecked(False)
            self.r1.toggled.connect(self.radio1)
            # self.vbox2.addWidget(self.r1)
            self.r2 = QRadioButton("Enter New Camera Link")
            self.r2.setChecked(False)
            self.r2.toggled.connect(self.radio2)

            # New cam label
            self.new_camera_label = QLabel('', self)
            self.new_camera_label.setFont(regular_font)
            self.new_camera_label.setStyleSheet(label_style_non_header)

            # Camera textbox
            self.camera_settings_textbox = QLineEdit(self)
            self.camera_settings_textbox.setStyleSheet("background-color : #ffffff")
            # self.vbox2.addWidget(self.r2)

            # Label for combo box
            self.cb_label = QLabel('', self)
            self.cb_label.setText("Set default camera link below")
            self.cb_label.setFont(regular_font)
            self.cb_label.setStyleSheet(label_style_non_header)
            # self.vbox2.addWidget(self.cb_label, alignment=QtCore.Qt.AlignHCenter)

            # combo box for settings page
            self.cb = QComboBox()
            self.cb.setStyleSheet("background-color : #ffffff")
            # self.vbox2.addWidget(self.cb)

            # accept default rstp link button
            self.default_rstp = QtWidgets.QPushButton(self)
            self.default_rstp.setStyleSheet(self.regular_button_style)
            self.default_rstp.setText("Accept")
            self.default_rstp.setFixedWidth(80)
            self.default_rstp.clicked.connect(self.on_clicked_default_rstp)

            # Legal settings page
            self.terms_and_conditions = QTextEdit(self)
            self.terms_and_conditions.setText('Terms and Conditions\n'
                                              """Generic Terms and Conditions Template
                Please read these terms and conditions ("terms and conditions", "terms") carefully before using [website] website (“website”, "service") operated by [name] ("us", 'we", "our").
                Conditions of use
                By using this website, you certify that you have read and reviewed this Agreement and that you agree to comply with its terms. If you do not want to be bound by the terms of this Agreement, you are advised to leave the website accordingly. [name] only grants use and access of this website, its products, and its services to those who have accepted its terms.
                Privacy policy
                Before you continue using our website, we advise you to read our privacy policy [link to privacy policy] regarding our user data collection. It will help you better understand our practices.
                Age restriction
                You must be at least 18 (eighteen) years of age before you can use this website. By using this website, you warrant that you are at least 18 years of age and you may legally adhere to this Agreement. [name] assumes no responsibility for liabilities related to age misrepresentation.
                Intellectual property
                You agree that all materials, products, and services provided on this website are the property of [name], its affiliates, directors, officers, employees, agents, suppliers, or licensors including all copyrights, trade secrets, trademarks, patents, and other intellectual property. You also agree that you will not reproduce or redistribute the [name]’s intellectual property in any way, including electronic, digital, or new trademark registrations.
                You grant [name] a royalty-free and non-exclusive license to display, use, copy, transmit, and broadcast the content you upload and publish. For issues regarding intellectual property claims, you should contact the company in order to come to an agreement.
                User accounts
                As a user of this website, you may be asked to register with us and provide private information. You are responsible for ensuring the accuracy of this information, and you are responsible for maintaining the safety and security of your identifying information. You are also responsible for all activities that occur under your account or password.
                If you think there are any possible issues regarding the security of your account on the website, inform us immediately so we may address them accordingly.
                We reserve all rights to terminate accounts, edit or remove content and cancel orders at our sole discretion.
                Applicable law
                By visiting this website, you agree that the laws of the [location], without regard to principles of conflict laws, will govern these terms and conditions, or any dispute of any sort that might come between [name] and you, or its business partners and associates.
                Disputes
                Any dispute related in any way to your visit to this website or to products you purchase from us shall be arbitrated by state or federal court [location] and you consent to exclusive jurisdiction and venue of such courts.
                Indemnification
                You agree to indemnify [name] and its affiliates and hold [name] harmless against legal claims and demands that may arise from your use or misuse of our services. We reserve the right to select our own legal counsel. 
                Limitation on liability
                [name] is not liable for any damages that may occur to you as a result of your misuse of our website.
                [name] reserves the right to edit, modify, and change this Agreement at any time. We shall let our users know of these changes through electronic mail. This Agreement is an understanding between [name] and the user, and this supersedes and replaces all prior agreements regarding the use of this website.
                """)
            self.terms_and_conditions.setReadOnly(True)
            self.privacy_policy = QTextEdit(self)
            self.privacy_policy.setText('Privacy Policy'
                                        '')
            self.privacy_policy.setReadOnly(True)

            # Accept terms and conditions
            self.read_terms_and_conditions = QTextEdit()
            self.read_terms_and_conditions.setReadOnly(True)
            self.read_privacy_policy = QTextEdit()
            self.read_privacy_policy.setReadOnly(True)
            self.check_read_terms = QCheckBox("I have read and accept the terms and conditions.", self)
            self.check_read_privacypolicy = QCheckBox("I have read and accept the privacy policy.", self)
            self.accept_terms_and_policy_button = QPushButton(self)
            self.accept_terms_and_policy_button.clicked.connect(self.on_accept_terms_button)
            self.accept_terms_and_policy_button.setStyleSheet(self.regular_button_style)

            # Set  Icon for homepage
            image = cv2.imread(current_path + "/icon_512x512.png", cv2.IMREAD_UNCHANGED)
            # print("Image:", image)
            img = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
            # img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
            # flipped = cv2.flip(img, 1)
            convertQT = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGBA8888)
            pic = convertQT.scaled(512, 512, Qt.KeepAspectRatio)
            pic.createAlphaMask()
            self.ImageUpdateSlot(pic)

            # self.hbox2.addLayout(self.vbox2)
            # self.vbox2.setAlignment( Qt.AlignCenter )
            # self.layout.addLayout(self.hbox1)

            # Main Layout
            self.taskLayout = QtWidgets.QStackedLayout()
            self.setMainLayout(self.taskLayout)

            self.hbox1.addLayout(self.vbox1)
            self.hbox1.addLayout(self.taskLayout)
            self.setLayout(self.hbox1)
            # Initialize log page as defualt page
            self.loginpageButtonpress()

        def setMainLayout(self, layout):
            home = self.home()
            search = self.search()
            menu = self.menu()
            settings = self.settings()
            camera_settings = self.camera_settings()
            account_settings = self.account_settings()
            legal_settings = self.legal_settings()
            accept_terms_and_privacy = self.accept_terms_and_conditions()
            login = self.login()
            signup = self.signup()

            layout.addWidget(home)
            layout.addWidget(search)
            layout.addWidget(menu)
            layout.addWidget(settings)
            layout.addWidget(camera_settings)
            layout.addWidget(account_settings)
            layout.addWidget(legal_settings)
            layout.addWidget(accept_terms_and_privacy)
            layout.addWidget(login)
            layout.addWidget(signup)

        def home(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            layout.addWidget(self.label, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.image_label, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.control_bt, alignment=QtCore.Qt.AlignHCenter)

            return widget

        def search(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            layout.addWidget(self.search_textbox)
            layout.addWidget(self.table)

            return widget

        def menu(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            layout.addWidget(self.scroll)

            return widget

        def settings(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            layout.addWidget(self.toolbar, alignment=QtCore.Qt.AlignTop)

            return widget

        def camera_settings(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            layout.addStretch()
            layout.addWidget(self.r1)
            layout.addWidget(self.r2)
            layout.addStretch()
            layout.addWidget(self.new_camera_label, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.camera_settings_textbox)
            layout.addWidget(self.enter_bt)
            layout.addStretch()
            layout.addWidget(self.cb_label, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.cb)
            layout.addWidget(self.default_rstp)
            layout.addStretch()
            return widget

        def account_settings(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            hbox1 = QHBoxLayout()
            hbox1.addWidget(self.user_textbox)
            hbox1.addWidget(self.user_enter_bt)

            hbox2 = QHBoxLayout()
            vbox1 = QVBoxLayout()
            vbox1.addWidget(self.pass_check_textbox)
            vbox1.addWidget(self.pass_textbox)
            hbox2.addLayout(vbox1)
            hbox2.addWidget(self.pass_enter_bt, QtCore.Qt.AlignBottom)

            layout.addStretch()
            layout.addWidget(self.change_user_label)
            layout.addLayout(hbox1)
            layout.addStretch()
            layout.addWidget(self.change_pass_label)
            layout.addLayout(hbox2)
            layout.addStretch()
            layout.addWidget(self.sign_out_button, alignment=QtCore.Qt.AlignBottom)

            return widget

        def legal_settings(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            layout.addWidget(self.terms_and_conditions)
            layout.addWidget(self.privacy_policy)

            return widget

        def accept_terms_and_conditions(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            layout.addWidget(self.read_terms_and_conditions)
            layout.addWidget(self.read_privacy_policy)
            layout.addWidget(self.check_read_terms, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.check_read_privacypolicy, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.accept_terms_and_policy_button, alignment=QtCore.Qt.AlignHCenter)

            return widget

        def login(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            layout.addStretch()
            layout.addWidget(self.login_label, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.login_username, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.login_password, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.login_button, alignment=QtCore.Qt.AlignHCenter)
            hbox = QHBoxLayout()
            # hbox.setSpacing(0)
            hbox.addStretch()
            # hbox.setContentsMargins(int(self.width()/2),0,0,0)
            hbox.addWidget(self.remember_device_label)
            hbox.addWidget(self.remember_this_device)
            hbox.addStretch()
            layout.addLayout(hbox)
            layout.addWidget(self.signupfromloginpage, alignment=QtCore.Qt.AlignHCenter)
            layout.addStretch()
            self.home_btn.hide()
            self.search_btn.hide()
            self.menu_bt.hide()
            self.setting_bt.hide()

            return widget

        def signup(self):
            widget = QtWidgets.QWidget(self)
            layout = QVBoxLayout(widget)
            layout.addWidget(self.back_signuppage, QtCore.Qt.AlignLeft)
            layout.addStretch()
            layout.addWidget(self.signup_label, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.signup_password_rules, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.signup_email, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.create_username, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.create_password, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.create_password_check, alignment=QtCore.Qt.AlignHCenter)
            layout.addWidget(self.signup_button, alignment=QtCore.Qt.AlignHCenter)
            layout.addStretch()
            return widget

        def homeButtonPress(self):
            self.reload_detector_thread()
            self.MainActive = False
            image = cv2.imread(current_path + "/icon_512x512.png", cv2.IMREAD_UNCHANGED)
            img = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
            # flipped = cv2.flip(img, 1)
            convertQT = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGBA8888)
            pic = convertQT.scaled(512, 512, Qt.KeepAspectRatio)
            pic.createAlphaMask()
            self.ImageUpdateSlot(pic)

            self.control_bt.setText("Start")
            self.label.setText("Click the Menu to update new faces!")
            self.taskLayout.setCurrentIndex(0)

        def searchButtonPress(self):
            self.reload_detector_thread()
            self.MainActive = True
            self.toggle_start_stop()
            # Call search filter function
            self.search_button()
            self.taskLayout.setCurrentIndex(1)

        def menuButtonPress(self):
            self.MainActive = True
            self.toggle_start_stop()
            self.reload_detector_thread()
            # function variables
            self.widget = QWidget()
            self.unknown_pictures = []
            self.unknown_face_ids = []
            self.unknown_face_encodings = []

            ##################################################
            # Extract data from database to load unknown faces
            print("Loading unknown faces...")

            # get pictures
            self.mycursor.execute(f"SELECT image from {self.current_account_id}unknown_faces")
            images = self.mycursor.fetchall()

            # get id's
            self.mycursor.execute(f"SELECT id FROM {self.current_account_id}unknown_faces")
            ids = self.mycursor.fetchall()

            # get encoding's
            self.mycursor.execute(f"SELECT face_encoding FROM {self.current_account_id}unknown_faces")
            encodings = self.mycursor.fetchall()
            ########################################################################
            # insert ids, encodings, and pictures into function lists at top
            filepath = current_path + "/image.png"
            self.vscrollbox = QVBoxLayout()

            i = 1
            for row in images:
                # print("Length of images:", len(images))
                # print("Image in images:", image)
                for img in row:
                    # print("Length of row:", len(row))
                    # print("img in image:", img)
                    with open(filepath, "wb") as File:
                        img_ = pickle.loads(img)
                        File.write(img_)
                        File.close()

                    # Convert the bytes into a PIL image( not as good as pickle.loads)
                    # img = Image.open(io.BytesIO(base64.b64decode(img)))

                    # cv2 show image
                    img = cv2.imread(filepath)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    convertQT = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)
                    pic = convertQT.scaled(640, 480, Qt.KeepAspectRatio)

                    # Create image for scroll box
                    self.unknown_pictures.append(img)
                    self.image = QtWidgets.QLabel(self)
                    self.image.setPixmap(QPixmap.fromImage(pic))

                    # Create Label/button for scroll box
                    self.scroll_label = QLabel('Update Face# ', self)
                    #self.scroll_label.setStyleSheet("color:white")
                    self.scroll_btn = QtWidgets.QPushButton(self)
                    self.scroll_btn.setText(str(i))
                    self.scroll_btn.setFixedWidth(90)
                    self.scroll_btn.setStyleSheet(self.regular_button_style)
                    self.scroll_btn.clicked.connect(self.scrollbtn_clicked)
                    self.delete_label = QLabel("Delete # ", self)
                    self.delete_btn = QPushButton(self)
                    self.delete_btn.setText(str(i))
                    self.delete_btn.setStyleSheet(""" 
                        background-color: red;
                        border-style: none;
                        border-width:1px;
                        border-radius:5px;
                        border-color: red;
                        max-width:25px;
                        max-height:20px;
                        min-width:25px;
                        min-height:20px;
                        color: black;""")
                    self.delete_btn.clicked.connect(self.delete_unknown)

                    # Add image and id/label/button to scrollbox layout
                    hbox = QHBoxLayout()
                    hbox.addStretch()
                    hbox.addWidget(self.scroll_label)
                    hbox.addWidget(self.scroll_btn)
                    hbox.addStretch()
                    hbox.addWidget(self.delete_label)
                    hbox.addWidget(self.delete_btn)
                    hbox.addStretch()
                    self.vscrollbox.addLayout(hbox)
                    self.vscrollbox.addWidget(self.image)
                    self.vscrollbox.addStretch()
                    i = i + 1

            # self.setLayout(self.hbox1)
            # self.image.show()
            print("...Pictures loaded")

            for id_ in ids:
                self.unknown_face_ids.append(id_)
            print("...Unknown id's loaded")

            for encoding in encodings:
                # The result is also in a tuple
                for face_stored_pickled_data in encoding:
                    face_data = pickle.loads(face_stored_pickled_data)
                    self.unknown_face_encodings.append(face_data)
                    # print("Loaded pickle:", face_data )
            print("...Unknown faces loaded.")

            ###########################################
            ############ Create Scroll Window #########
            # Scroll area
            self.scroll.show()

            # widgets holds all of the images and labels in the scroll area
            self.widgets = QWidget()
            self.widgets.setLayout(self.vscrollbox)

            self.scroll.setWidget(self.widgets)

            self.taskLayout.setCurrentIndex(2)

        def settingsButtonPress(self):
            self.MainActive = True
            self.toggle_start_stop()

            self.taskLayout.setCurrentIndex(3)

        def camera_settingsButtonpress(self):
            self.load_defaultcam_cb()
            self.enter_bt.hide()
            self.camera_settings_textbox.hide()
            if self.r2.isChecked():
                self.radio2()

            self.taskLayout.setCurrentIndex(4)

        def account_settingsButtonpress(self):
            self.taskLayout.setCurrentIndex(5)

        def legal_settingsButtonpress(self):
            self.taskLayout.setCurrentIndex(6)

        def accept_terms_and_privacy_policyButtonpress(self):
            self.taskLayout.setCurrentIndex(7)

        def loginpageButtonpress(self):
            self.taskLayout.setCurrentIndex(8)
            self.login_label.setText("Login")
            user, pass_ = self.check_for_saved_login_info()
            if user and pass_:
                self.login_username.setText(user)
                self.login_password.setText(pass_)
                self.remember_this_device.setChecked(True)

        def signuppageButtonpress(self):
            self.taskLayout.setCurrentIndex(9)

        def check_db_user_exists(self):
            hostname = socket.gethostname()
            self.local_ip = socket.gethostbyname(hostname)

            self.mycursor.execute("SELECT user FROM mysql.user;")
            users = self.mycursor.fetchall()

            print(users)
            print(self.local_ip)
            exit(0)

        def DBconnect(self):
            try:
                # username: administrator, password: password
                #10.111.1.48
                self.db = mdb.connect(host='127.0.0.1', user='root', database='root', password='#####')
                # self.label.setText('Connected to Database.')

            except mdb.Error as e:
                QMessageBox.about(self, "Connect", "Failed to connect to Database")

            self.mycursor = self.db.cursor()

        def reload_detector_thread(self):
            self.thread.db_load_face_encodings()
            self.thread.db_load_unknown_encodings()
            self.thread.db_load_known_face_names()
            self.thread.db_entry_times()
            self.thread.db_check_date_change()
            self.db.commit()
            print("...Detector Reloaded")

        def form_window(self):

            if self.popup.formActive is False or self.popup.isHidden():
                print("Opening form window...")
                # self.popup = form_popup()
                self.thread.popup = self.popup
                self.popup.setGeometry(QRect(100, 100, 400, 200))
                self.popup.show()
                self.popup.formActive = True

                self.popup.nameupdate.connect(self.nameUpdateSlot)

            # self.thread.nameUpdateSlot.connect(self.popup.nameupdate)

        def radio1(self):
            if self.r1.isChecked():
                self.new_camera_label.hide()
                self.camera_settings_textbox.hide()
                self.enter_bt.hide()
                self.thread.camera_address = 0

        def radio2(self):
            if self.r2.isChecked():
                self.new_camera_label.show()
                self.enter_bt.show()
                self.camera_settings_textbox.show()
                self.new_camera_label.setText("Enter an Address for the IP Camera")

        def scrollbtn_clicked(self, delete=False):
            sender = self.sender()
            text = sender.text()
            self.scroll_image_index = int(text) - 1
            # print('Scroll button:', scroll_image_index)
            if delete == False:
                # Call form_window function to open user form
                self.form_window()

        def form_accept_updateslot(self, str):
            # pickle dumps face encoding
            print(self.scroll_image_index)
            face_data = pickle.dumps(self.unknown_face_encodings[self.scroll_image_index])
            self.mycursor.execute(
                f"INSERT INTO {self.current_account_id}Client (name, known_face_encodings) VALUES (%s, %s)",
                (str, face_data)
            )
            self.mycursor.execute(f"DELETE FROM {self.current_account_id}unknown_faces WHERE face_encoding = %s",
                                  (face_data,)
                                  )
            self.db.commit()
            # Reload menu page(widgets) while user is on page
            self.menuButtonPress()

        def delete_unknown(self):
            self.scrollbtn_clicked(delete=True)
            face_data = pickle.dumps(self.unknown_face_encodings[self.scroll_image_index])
            self.mycursor.execute(f"DELETE FROM {self.current_account_id}unknown_faces WHERE face_encoding = %s",
                                  (face_data,)
                                  )
            self.db.commit()
            self.menuButtonPress()

        def search_button(self):
            # self.table = QTableView()
            # init data class and proxy(filter) model then assign filter model to textbox for searching
            self.data = self.get_account_data()
            if len(self.data) != 0:
                print("Initializing data model...")
                self.data_class = data_source(self.data)
                self.proxy_model = QSortFilterProxyModel()
                self.proxy_model.setFilterKeyColumn(-1)  # Search all columns.
                self.proxy_model.setSourceModel(self.data_class)
                self.proxy_model.sort(0, Qt.AscendingOrder)
                self.search_textbox.textChanged.connect(self.search_textbox_changed)

                # while the user is on the admin page show labels or filter search if they are typing or not
                # print("Textbox empty.")
                # self.table.setModel(self.table_style_model)

        def search_textbox_changed(self):
            self.search_textbox.textChanged.connect(self.proxy_model.setFilterFixedString)
            print("User searching...")
            if self.search_textbox.text() == "" or self.search_textbox.text() == " ":
                self.table.setModel(self.table_style_model)
                return 0
            self.table.setModel(self.proxy_model)

        def toggle_start_stop(self):
            if not self.MainActive:
                # if detecting is turned on
                self.setWindowTitle("Detecting")
                # self.label.setText('Click start to begin detecting')

                self.thread.ThreadActive = True
                self.reload_detector_thread()
                self.thread.start()
                # self.image_label.show()
                # self.change_question()

                self.control_bt.setText("Stop")
                self.MainActive = True

            else:
                # if detecting is turned off
                self.setWindowTitle("Face Detector")
                self.MainActive = False
                self.thread.stop()

                self.control_bt.setText("Start")

        def on_enter(self):
            print("On enter function called.")
            text = self.camera_settings_textbox.text()
            self.camera_settings_textbox.setText('')
            if self.r2.isChecked():
                if text == "0" or text == "1" or text == "2":
                    text = int(text)
                # Test the new link
                self.new_camera_label.setText('Testing new camera')
                cap = cv2.VideoCapture(text)
                if cap is None or not cap.isOpened():
                    self.new_camera_label.setText('Warning: unable to open video source: ' + str(text))
                else:
                    self.thread.camera_address = text
                    self.save_camaddress(str(text))
                    self.new_camera_label.setText("Successfully connected to camera.")
                    AllItems = [self.cb.itemText(i) for i in range(self.cb.count())]
                    if text in AllItems == False:
                        self.cb.addItem(text)
                self.load_defaultcam_cb()

        def on_clicked_default_rstp(self):
            self.mycursor.execute(f"SELECT cam FROM {self.current_account_id}default_cam")
            cams = self.mycursor.fetchall()
            if len(cams) != 0:
                self.mycursor.execute(f"DELETE FROM {self.current_account_id}default_cam")
                self.db.commit()

            current_cam = self.cb.currentText()
            self.mycursor.execute(
                f"INSERT INTO {self.current_account_id}default_cam (cam) VALUES (" + "'" + current_cam + "')")
            self.db.commit()
            if current_cam == '0' or current_cam == 1 or current_cam == 2:
                current_cam = int(current_cam)
            self.thread.camera_address = current_cam
            self.cb_label.setText("Default Set Succesfully.Choose a new link to reset.")

        def save_camaddress(self, text):
            in_db = False
            self.mycursor.execute(f"SELECT address FROM {self.current_account_id}cameras")
            addresses = self.mycursor.fetchall()
            if len(addresses) == 0:
                self.mycursor.execute(f"INSERT INTO {self.current_account_id}cameras (address) VALUES('{text}')")
                self.db.commit()
                return 0
            for row in addresses:
                for address in row:
                    # print("Addresses:",text, address)
                    if text == address:
                        in_db = True
                        break
            if not in_db:
                print("Camera address to insert:", text)
                self.mycursor.execute(
                    f"INSERT INTO {self.current_account_id}cameras (address) VALUES(" + "'" + text + "'" + ")")
                self.db.commit()

        def on_accept_terms_button(self):
            return 0

        def on_user_enterButton(self):
            return 0

        def on_pass_enterButton(self):
            return 0

        def on_login_button(self):
            username_text = self.login_username.text()
            password_text = self.login_password.text()

            username_status = self.check_username_exists(username_text)
            email_status = self.check_email_exists_in_userdb(username_text)

            if username_status:
                login_status = self.confirm_login(password_text, username_=username_text)
            elif email_status:
                login_status = self.confirm_login(password_text, email_=username_text)
            else:
                self.login_label.setText("Username or email not found.")
                return 0
            # Successfull Log in
            if login_status:
                # Load Account info
                self.get_account_id(username_text)
                self.load_account_data()
                # Check for saved Login Encryption
                if self.remember_this_device.isChecked() and os.stat(current_path + "/deviceinfo.dat").st_size == 0:
                    self.remember_device(username_text, password_text)

                # show page buttons and redirect to homepage
                self.home_btn.show()
                self.search_btn.show()
                self.menu_bt.show()
                self.setting_bt.show()
                self.login_username.clear()
                self.login_password.clear()
                self.homeButtonPress()
            else:
                self.login_label.setText("Password Incorrect.")

        def on_signup_button(self):
            email_text = self.signup_email.text()
            username_text = self.create_username.text()
            password_text = self.create_password.text()
            password_check_text = self.create_password_check.text()

            email_status = self.check_email(email_text)
            username_status = self.check_username_exists(username_text)
            password_status = self.check_password_valid(password_text)

            if not email_status or not password_status or password_check_text != password_text or username_status:
                if not email_status:
                    self.signup_label.setText("Email is not valid.")
                    self.signup_email.setStyleSheet(self.invalid_textbox)
                if username_status:
                    self.signup_label.setText("Username already exists.")
                    self.create_username.setStyleSheet(self.invalid_textbox)
                if not password_status:
                    self.signup_label.setText("Password is Invalid.")
                    self.create_password.setStyleSheet(self.invalid_textbox)
                if password_check_text != password_text:
                    self.signup_label.setText("Passwords do not match.")
                    self.create_password_check.setStyleSheet(self.invalid_textbox)
            else:
                # Susscessfull account creation
                print("Creating new account...")
                self.signup_email.setStyleSheet(self.valid_textbox)
                self.create_username.setStyleSheet(self.valid_textbox)
                self.create_password.setStyleSheet(self.valid_textbox)
                self.create_password_check.setStyleSheet(self.valid_textbox)
                # Insert new account data into table
                self.mycursor.execute("INSERT INTO device_account (username,password,email) VALUES (%s, %s, %s)",
                                      (username_text, password_text, email_text))
                self.db.commit()
                id = self.get_account_id(username_text)

                # Create New Account tables
                self.mycursor.execute(
                    f"CREATE TABLE {id}Client (name VARCHAR(100), known_face_encodings BLOB, pk INT AUTO_INCREMENT PRIMARY KEY NOT NULL);")
                self.mycursor.execute(
                    f"CREATE TABLE {id}unknown_faces (id INT AUTO_INCREMENT PRIMARY KEY NOT NULL, face_encoding BLOB, image LONGBLOB);")
                self.mycursor.execute(
                    f"CREATE TABLE {id}Client_account (id INT AUTO_INCREMENT PRIMARY KEY NOT NULL, name VARCHAR(100), phone_number VARCHAR(100), email VARCHAR(100), birth_date VARCHAR(100), address VARCHAR(100), card_number VARCHAR(40), expiration_date VARCHAR(100), security_code VARCHAR(100));")
                self.mycursor.execute(
                    f"CREATE TABLE {id}cameras (id INT AUTO_INCREMENT PRIMARY KEY NOT NULL, address VARCHAR(100));")
                self.mycursor.execute(
                    f"CREATE TABLE {id}default_cam (id INT AUTO_INCREMENT PRIMARY KEY NOT NULL, cam VARCHAR(100));")
                self.mycursor.execute(f"""CREATE TABLE `root`.`{id}month` (
                                          `id` INT NOT NULL AUTO_INCREMENT,
                                          `name` VARCHAR(45) NULL,
                                          `entry` VARCHAR(45) NULL,
                                          `exit` VARCHAR(45) NULL,
                                          `date` VARCHAR(45) NULL,
                                          PRIMARY KEY (`id`));""")
                self.mycursor.execute(
                    f"CREATE TABLE `root`.`{id}Today` (`name` VARCHAR(100) NULL, `entry` VARCHAR(100) NULL, `exit` VARCHAR(100) NULL, `date` VARCHAR(45) NULL);")
                # self.signup_label.setText("Signup successful! \nConfirmation email has been sent.")
                self.signup_email.clear()
                self.create_username.clear()
                self.create_password.clear()
                self.create_password_check.clear()
                # redirect to login page
                self.loginpageButtonpress()
                print("...new account created.")

        def load_account_data(self):
            print("Account Data Loading...")
            # initialize detector thread variables and signal slots
            self.thread = Thread()
            self.thread.current_account_id = self.current_account_id
            self.load_defaultcam()
            if self.default_cam == None:
                self.default_cam = 0
            self.thread.camera_address = self.default_cam
            self.thread.ImageUpdate.connect(self.ImageUpdateSlot)
            self.thread.labelupdate.connect(self.labelupdateslot)

            # Initialize(load) data from database
            self.thread.db_connect_thread(self.db, self.mycursor)
            #self.reload_detector_thread()

            # initialize popup form
            self.popup = form_popup()
            self.popup.nameupdate.connect(self.form_accept_updateslot)
            self.popup.db_connect_thread(self.db, self.mycursor)
            self.popup.current_account_id = self.current_account_id
            self.popup.load_existing_cb()
            print("...Account", self.current_account_id, "loaded")

        def get_account_id(self, username):
            self.mycursor.execute(f"SELECT id FROM device_account WHERE username='{username}';")
            id_fetch = self.mycursor.fetchall()
            id = None
            for row in id_fetch:
                for i in row:
                    id = i
            self.current_account_id = id
            return id

        def remember_device(self, user, password):
            userb = bytes(user, 'utf-8')
            passb = bytes(password, 'utf-8')

            cipher_encrypt = Fernet(self.key)
            ciphered_user = cipher_encrypt.encrypt(userb)
            ciphered_pass = cipher_encrypt.encrypt(passb)
            # print(ciphered_user, ciphered_pass)

            file = current_path + "/deviceinfo.dat"
            with open(file, "wb") as f:
                pickle.dump(self.key, f)
                pickle.dump(ciphered_user, f)
                pickle.dump(ciphered_pass, f)
            print("Login Saved")
            return True

        def check_for_saved_login_info(self):
            file = current_path + "/deviceinfo.dat"
            with open(file, "rb") as f:
                if os.stat(file).st_size == 0:
                    return False, False
                key = pickle.load(f)
                user_ = pickle.load(f)
                pass_ = pickle.load(f)

            cipher_decrypt = Fernet(key)
            decrypted_user = cipher_decrypt.decrypt(user_)
            decrypted_pass = cipher_decrypt.decrypt(pass_)

            user_ = decrypted_user.decode("utf-8")
            pass_ = decrypted_pass.decode("utf-8")
            # print("Decryption", decrypted_user, decrypted_pass)

            return user_, pass_

        def on_sign_out_button(self):
            self.home_btn.hide()
            self.search_btn.hide()
            self.menu_bt.hide()
            self.setting_bt.hide()
            self.cb.clear()
            self.loginpageButtonpress()

        def check_email(self, email):
            api_key = "7b5779ad-ec4c-4f76-ac0a-0b91d8f34e92"  # API Key goes here

            email_address = email
            response = requests.get(
                "https://isitarealemail.com/api/email/validate",
                params={'email': email_address},
                headers={'Authorization': "Bearer " + api_key})

            status = response.json()['status']
            if status == "valid":
                print("email is valid")
                return True
            elif status == "invalid":
                print("email is invalid")
                return False
            else:
                print("email was unknown")
                return True

        def check_username_exists(self, username):
            self.mycursor.execute("SELECT username FROM device_account")
            usernames = self.mycursor.fetchall()
            for row in usernames:
                for u in row:
                    if u == username:
                        return True
            return False

        def check_email_exists_in_userdb(self, email):
            self.mycursor.execute("SELECT email FROM device_account")
            emails = self.mycursor.fetchall()
            for row in emails:
                for e in row:
                    if e == email:
                        return True
            return False

        def confirm_login(self, password, username_=False, email_=False):
            if username_ is not False:
                self.mycursor.execute(f"SELECT password FROM device_account WHERE username = '{username_}';")
            elif email_ is not False:
                self.mycursor.execute(f"SELECT password FROM device_account WHERE email = '{email_}';")
            else:
                print("Username and email params == False.")

            useroremail = self.mycursor.fetchall()
            for row in useroremail:
                if password in row:
                    print("Login Succesfull")
                    return True
            print("Login Failed.")
            return False

        def check_password_valid(self, password):
            if len(password) < 8:
                return False
            elif re.search('[0-9]', password) is None:
                return False
            elif re.search('[A-Z]', password) is None:
                return False
            else:
                return True

        def load_defaultcam(self):
            self.mycursor.execute(f"SELECT cam FROM {self.current_account_id}default_cam")
            cam = self.mycursor.fetchall()
            for row in cam:
                for c in row:
                    if c == '0' or c == '1' or c == '2':
                        c = int(c)
                    self.default_cam = c

        def load_defaultcam_cb(self):
            AllItems = [self.cb.itemText(i) for i in range(self.cb.count())]
            self.mycursor.execute(f"SELECT address FROM {self.current_account_id}cameras")
            addresses = self.mycursor.fetchall()
            if len(addresses) == 0:
                return 0
            for row in addresses:
                for address in row:
                    if address not in AllItems:
                        self.cb.addItem(address)

        def get_account_data(self):
            # self.mycursor.execute("INSERT INTO Client_account (name, phone_number, email, birth_date, address, card number, expiration_date, security_code) VALUES ( ) ")
            self.mycursor.execute(f"SELECT * FROM {self.current_account_id}Client_account")
            data = self.mycursor.fetchall()
            # print("Account Data:", data)
            return data

        def listupdateslot(self, item):
            self.list.insertItem(self.list_iterator, item)
            self.list_iterator += 1

        def textboxupdateslot(self, bool_):
            if bool_:
                self.on_enter()

        def ImageUpdateSlot(self, image):
            self.image_label.setPixmap(QPixmap.fromImage(image))

        def labelupdateslot(self):
            if self.thread.currentname != '' and self.MainActive:
                string = "Hey " + self.thread.currentname + "!"
                self.label.setText(string)
            else:
                self.label.setText('')

        def nameUpdateSlot(self, str_):
            self.thread.name = str_
            self.thread.string = ''

        def send_email(self, subject="Make AI Today",
                       text="", img=None, attachment=None):

            # build message contents
            msg = MIMEMultipart()

            # Add Subject
            msg['Subject'] = subject

            # Add text contents
            msg.attach(MIMEText(text))

            # Check if we have anything
            # given in the img parameter
            if img is not None:

                # Check whether we have the
                # lists of images or not!
                if type(img) is not list:
                    # if it isn't a list, make it one
                    img = [img]

                # Now iterate through our list
                for one_img in img:
                    # read the image binary data
                    img_data = open(one_img, 'rb').read()

                    # Attach the image data to MIMEMultipart
                    # using MIMEImage,
                    # we add the given filename use os.basename
                    msg.attach(MIMEImage(img_data,
                                         name=os.path.basename(one_img)))

            # We do the same for attachments
            # as we did for images
            if attachment is not None:

                # Check whether we have the
                # lists of attachments or not!
                if type(attachment) is not list:
                    # if it isn't a list, make it one
                    attachment = [attachment]

                for one_attachment in attachment:
                    with open(one_attachment, 'rb') as f:
                        # Read in the attachment using MIMEApplication
                        file = MIMEApplication(
                            f.read(),
                            name=os.path.basename(one_attachment)
                        )
                    file['Content-Disposition'] = f'attachment; filename="{os.path.basename(one_attachment)}"'

                    # At last, Add the attachment to our message object
                    msg.attach(file)
            return msg

        def mail(self, to=None, msg=None):

            # initialize connection to our email server,
            # we will use gmail here
            smtp = smtplib.SMTP('smtp.gmail.com', 587)
            smtp.ehlo()
            smtp.starttls()

            # Login with your email and password
            smtp.login('makeAItoday@gmail.com', '')

            # Provide some data to the sendmail function!
            smtp.sendmail(from_addr="makeAItoday@gmail.com",
                          to_addrs=to, msg=msg.as_string())

            # Finally, don't forget to close the connection
            smtp.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # create and show mainWindow
    print("Initializing Mainwindow Object...")
    mainWindow = MainWindow()
    print("Window Ready")

    mainWindow.show()
    print("Displaying window...\n")

    sys.exit(app.exec_())

""" pyinstaller main_window.py --onedir --windowed --paths venv/lib/python3.8/site-packages/face_recognition_models/models --collect-all face_recognition_models --add-data Resources_/*.png:. --noconfirm 

"""
