from PyQt6.QtWidgets import QMessageBox

def PushNotification(text: str):
	box = QMessageBox
	box.setText(text)
	box.exec()