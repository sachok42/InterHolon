import logging


logger = logging.getLogger(__name__)
logging.basicConfig(filename='chatting_log.log', encoding='utf-8', level=logging.DEBUG)

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

# Run validation on script load (optional)
validate_language_tree(LANGUAGE_TREE)
