from enum import Enum, auto


class SpeechPart(Enum):
	NOUN = auto()
	VERB = auto()
	ARTICLE = auto()
	PRONOUN = auto()
	PREPOSITION = auto()
	CONJUNCTION = auto() 


if __name__ == '__main__':
	noun = SpeechPart.NOUN
	print('hello world')
	print(noun)