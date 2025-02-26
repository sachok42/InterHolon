import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QListWidget, QListWidgetItem, QLabel, QSplitter, QSizePolicy, QTextEdit, QComboBox, QMainWindow, QStackedWidget
from PyQt6.QtGui import QIcon, QTextOption
from PyQt6.QtCore import Qt

class Message:
    def __init__(self, sender, text):
        self.sender = sender
        self.text = text

    def display_text(self):
        return f"{self.sender}: {self.text}"

class MessageWidget(QWidget):
    def __init__(self, message):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QTextEdit()
        self.label.setReadOnly(True)
        self.label.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.label.setText(message.display_text())
        layout.addWidget(self.label)

class MistakesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Mistakes')
        layout = QVBoxLayout()
        label = QLabel("This is the Mistakes Window")
        layout.addWidget(label)
        self.setLayout(layout)

class RequestsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Requests')
        layout = QVBoxLayout()
        label = QLabel("This is the Requests Window")
        layout.addWidget(label)
        self.setLayout(layout)

class ProfileWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Profile')
        layout = QVBoxLayout()
        label = QLabel("This is the Profile Window")
        layout.addWidget(label)
        self.setLayout(layout)

class MessengerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Beautiful Messenger')
        self.setWindowIcon(QIcon('path/to/your/icon.png'))  # Set your own icon path here
        self.resize(800, 600)

        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        self.layout = QVBoxLayout()
        self.centralWidget.setLayout(self.layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter)

        self.chatList = QListWidget()
        self.splitter.addWidget(self.chatList)
        self.chatList.setFixedWidth(200)

        self.rightPanel = QWidget()
        self.rightPanelLayout = QVBoxLayout()
        self.rightPanel.setLayout(self.rightPanelLayout)
        self.splitter.addWidget(self.rightPanel)

        self.messageTypeCombo = QComboBox()
        self.messageTypeCombo.addItem("Personal")
        self.messageTypeCombo.addItem("Group")
        self.messageTypeCombo.currentIndexChanged.connect(self.switchMessageType)
        self.rightPanelLayout.addWidget(self.messageTypeCombo)

        self.messageDisplay = QListWidget()
        self.rightPanelLayout.addWidget(self.messageDisplay)

        self.inputLayout = QHBoxLayout()
        self.textInput = QTextEdit()
        self.textInput.setPlaceholderText("Type your message here...")
        self.textInput.setMinimumHeight(50)
        self.textInput.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.textInput.textChanged.connect(self.adjustTextEditHeight)
        self.sendButton = QPushButton('Send')
        self.sendButton.clicked.connect(self.sendMessage)

        self.inputLayout.addWidget(self.textInput)
        self.inputLayout.addWidget(self.sendButton)
        self.rightPanelLayout.addLayout(self.inputLayout)

        self.buttonsLayout = QHBoxLayout()
        self.mistakesButton = QPushButton('Mistakes')
        self.requestsButton = QPushButton('Requests')
        self.profileButton = QPushButton('Profile')
        self.buttonsLayout.addWidget(self.mistakesButton)
        self.buttonsLayout.addWidget(self.requestsButton)
        self.buttonsLayout.addWidget(self.profileButton)
        self.rightPanelLayout.addLayout(self.buttonsLayout)

        self.setLayout(self.layout)

        self.mistakesWindow = MistakesWindow()
        self.requestsWindow = RequestsWindow()
        self.profileWindow = ProfileWindow()

        self.mistakesButton.clicked.connect(self.showMistakesWindow)
        self.requestsButton.clicked.connect(self.showRequestsWindow)
        self.profileButton.clicked.connect(self.showProfileWindow)

    def showMistakesWindow(self):
        self.mistakesWindow.show()

    def showRequestsWindow(self):
        self.requestsWindow.show()

    def showProfileWindow(self):
        self.profileWindow.show()

    def switchMessageType(self):
        message_type = self.messageTypeCombo.currentText()
        # Handle switching message type logic here
        print(f"Switched to {message_type} messages")

    def adjustTextEditHeight(self):
        doc = self.textInput.document()
        doc.setTextWidth(self.textInput.viewport().width())
        height = doc.size().height()
        self.textInput.setFixedHeight(max(50, int(height) + 10))

    def sendMessage(self):
        text = self.textInput.toPlainText()
        if text:
            message = Message(sender="You", text=text)
            item = QListWidgetItem()
            widget = MessageWidget(message)
            item.setSizeHint(widget.sizeHint())
            self.messageDisplay.addItem(item)
            self.messageDisplay.setItemWidget(item, widget)
            self.textInput.clear()
            self.adjustTextEditHeight()

def main():
    app = QApplication(sys.argv)
    messenger = MessengerApp()
    messenger.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
