import sys
from userside_final_values import LOGO_PATH, SCREEN_SIZE
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, \
    QHBoxLayout, QComboBox, QFrame, QScrollArea, QFormLayout
from PyQt5.QtCore import Qt
from client_implementation.user_data import UserData, generate_string
from general_system_functions import open_account, open_node_account, get_node_approval


class HomePage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Create a QLabel to display the image
        image_label = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        image_label.setPixmap(pixmap.scaledToWidth(int(SCREEN_SIZE.width / 3)))  # Adjust the desired width
        layout.addWidget(image_label)

        label = QLabel("Welcome to the Orion User Interface")
        label.setStyleSheet("QLabel { color: darkblue; font-size: 36px; }")
        layout.addWidget(label)

        login_button = QPushButton("Log In")
        login_button.setStyleSheet("QPushButton { font-size: 24px; }")
        login_button.clicked.connect(self.show_login_page)
        layout.addWidget(login_button)

        create_account_button = QPushButton("Create Account")
        create_account_button.setStyleSheet("QPushButton { font-size: 24px; }")
        create_account_button.clicked.connect(self.show_create_account_page)  # Updated connection
        layout.addWidget(create_account_button)

        self.setLayout(layout)

    def show_create_account_page(self):
        # Switch to the create account page
        self.parent().setCentralWidget(AccountsInfoPage(self.parent()))

    def show_login_page(self):
        # Switch to the login page
        self.parent().setCentralWidget(LoginPage(self.parent()))


