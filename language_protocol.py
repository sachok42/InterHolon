from PyQt6.QtGui import QColor, QTextCharFormat

languages = ["English", "German", "Spanish", "Russian", "Hebrew", "Ukranian"]
# Function to validate language structure (optional utility)
def validate_language_tree(language_tree):
	"""
	Validates the structure of the LANGUAGE_TREE.
	Ensures every branch is a dictionary and leaves are lists.
	"""
	if not isinstance(language_tree, dict):
		raise TypeError("LANGUAGE_TREE must be a dictionary at the root level.")
	for family, subfamilies in language_tree.items():
		if not isinstance(subfamilies, dict):
			raise TypeError(f"Subfamilies under '{family}' must be dictionaries.")
		for subfamily, languages in subfamilies.items():
			if not isinstance(languages, list):
				raise TypeError(f"Languages under '{subfamily}' in '{family}' must be lists.")

# Base group categories for organizing languages
base_groups = ["Collective", "Indo-European", "Semitic", "Uralic"] # Placeholder for broader linguistic categories or roles

# Language families and subfamilies with examples
LANGUAGE_TREE = {
	"Indo-European": {
		"Germanic": ["English", "German", "Dutch"],
		"Romance": ["Spanish", "French", "Italian"],
		"Slavic": ["Russian", "Polish", "Czech"]
	},
	"Semitic": {
		"Arabic": [],  # Future extensions can populate dialects or variations
		"Hebrew": []
	},
	"Uralic": {
		"Finnic": ["Finnish", "Estonian"],
		"Ugric": ["Hungarian"]
	}
}

RTL_langs = {
	"Hebrew",
	"Arabic"
}

POS_color_map = {
	"ADJ": "#FFD700",  # Gold (Adjectives describe qualities)
	"ADP": "#8A2BE2",  # Blue Violet (Adpositions like prepositions)
	"ADV": "#FF69B4",  # Hot Pink (Adverbs modify verbs/adjectives)
	"AUX": "#FF4500",  # Orange Red (Auxiliary verbs)
	"CCONJ": "#00CED1",  # Dark Turquoise (Coordinating conjunctions)
	"DET": "#FFA07A",  # Light Salmon (Determiners like articles)
	"INTJ": "#BA55D3",  # Medium Orchid (Interjections express emotion)
	"NOUN": "#1E90FF",  # Dodger Blue (Nouns represent things)
	"NUM": "#32CD32",  # Lime Green (Numerals represent numbers)
	"PART": "#FF6347",  # Tomato (Particles like negation)
	"PRON": "#6A5ACD",  # Slate Blue (Pronouns replace nouns)
	"PROPN": "#4682B4",  # Steel Blue (Proper nouns are specific names)
	"PUNCT": "#A9A9A9",  # Dark Gray (Punctuation marks)
	"SCONJ": "#20B2AA",  # Light Sea Green (Subordinating conjunctions)
	"SYM": "#808080",   # Gray (Symbols like $, %)
	"VERB": "#DC143C",  # Crimson (Verbs represent actions)
	"X": "#D3D3D3",     # Light Gray (Other/unknown)
}

language_names_to_shortnames = {
	"English": "en",
	"Hebrew": "he",
	"Spanish": "es",
	"French": "fr",
	"German": "de",
	"Russian": "ru",
	"Arabic": "ar",
	"Chinese": "zh",
	"Japanese": "ja",
	"Korean": "ko",
	"Italian": "it",
	"Portuguese": "pt",
	"Dutch": "nl",
	"Turkish": "tr",
	"Hindi": "hi",
	"Greek": "el",
	"Polish": "pl",
	"Finnish": "fi",
	"Swedish": "sv",
	"Danish": "da",
	"Norwegian": "no",
	"Hungarian": "hu",
	"Czech": "cs",
	"Thai": "th",
	"Vietnamese": "vi",
	"Ukrainian": "uk"
}


