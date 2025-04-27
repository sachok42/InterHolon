class Spellchecker:
	def __init__(_spellchecker):
		self._spellchecker = _spellchecker

	def Im_Phunspell(self):
		return type(self._spellchecker) == phunspell.phunspell.Phunspell

	def Im_spellchecker(self):
		return type(self._spellchecker) == sp.spellchecker.SpellChecker

	def lookup(self, word):
		if self.Im_Phunspell():
			return self._spellchecker.lookup(word)

		elif self.Im_spellchecker():
			return self._spellchecker.suggestion(word) == word

		print("undetected type")
		raise Exception
	
	def correction(self, word):
		if self.Im_Phunspell():
			corrections_lowered = [variant.lower() for variant in self._spellchecker.suggest(word)]
			logger.info(f"[MESSAGE] on analyze: found mistake, suggestions are {', '.join(corrections_lowered)}")
			try:
				correction = corrections_lowered[0]
			except:
				correction = "unknown"
			return correction

		elif self.Im_spellchecker():
			correction = self._spellchecker.correction(word)
			return correction