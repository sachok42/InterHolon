from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QColor

class MessageWidget(QTextEdit):
	def __init__(self, words_with_tags, pos_colors=None, parent=None):
		"""
		:param words_with_tags: List of (word, POS_tag) tuples OR a simple text string.
		:param pos_colors: Dictionary mapping POS tags to hex colors.
		"""
		super().__init__(parent)
		self.setReadOnly(True)
		self.setMaximumHeight(80)  # Adjusted for better UI
		self.setMinimumHeight(40)
		self.setWordWrapMode(3)  # QTextOption.WrapAtWordBoundaryOrAnywhere
		
		if isinstance(words_with_tags, str):
			self.setText(words_with_tags)  # Display as plain text
		else:
			self.apply_colored_text(words_with_tags, pos_colors or {})

	def apply_colored_text(self, words_with_tags, pos_colors):
		"""Apply word color based on POS tags."""
		self.clear()
		cursor = self.textCursor()

		for word, pos_tag in words_with_tags:
			fmt = QTextCharFormat()
			fmt.setForeground(QColor(pos_colors.get(pos_tag, "#000000")))  # Default black
			cursor.setCharFormat(fmt)
			cursor.insertText(f"{word} ")  # Add space between words
