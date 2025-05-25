import re

def decomplex_numbers(text):
	pattern = r"(\d+) +(\d+)"

	previous_text = None
	current_text = text

	while current_text != previous_text:
		previous_text = current_text
		current_text = re.sub(pattern, r"\1\2", previous_text)

	return current_text