from googletrans import Translator
translator = Translator()
print(translator.translate("hello", dest="ta").text)