class AccountsInfoPage(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        layout = QHBoxLayout()

        # Logo layout
        image_label = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        image_label.setPixmap(pixmap.scaledToWidth(int(SCREEN_SIZE.width / 2.5)))  # Adjust the desired width
        layout.addWidget(image_label)

        # client account
        options_layout = QVBoxLayout()
        options_layout.setAlignment(Qt.AlignCenter)

        client_title_label = QLabel("Open a Client Account")
        client_title_label.setStyleSheet("QLabel { color: darkblue; font-size: 36px; }")
        options_layout.addWidget(client_title_label)

        client_description_label = QLabel("Store, manage, and manipulate data in the OrionDB data storage system. \nUtilize the OrionDB user interface and our Python API.")
        client_description_label.setStyleSheet("QLabel { font-size: 24px; }")
        options_layout.addWidget(client_description_label)

        client_button = QPushButton("Open Client Account")
        client_button.setStyleSheet("QPushButton { font-size: 24px; }")
        client_button.clicked.connect(self.show_create_client_account_page)
        options_layout.addWidget(client_button)

        # node account
        node_title_label = QLabel("\n\nOpen Node Management Account")
        node_title_label.setStyleSheet("QLabel { color: darkblue; font-size: 36px; }")
        options_layout.addWidget(node_title_label)

        node_description_label = QLabel("Allocate personal memory space and \nparticipate in a groundbreaking new database system")
        node_description_label.setStyleSheet("QLabel { font-size: 24px; }")
        options_layout.addWidget(node_description_label)

        node_button = QPushButton("Open Node Account")
        node_button.setStyleSheet("QPushButton { font-size: 24px; }")
        node_button.clicked.connect(self.show_create_node_account_page)
        options_layout.addWidget(node_button)

        layout.addLayout(options_layout)

        self.setLayout(layout)

    def show_create_client_account_page(self):
        # Switch to the create client account page
        self.parent.setCentralWidget(OpenClientAccountPage(self.parent))

    def show_create_node_account_page(self):
        # Switch to the create node account page
        self.parent.setCentralWidget(OpenNodeAccountPage(self.parent))


class OpenNodeAccountPage(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Create a QHBoxLayout for the logo and "Log In" text
        logo_text_layout = QHBoxLayout()

        # Create a QLabel to display the logo
        logo_label = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        logo_label.setPixmap(pixmap.scaledToWidth(int(SCREEN_SIZE.width / 10)))  # Adjust the desired width
        logo_text_layout.addWidget(logo_label)

        label = QLabel("Open Node Management Account")
        label.setStyleSheet("QLabel { color: darkblue; font-size: 36px; }")
        logo_text_layout.addWidget(label)

        # Set the logo and "Log In" text layout to align in the center horizontally
        logo_text_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(logo_text_layout)

        input_layout = QVBoxLayout()
        input_layout.setAlignment(Qt.AlignCenter)

        username_label = QLabel("Username:")
        username_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.username_input = QLineEdit()
        self.username_input.setStyleSheet("QLineEdit { font-size: 24px; }")
        self.username_input.setFixedWidth(int(SCREEN_SIZE.width / 3))  # Set the desired width
        input_layout.addWidget(username_label)
        input_layout.addWidget(self.username_input)

        password_label = QLabel("Password:")
        password_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.password_input = QLineEdit()
        self.password_input.setStyleSheet("QLineEdit { font-size: 24px; }")
        self.password_input.setFixedWidth(int(SCREEN_SIZE.width / 3))  # Set the desired width
        self.password_input.setEchoMode(QLineEdit.Password)
        input_layout.addWidget(password_label)
        input_layout.addWidget(self.password_input)

        memory_label = QLabel("Requested Memory to Allocate:")
        memory_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.memory_input = QLineEdit()
        self.memory_input.setStyleSheet("QLineEdit { font-size: 24px; }")
        self.memory_input.setFixedWidth(int(SCREEN_SIZE.width / 3))  # Set the desired width
        input_layout.addWidget(memory_label)
        input_layout.addWidget(self.memory_input)

        layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)

        login_button = QPushButton("Create Account")
        login_button.setStyleSheet("QPushButton { font-size: 24px; }")
        login_button.clicked.connect(self.open_account)
        button_layout.addWidget(login_button)

        back_button = QPushButton("Back")
        back_button.setStyleSheet("QPushButton { font-size: 24px; }")
        back_button.clicked.connect(self.show_home_page)
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def open_account(self):
        username = self.username_input.text()
        password = self.password_input.text()
        memory = self.memory_input.text()

        approval, confirmation_code = get_node_approval(memory)
        if not approval:
            UserData().redirected_flag = True
            UserData().response_string = 'Node not approved at this time.'
            self.parent.setCentralWidget(OpenNodeAccountPage(self.parent))

        confirm = True
        connection_string = open_node_account(username, password, memory, confirmation_code)
        if connection_string is None:
            confirm = False

        UserData().redirected_flag = True
        if not confirm:
            # display response code
            UserData().response_string = 'Invalid account information. Input is either invalid, \nor is already assigned to another account. Please try again.'
            # return to current page
            self.parent.setCentralWidget(OpenNodeAccountPage(self.parent))
        else:
            UserData().response_string = 'Node Management account created.'
            self.parent.setCentralWidget(LoginPage(self.parent))

    def show_home_page(self):
        # Switch to the home page
        self.parent.setCentralWidget(HomePage())


class OpenClientAccountPage(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Create a QHBoxLayout for the logo and "Log In" text
        logo_text_layout = QHBoxLayout()

        # Create a QLabel to display the logo
        logo_label = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        logo_label.setPixmap(pixmap.scaledToWidth(int(SCREEN_SIZE.width / 10)))  # Adjust the desired width
        logo_text_layout.addWidget(logo_label)

        label = QLabel("Open Client Account")
        label.setStyleSheet("QLabel { color: darkblue; font-size: 36px; }")
        logo_text_layout.addWidget(label)

        # Set the logo and "Log In" text layout to align in the center horizontally
        logo_text_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(logo_text_layout)

        input_layout = QVBoxLayout()
        input_layout.setAlignment(Qt.AlignCenter)

        username_label = QLabel("Username:")
        username_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.username_input = QLineEdit()
        self.username_input.setStyleSheet("QLineEdit { font-size: 24px; }")
        self.username_input.setFixedWidth(int(SCREEN_SIZE.width / 3))  # Set the desired width
        input_layout.addWidget(username_label)
        input_layout.addWidget(self.username_input)

        password_label = QLabel("Password:")
        password_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.password_input = QLineEdit()
        self.password_input.setStyleSheet("QLineEdit { font-size: 24px; }")
        self.password_input.setFixedWidth(int(SCREEN_SIZE.width / 3))  # Set the desired width
        self.password_input.setEchoMode(QLineEdit.Password)
        input_layout.addWidget(password_label)
        input_layout.addWidget(self.password_input)

        layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)

        login_button = QPushButton("Create Account")
        login_button.setStyleSheet("QPushButton { font-size: 24px; }")
        login_button.clicked.connect(self.open_account)
        button_layout.addWidget(login_button)

        back_button = QPushButton("Back")
        back_button.setStyleSheet("QPushButton { font-size: 24px; }")
        back_button.clicked.connect(self.show_home_page)
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)

        # add response if necessary
        if UserData().redirected_flag:
            response_layout = QHBoxLayout()
            response_layout.setAlignment(Qt.AlignCenter)
            response = QLabel(UserData().response_string)
            response.setStyleSheet("QLabel { font-size: 24px; }")
            response_layout.addWidget(response)
            UserData().response_string = ''
            UserData().redirected_flag = False
            layout.addLayout(response_layout)

        self.setLayout(layout)

    def open_account(self):
        username = self.username_input.text()
        password = self.password_input.text()
        confirm = True
        connection_string = open_account(username, password)
        if connection_string is None:
            confirm = False

        UserData().redirected_flag = True
        if not confirm:
            # display response code
            UserData().response_string = 'Invalid account information. Input is either invalid, \nor is already assigned to another account. Please try again.'
            # return to current page
            self.parent.setCentralWidget(OpenClientAccountPage(self.parent))
        else:
            UserData().response_string = 'Client account created.'
            self.goto_login_page()

    def show_home_page(self):
        # Switch to the home page
        self.parent.setCentralWidget(HomePage())

    def goto_login_page(self):
        # Switch to the login page
        self.parent.setCentralWidget(LoginPage(self.parent))


