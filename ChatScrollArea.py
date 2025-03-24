from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton

class ChatScrollArea(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)

		# Scroll Area
		self.scroll_area = QScrollArea(self)
		self.scroll_area.setWidgetResizable(True)

		# Container for messages
		self.messages_container = QWidget()
		self.messages_layout = QVBoxLayout(self.messages_container)
		self.messages_layout.setSpacing(5)
		self.scroll_area.setWidget(self.messages_container)

		# Button to add messages (for testing)
		self.add_message_button = QPushButton("Add Message")
		self.add_message_button.clicked.connect(self.add_message)

		# Main layout
		self.main_layout = QVBoxLayout(self)
		self.main_layout.addWidget(self.scroll_area)
		self.main_layout.addWidget(self.add_message_button)

	def add_message(self, text="This is a new message!"):
		msg = MessageWidget(text)
		self.messages_layout.addWidget(msg)
		self.messages_container.adjustSize()  # Adjust size for proper scrolling
