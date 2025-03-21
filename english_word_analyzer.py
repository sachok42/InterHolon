from SpeechPart import SpeechPart

pronouns = {"i", "you", "he", "she", "it", "they"}
conjuctions = {"and", "or"}

class EnglishWordAnalyzer:
	def __init__(self):
		self.pronouns = {*pronouns}

	def get_speech_part(self, word) -> SpeechPart:
		word = word.lower()
		length = len(word)

		if word in pronouns: return SpeechPart.PRONOUN

		if word in conjuctions: return SpeechPart.CONJUCTION

		if length < 3:
			return SpeechPart.PREPOSITION

		if word[-3:] == 'ion':
			return SpeechPart.NOUN
