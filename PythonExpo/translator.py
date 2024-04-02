def translate(phrase):
    translation = ""
    for letter in phrase:
        if letter.lower() in "aeiou":
            if letter.isupper():                         # check upper case letters
                translation = translation + "A"
            else:
                translation = translation + "a"
        else:
            translation = translation + letter 
    return translation

print(translate(input("Enter a phrase: ")))