shortnames_to_phunspell_names = {
	"en": "en_US",  # English (United States)
	"he": "he_IL",  # Hebrew (Israel)
	"es": "es_ES",  # Spanish (Spain)
	"fr": "fr_FR",  # French (France)
	"de": "de_DE",  # German (Germany)
	"ru": "ru_RU",  # Russian (Russia)
	"ar": "ar_SA",  # Arabic (Saudi Arabia)
	"zh": "zh_CN",  # Chinese (China)
	"ja": "ja_JP",  # Japanese (Japan)
	"ko": "ko_KR",  # Korean (South Korea)
	"it": "it_IT",  # Italian (Italy)
	"pt": "pt_PT",  # Portuguese (Portugal)
	"nl": "nl_NL",  # Dutch (Netherlands)
	"tr": "tr_TR",  # Turkish (Turkey)
	"hi": "hi_IN",  # Hindi (India)
	"el": "el_GR",  # Greek (Greece)
	"pl": "pl_PL",  # Polish (Poland)
	"fi": "fi_FI",  # Finnish (Finland)
	"sv": "sv_SE",  # Swedish (Sweden)
	"da": "da_DK",  # Danish (Denmark)
	"no": "no_NO",  # Norwegian (Norway)
	"hu": "hu_HU",  # Hungarian (Hungary)
	"cs": "cs_CZ",  # Czech (Czech Republic)
	"th": "th_TH",  # Thai (Thailand)
	"vi": "vi_VN",  # Vietnamese (Vietnam)
	"uk": "uk_UA" 	# Ukranian (Ukrain)
}

full_names_to_phunspell_names = {
	"English": "en_US",  	# English (United States)
	"Hebrew": "he_IL",   	# Hebrew (Israel)
	"Spanish": "es_ES",  	# Spanish (Spain)
	"French": "fr_FR",   	# French (France)
	"German": "de_DE",   	# German (Germany)
	"Russian": "ru_RU",  	# Russian (Russia)
	"Arabic": "ar_SA",   	# Arabic (Saudi Arabia)
	"Chinese": "zh_CN",  	# Chinese (China)
	"Japanese": "ja_JP", 	# Japanese (Japan)
	"Korean": "ko_KR",   	# Korean (South Korea)
	"Italian": "it_IT",  	# Italian (Italy)
	"Portuguese": "pt_PT",  # Portuguese (Portugal)
	"Dutch": "nl_NL",    	# Dutch (Netherlands)
	"Turkish": "tr_TR",  	# Turkish (Turkey)
	"Hindi": "hi_IN",    	# Hindi (India)
	"Greek": "el_GR",    	# Greek (Greece)
	"Polish": "pl_PL",   	# Polish (Poland)
	"Finnish": "fi_FI",  	# Finnish (Finland)
	"Swedish": "sv_SE",  	# Swedish (Sweden)
	"Danish": "da_DK",   	# Danish (Denmark)
	"Norwegian": "no_NO",  	# Norwegian (Norway)
	"Hungarian": "hu_HU",  	# Hungarian (Hungary)
	"Czech": "cs_CZ",    	# Czech (Czech Republic)
	"Thai": "th_TH",     	# Thai (Thailand)
	"Vietnamese": "vi_VN",  # Vietnamese (Vietnam)
	"Ukrainian": "uk_UA"	# Ukranian (Ukraine)
}

mwt_languages = {"he", "en", "de"}

POS_color_map_qt = dict()
for color in POS_color_map:
	char_format = QTextCharFormat()
	char_format.setForeground(QColor(color))
	POS_color_map_qt[color] = char_format

POS_painting = {
	"CC": "#7f7f7f",
	"CD": "#d62738",
	"DT": "#9467bd",
	"EX": "#ff9896",
	"FW": "#555555",
	"IN": "#17becf",
	"JJ": "#ff7f0e",
	"JJR": "#ffbb78",
	"JJS": "#d62728",
	"LS": "#17becf",
	"MD": "#1f77b4",
	"NN": "#1f77b4",
	"NNS": "#aec7e8",
	"NNP": "#2ca02c",
	"NNPS": "#98df8a",
	"PDT": "#c5b0d5",
	"POS": "#e7ba52",
	"PRP": "#e377c2",
	"PRP$": "#f7b6d2",
	"RB": "#ffbb78",
	"RBR": "#ffcc00",
	"RBS": "#ffeb3b",
	"RP": "#8c564b",
	"SYM": "#000000",
	"TO": "#bcbd22",
	"UH": "#c49c94",
	"VB": "#2ca02c",
	"VBD": "#98df8a",
	"VBG": "#d62728",
	"VBN": "#ff9896",
	"VBP": "#9467bd",
	"VBZ": "#c5b0d5",
	"WDT": "#8c564b",
	"WP": "#8c564b",
	"WP$": "#c49c94",
	"WRB": "#8c564b",
	"PNC": "black"
}