class LoginPage(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Create a QHBoxLayout for the logo and "Log In" text
        logo_text_layout = QHBoxLayout()

        # Create a QLabel to display the logo
        logo_label = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        logo_label.setPixmap(pixmap.scaledToWidth(int(SCREEN_SIZE.width / 10)))  # Adjust the desired width
        logo_text_layout.addWidget(logo_label)

        label = QLabel("Login Page")
        label.setStyleSheet("QLabel { color: darkblue; font-size: 36px; }")
        logo_text_layout.addWidget(label)

        # Set the logo and "Log In" text layout to align in the center horizontally
        logo_text_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(logo_text_layout)

        input_layout = QVBoxLayout()
        input_layout.setAlignment(Qt.AlignCenter)

        username_label = QLabel("Username:")
        username_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.username_input = QLineEdit()
        self.username_input.setStyleSheet("QLineEdit { font-size: 24px; }")
        self.username_input.setFixedWidth(int(SCREEN_SIZE.width / 3))  # Set the desired width
        input_layout.addWidget(username_label)
        input_layout.addWidget(self.username_input)

        password_label = QLabel("Password:")
        password_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.password_input = QLineEdit()
        self.password_input.setStyleSheet("QLineEdit { font-size: 24px; }")
        self.password_input.setFixedWidth(int(SCREEN_SIZE.width / 3))  # Set the desired width
        self.password_input.setEchoMode(QLineEdit.Password)
        input_layout.addWidget(password_label)
        input_layout.addWidget(self.password_input)

        account_type_label = QLabel("Select Account Type:")
        account_type_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.account_type_combo = QComboBox()
        self.account_type_combo.setStyleSheet("QComboBox { font-size: 24px; }")
        self.account_type_combo.addItem("Client Account")
        self.account_type_combo.addItem("Node Management Account")
        input_layout.addWidget(account_type_label)
        input_layout.addWidget(self.account_type_combo)

        layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)

        login_button = QPushButton("Log In")
        login_button.setStyleSheet("QPushButton { font-size: 24px; }")
        login_button.clicked.connect(self.login)
        button_layout.addWidget(login_button)

        back_button = QPushButton("Back")
        back_button.setStyleSheet("QPushButton { font-size: 24px; }")
        back_button.clicked.connect(self.show_home_page)
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)

        # add response if necessary
        if UserData().redirected_flag:
            response_layout = QHBoxLayout()
            response_layout.setAlignment(Qt.AlignCenter)
            response = QLabel(UserData().response_string)
            response.setStyleSheet("QLabel { font-size: 24px; }")
            response_layout.addWidget(response)
            UserData().response_string = ''
            UserData().redirected_flag = False
            layout.addLayout(response_layout)

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        account_type = self.account_type_combo.currentText()
        # Process the login based on the selected account type
        ac_type = 'account' if account_type == 'Client Account' else 'node'
        string = generate_string(username, password, ac_type)
        confirm = UserData().initialize_connector(string)
        if confirm:
            UserData().username = username
            UserData().password = password
            if ac_type == 'account':
                self.parent.setCentralWidget(ClientHomePage(self.parent))
            else:
                self.parent.setCentralWidget(NodeHomePage(self.parent))
        else:
            UserData().redirected_flag = True
            self.parent.setCentralWidget(LoginPage(self.parent))

    def show_home_page(self):
        # Switch to the home page
        self.parent.setCentralWidget(HomePage())


