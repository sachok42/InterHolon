import stanza

class POS_tagger:
	def __init__(self, language):
		self.nlp = stanza.Pipeline(language, processors='tokenize,mwt,pos')

	def tag_text(self, text):
		doc = self.nlp(text)
		
		# Extract tokens and their POS tags
		pos_tags = []
		for sentence in doc.sentences:
			pos_tags.append([])
			for word in sentence.words:
				pos_tags[-1].append((word.text, word.pos))
		
		return pos_tags