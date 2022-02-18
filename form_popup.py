from ui_main_window import *
from data_model import *
from PyQt5.QtWidgets import *

class form_popup(QDialog):
    # signal variables
    nameupdate = pyqtSignal(str)
    def __init__(self):
        super(form_popup, self).__init__()
        self.setStyleSheet("color: #24a5ed;"
                           "background-color: #f0f0f0;"
                           # "border-style: solid;"
                           # "border-width: 2px;"
                           # "border-color: #ffffff"
                           )
        self.current_account_id = None
        self.createForm()
        self.formActive = False

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.form)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def createForm(self):
        self.name = QLineEdit(self)
        self. phone = QLineEdit(self)
        self.email = QLineEdit(self)
        self.birth_date = QLineEdit(self)
        self.address = QLineEdit(self)
        self.card = QLineEdit(self)
        self.expiration = QLineEdit(self)
        self.cvv = QLineEdit(self)
        self.existing_cb = QComboBox()
        self.existing_cb.setStyleSheet("background-color : #ffffff")
        self.existing_cb.setFixedWidth(self.name.width()+30)
        self.existing_cb.addItem("No")

        self.form = QGroupBox("New Client Information")
        self.form.setStyleSheet("color: #24a5ed;"
                           "background-color: #f0f0f0;"
                           # "border-style: solid;"
                           # "border-width: 2px;"
                           # "border-color: #ffffff"
                           )
        layout = QFormLayout()
        layout.addRow(QLabel("Existing Person?:"), self.existing_cb)
        layout.addRow(QLabel("Name:"), self.name)
        layout.addRow(QLabel("Cellphone:"), self.phone)
        layout.addRow(QLabel("Email:"), self.email)
        layout.addRow(QLabel("Birth date:"), self.birth_date)
        layout.addRow(QLabel("Address:"), self.address)
        layout.addRow(QLabel("Card number:"), self.card)
        layout.addRow(QLabel("Expiration:"), self.expiration)
        layout.addRow(QLabel("CVV:"), self.cvv)
        self.form.setLayout(layout)

    def db_connect_thread(self, db, cursor):
        self.db = db
        self.mycursor = cursor

    def accept(self):
        # insert client account data into db
        name = self.name.text()
        phone =self.phone.text()
        email =self.email.text()
        birthdate =self.birth_date.text()
        address =self.address.text()
        card_number =self.card.text()
        expiration =self.expiration.text()
        cvv =self.cvv.text()

        if self.existing_cb.currentText()  == "No":
            #insert new account data into database table Client_account
            self.mycursor.execute(f"INSERT INTO {self.current_account_id}Client_account (name, phone_number, email, birth_date, address, card_number, expiration_date, security_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                              (name, phone, email, birthdate, address, card_number, expiration, cvv))
            self.db.commit()
            self.nameupdate.emit(name)
        else:
            # update name for face encoding given by the form
            self.nameupdate.emit(self.existing_cb.currentText())

        # clear all textboxes
        self.name.setText('')
        self.phone.setText('')
        self.email.setText('')
        self.birth_date.setText('')
        self.address.setText('')
        self.card.setText('')
        self.expiration.setText('')
        self.cvv.setText('')
        self.hide()
        self.load_existing_cb()
        self.formActive = False

    def reject(self):
        self.formActive = False
        self.hide()

    def load_existing_cb(self):
        AllItems = [self.existing_cb.itemText(i) for i in range(self.existing_cb.count())]
        self.mycursor.execute(f"SELECT name FROM {self.current_account_id}Client_account")
        addresses = self.mycursor.fetchall()
        if len(addresses) == 0:
            return 0
        for row in addresses:
            for address in row:
                if address not in AllItems:
                    self.existing_cb.addItem(address)
