import phunspell
import spellchecker as sp
from log_protocol import *


class Spellchecker:
	def __init__(self, _spellchecker):
		self._spellchecker = _spellchecker
		if not self.Im_Phunspell() and not self.Im_spellchecker():
			custom_log(f"[Spellchecker]: undetected spellchecker")
			raise Exception
		custom_log(f"[SpellChecker] spellchecker initialized")

	def Im_Phunspell(self):
		return type(self._spellchecker) == phunspell.phunspell.Phunspell

	def Im_spellchecker(self):
		return type(self._spellchecker) == sp.spellchecker.SpellChecker

	def lookup(self, word):
		custom_log(f"[Spellchecker] on lookup: word is {word}")
		if self.Im_Phunspell():
			return self._spellchecker.lookup(word)

		elif self.Im_spellchecker():
			return self._spellchecker.correction(word) == word
	
	def correction(self, word):
		# custom_log(f"[Spellchecker] on correction: word is {word}")
		if self.Im_Phunspell():
			corrections_lowered = [variant.lower() for variant in self._spellchecker.suggest(word)]
			logger.info(f"[MESSAGE] on correction: found mistake, suggestions are {', '.join(corrections_lowered)}")
			try:
				correction = corrections_lowered[0]
			except:
				correction = "unknown"
			return correction

		elif self.Im_spellchecker():
			correction = self._spellchecker.correction(word)
			return correction