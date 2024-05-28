from unidecode import unidecode

punctuation_characters = set([',', '.'])

separator_characters = set(['-'])

useless_words = set([
    "A",
    "CON",
    "DE",
    "DESDE",
    "EN",
    "ENTRE",
    "PARA",
    "POR",
    "SEGUN",
    "SOBRE",
    "DEL",
    "EL",
    "LA",
    "X",
    "G", "GR", "GRS", "LT", "LTS", "ML"
]
)

def get_keywords(string:str):

    #Unidecode + Uppercase
    key_words = unidecode(string.upper())

    #Remove Punctuation
    for char in punctuation_characters:
        key_words = key_words.replace(char, '')

    #Convert to List 
    key_words = key_words.split()

    #Treat separators, ex: "COCA-COLA" is converted into [COCA, COLA, COCACOLA, COCA-COLA]"
    for word in key_words:
        for char in word:
            if char in separator_characters:
                key_words += word.split(char)
                key_words.append(word.replace(char, ''))
                

    #Remove too short words
    key_words = [word for word in key_words if len(word) > 1]

    #convert to set and remove useless words
    key_words = set(key_words)
    key_words = key_words-useless_words
        
    #pluralize words
    plural = [s + 'S'  if s[-1] != 'S' else s for s in key_words]

    #Singularize words
    singular = [s[:-1] if s[-1] in ('s', 'S') else s for s in key_words]

    return list(set(plural + singular))

if __name__ == '__main__':
    print (get_keywords('martillo de pelotas Coca-cola.'))