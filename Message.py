import string
from protocol import *

class Message:
	def __init__(self, content, sender=None, chat=None, language=None):
		self.content = content
		self.sender = sender
		self.chat = chat
		self.language = language

	def analyze(self, spellchecker):
		def preprocess_text(text):
			# Remove punctuation
			text = text.translate(str.maketrans("", "", string.punctuation))
			return text
		# print(f"started analysis of message {self.content}")
		mistakes = []
		text = preprocess_text(self.content)
		words = text.split()
		print(f"content is {text}, words are {words}")
		# misspelled = spellchecker.lookup_list(text)
		# print(f"wrong words are {misspelled}")
		# indexes = [words.index(mistake) for mistake in misspelled]
		for i in range(len(words)):
			word = words[i]
			# print(f"i is {i}, word is {word}")
			if not spellchecker.lookup(word):
				corrections_lowered = [variant.lower() for variant in spellchecker.suggest(word)]
				logger.info(f"[MESSAGE] on analyze: found mistake, suggestions are {', '.join(corrections_lowered)}")
				try:
					correction = corrections_lowered[0]
				except:
					correction = "unknown"

				mistakes.append({"type": "typo", "word_number": i, "corrected_word": correction, "original": word})
		print(f"mistakes are {mistakes}")
		return mistakes