class Message:
	def __init__(self, content, sender=None, timestamp=None, chat=None, receiver=None):
		self.content = content
		self.sender = sender
		self.chat = chat
		self.timestamp = timestamp

	def analyze(self, my_spellchecker):
		print(f"started analysis of message {self.content}")
		mistakes = []
		words = self.content.split()
		print(f"words are {words}")
		for i in range(len(words)):
			print(f"i is {i}")
			word = words[i]
			correction = my_spellchecker.correction(word)
			if correction != word:
				mistakes.append({"type": "typo", "word_number": i, "corrected_word": correction})
		print(f"mistakes are {mistakes}")
		return mistakes