class NodeHomePage(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        # Create the main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # Create the logo and account information layout
        account_layout = QVBoxLayout()

        # Add the logo
        logo_label = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        logo_label.setPixmap(pixmap.scaledToWidth(int(SCREEN_SIZE.width / 10)))
        account_layout.addWidget(logo_label)

        # Add the account name
        account_name_label = QLabel(f'Account: {UserData().username}')
        account_name_label.setStyleSheet("QLabel { font-size: 24px; font-weight: bold; }")
        account_layout.addWidget(account_name_label)

        # Add the allocated memory
        allocated_memory_label = QLabel("Allocated Memory: 100 GB")
        allocated_memory_label.setStyleSheet("QLabel { font-size: 18px; }")
        account_layout.addWidget(allocated_memory_label)

        # Add the used memory
        used_memory_label = QLabel("Used Memory: 50 GB")
        used_memory_label.setStyleSheet("QLabel { font-size: 18px; }")
        account_layout.addWidget(used_memory_label)

        # Add the memory usage percentage
        memory_percentage_label = QLabel("Memory Usage: 50%")
        memory_percentage_label.setStyleSheet("QLabel { font-size: 18px; }")
        account_layout.addWidget(memory_percentage_label)

        layout.addLayout(account_layout)

        # Create the storage manipulation layout
        storage_layout = QVBoxLayout()

        # Add the "Add Storage" section
        add_storage_layout = QFormLayout()
        self.add_storage_input = QLineEdit()
        add_storage_layout.addRow(QLabel('\n\n'))
        add_storage_layout.addRow("Add Storage:", self.add_storage_input)
        add_storage_button = QPushButton("Add")
        add_storage_button.setStyleSheet("QPushButton { font-size: 18px; }")
        add_storage_button.clicked.connect(self.add_storage)
        add_storage_layout.addRow(add_storage_button)
        add_storage_layout.addRow(QLabel('\n\n'))
        storage_layout.addLayout(add_storage_layout)

        # Add the "Drop Storage" section
        drop_storage_layout = QFormLayout()
        self.drop_storage_input = QLineEdit()
        drop_storage_layout.addRow("Drop Storage:", self.drop_storage_input)
        drop_storage_button = QPushButton("Drop")
        drop_storage_button.setStyleSheet("QPushButton { font-size: 18px; }")
        drop_storage_button.clicked.connect(self.drop_storage)
        drop_storage_layout.addRow(drop_storage_button)
        drop_storage_layout.addRow(QLabel('\n\n'))
        storage_layout.addLayout(drop_storage_layout)

        layout.addLayout(storage_layout)

        # Add the logout of account button
        delete_layout = QVBoxLayout()
        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet("QPushButton { font-size: 24px; }")
        logout_button.clicked.connect(self.logout)
        delete_layout.addWidget(logout_button)
        layout.addLayout(delete_layout)

        # Add the delete account button
        delete_layout = QVBoxLayout()
        delete_account_button = QPushButton("Delete Account")
        delete_account_button.setStyleSheet("QPushButton { font-size: 24px; }")
        delete_account_button.clicked.connect(self.delete_account)
        delete_layout.addWidget(delete_account_button)
        layout.addLayout(delete_layout)

        self.setLayout(layout)

    def delete_account(self):
        # account deletion
        UserData().connector.withdraw_as_node(generate_string(UserData().username, UserData().password, 'node'))

    def add_storage(self):
        # storage addition
        storage_input = self.add_storage_input.text()
        # Use the storage_input value as needed
        UserData().connector.request_additional_memory_allocation(storage_input)

    def drop_storage(self):
        # storage dropping
        storage_input = self.drop_storage_input.text()
        # Use the storage_input value as needed
        UserData().connector.lower_allocated_memory_space(storage_input)

    def logout(self):
        UserData().username = None
        UserData().password = None
        UserData().account_type = None
        UserData().connector.disconnect()
        self.parent.setCentralWidget(LoginPage(self.parent))


class ClientHomePage(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        # Create main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Left side (Account information)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        logo_label.setPixmap(pixmap.scaledToWidth(int(SCREEN_SIZE.width / 2.75)))
        left_layout.addWidget(logo_label, alignment=Qt.AlignCenter)

        # Account name
        account_name_label = QLabel(f'Account: {UserData().username}')
        account_name_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        left_layout.addWidget(account_name_label)

        # buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)

        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet("font-size: 18px; background-color: white;")
        logout_button.clicked.connect(self.handle_logout)
        buttons_layout.addWidget(logout_button)
        if UserData().redirected_flag and UserData().response_string == 'logout':
            verify_logout_button = QPushButton("Confirm logout")
            verify_logout_button.setStyleSheet("font-size: 18px; background-color: lightgrey;")
            verify_logout_button.clicked.connect(self.confirm_logout)
            buttons_layout.addWidget(verify_logout_button)
            UserData().redirected_flag = False
            UserData().response_string = ''

        connection_string_button = QPushButton("Generate Connection String")
        connection_string_button.setStyleSheet("font-size: 18px; background-color: white;")
        connection_string_button.clicked.connect(self.generate_connection_string)
        buttons_layout.addWidget(connection_string_button)
        if UserData().redirected_flag and UserData().response_string == 'connection string':
            string_label = QLabel(f'Connection string: "{generate_string(UserData().username, UserData().password, "account")}"')
            string_label.setStyleSheet("font-size: 24px; font-weight: bold")
            buttons_layout.addWidget(string_label)
            UserData().redirected_flag = False
            UserData().response_string = ''

        buttons_layout.addStretch()

        left_layout.addLayout(buttons_layout)
        main_layout.addLayout(left_layout)

        # Right side (Database list)
        right_layout = QVBoxLayout()

        # Account databases title
        account_dbs_title_label = QLabel("Account Databases")
        account_dbs_title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        right_layout.addWidget(account_dbs_title_label)

        # Database list scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # get database names
        database_names = list(UserData().connector.account_dbs.keys())
        database_names.extend(list(UserData().connector.local_dbs.keys()))

        if len(database_names) == 0:
            no_db_label = QLabel("No databases found.")
            no_db_label.setStyleSheet("font-size: 18px; font-style: italic;")
            scroll_layout.addWidget(no_db_label, alignment=Qt.AlignCenter)
        else:
            # Add database segments
            for db_name in database_names:
                db_segment = QFrame()
                db_segment.setFrameShape(QFrame.Panel)
                db_segment.setFrameShadow(QFrame.Sunken)
                db_layout = QVBoxLayout(db_segment)

                db_label = QLabel(db_name)
                db_label.setStyleSheet("font-size: 20px;")
                db_layout.addWidget(db_label)

                browse_button = QPushButton("Browse Data")
                browse_button.setObjectName(db_name)  # Set the objectName to the database name
                browse_button.setStyleSheet("font-size: 16px; background-color: white;")
                browse_button.clicked.connect(self.browse_data)
                db_layout.addWidget(browse_button)

                scroll_layout.addWidget(db_segment)

        scroll_area.setWidget(scroll_content)
        right_layout.addWidget(scroll_area)

        # update system data button
        open_db_button = QPushButton("Upload All Data To System")
        if UserData().redirected_flag and UserData().response_string == 'updated':
            open_db_button.setStyleSheet("font-size: 18px; background-color: lightgrey;")
            UserData().redirected_flag = False
            UserData().response_string = ''
        else:
            open_db_button.setStyleSheet("font-size: 18px; background-color: white;")
        open_db_button.clicked.connect(self.update_system_data)
        right_layout.addWidget(open_db_button)

        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def browse_data(self):
        sender = self.sender()
        db_name = sender.objectName()
        if db_name not in UserData().connector.cache.keys():
            _ = UserData().connector[db_name]
        self.parent.setCentralWidget(DatabasePage(self.parent, db_name))

    def update_system_data(self):
        UserData().connector.update_system_data()
        UserData().redirected_flag = True
        UserData().response_string = 'updated'
        self.parent.setCentralWidget(ClientHomePage(self.parent))

    def generate_connection_string(self):
        UserData().redirected_flag = True
        UserData().response_string = 'connection string'
        self.parent.setCentralWidget(ClientHomePage(self.parent))

    def handle_logout(self):
        UserData().redirected_flag = True
        UserData().response_string = 'logout'
        self.parent.setCentralWidget(ClientHomePage(self.parent))

    def confirm_logout(self):
        UserData().username = None
        UserData().password = None
        UserData().account_type = None
        UserData().connector.disconnect()
        self.parent.setCentralWidget(LoginPage(self.parent))


class DatabasePage(QWidget):
    def __init__(self, parent, db_name):
        super().__init__()

        self.parent = parent
        self.db_name = db_name

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        # Create a QHBoxLayout for the logo and buttons
        logo_button_layout = QHBoxLayout()

        # Create a QLabel to display the logo
        logo_label = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        logo_label.setPixmap(pixmap.scaledToWidth(int(SCREEN_SIZE.width / 10)))  # Adjust the desired width
        logo_button_layout.addWidget(logo_label)
        # Create a button to go back to the home page
        home_button = QPushButton("Home")
        home_button.setStyleSheet("QPushButton { font-size: 24px; }")
        home_button.clicked.connect(self.show_home_page)
        logo_button_layout.addWidget(home_button)

        # Create a button to delete the database
        delete_db_button = QPushButton("Delete DB")
        delete_db_button.setStyleSheet("QPushButton { font-size: 24px; }")
        delete_db_button.setObjectName(self.db_name)
        delete_db_button.clicked.connect(self.delete_database)
        logo_button_layout.addWidget(delete_db_button)

        # Set the logo and buttons layout to align in the center horizontally
        logo_button_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(logo_button_layout)
        # Add a label for the database name
        db_name_label = QLabel(f"Database: {db_name}")
        db_name_label.setStyleSheet("QLabel { font-size: 28px; font-weight: bold; }")
        layout.addWidget(db_name_label)

        # Add a scroll area for the collection list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        # Create a widget to contain the collection list
        collection_list_widget = QWidget()
        scroll_area.setWidget(collection_list_widget)

        collection_layout = QVBoxLayout(collection_list_widget)
        collection_layout.setAlignment(Qt.AlignTop)
        # Fetch the collection data from the cache
        if db_name in UserData().connector.cache.keys():
            collection_data = UserData().connector.cache[db_name].to_dict()
        else:
            collection_data = UserData().connector.local_dbs[db_name].to_dict()
        if collection_data:
            # Iterate over each collection and create a segment for it
            for collection_name, items in collection_data.items():
                # Create a button to expand/collapse the collection segment
                collection_button = QPushButton(collection_name)
                collection_button.setStyleSheet("QPushButton { font-size: 24px; font-weight: bold; }")
                collection_button.setObjectName(collection_name)
                collection_button.clicked.connect(self.toggle_collection)
                collection_layout.addWidget(collection_button)

                # Create a widget to contain the items in the collection
                collection_widget = QWidget()
                collection_layout.addWidget(collection_widget)

                collection_inner_layout = QVBoxLayout(collection_widget)

                if UserData().redirected_flag and UserData().response_string == collection_name:
                    UserData().redirected_flag = False
                    UserData().response_string = ''
                    # Iterate over each item in the collection and create labels to display item data
                    for item_id, item_data in items.items():
                        item_label = QLabel(f"Item Data: {item_data}")
                        item_label.setStyleSheet("QLabel { font-size: 15px; }")
                        collection_inner_layout.addWidget(item_label)

                collection_layout.addLayout(collection_inner_layout)
        else:
            # If there are no collections, display a message
            no_collections_label = QLabel("No collections found.")
            no_collections_label.setStyleSheet("QLabel { font-size: 20px; }")
            collection_layout.addWidget(no_collections_label)

        self.setLayout(layout)

    def toggle_collection(self):
        UserData().redirected_flag = True
        UserData().response_string = self.sender().objectName()
        self.parent.setCentralWidget(DatabasePage(self.parent, self.db_name))

    def show_home_page(self):
        # Switch to the home page
        self.parent.setCentralWidget(ClientHomePage(self.parent))

    def delete_database(self):
        # Implement database deletion logic here
        del UserData().connector[self.sender().objectName()]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OrionDB User Interface")

        # Calculate the new size
        new_width = SCREEN_SIZE.width // 3
        new_height = SCREEN_SIZE.height // 3

        # Set the geometry of the main window
        self.setGeometry(100, 100, new_width, new_height)

        # Set the background color to white
        self.setStyleSheet("background-color: white;")

        # Apply a dark blue frame style
        self.setStyleSheet("QMainWindow { border: 2px solid darkblue; }")

        self.home_page = HomePage()
        self.setCentralWidget(self.home_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    sys.exit(app.exec_())
