import stanza
from protocol import mwt_languages

class POS_tagger:
	def __init__(self, language):
		if language in mwt_languages:
			processors = "tokenize,mwt,pos"
		else:
			processors = "tokenize,pos"
		self.nlp = stanza.Pipeline(language, processors=processors)

	def tag_text(self, text):
		doc = self.nlp(text)
		
		# Extract tokens and their POS tags
		pos_tags = []
		for sentence in doc.sentences:
			pos_tags.append([])
			for word in sentence.words:
				pos_tags[-1].append((word.text, word.pos))
		
		return pos_tags