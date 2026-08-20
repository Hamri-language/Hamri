import sys

from LexicalParser import LexicalParser
from StatementParser import StatementParser
from Logger import Logs,LogKeys
path_ = 'path_to_hamri_file'

##Note: hamri script files end in the extension ' .ham '

##Here is a sample Hamri script - showing off some of the language's
##newer features (loops, lists, classes) alongside the original demo

code = '''

darasa Mtu

    eleza jenga(jina)

        nafsi.jina = jina

    kwisha

    eleza salamu()

        rudisha "Hello world. I am " + nafsi.jina

    kwisha

kwisha

eleza sayHi(name)

    chapa "Hello world. " + "I am " + name

kwisha

kwanza

    hamri_v = "Hamri v1.0.3"

    sayHi(hamri_v)

    chapa 10 / 2

    aina hamri_v

    mtu1 = Mtu(hamri_v)

    chapa mtu1.salamu()

    orodha = [1, 2, 3]

    huku item kwenye orodha

        chapa item

    kwisha

kwisha



'''


if __name__ == '__main__':
    # Console mode: `python3 main.py` runs the built-in sample script
    # above; `python3 main.py path/to/script.ham` runs that file instead.
    #
    # LexicalParser's second argument, from_text, controls how the first
    # argument is read: from_text=True treats it as literal Hamri source
    # text (as used for `code` above); leaving it out (the default,
    # from_text=False) treats the first argument as a path to a script
    # file on disk instead - which is exactly what we want for the
    # command-line-argument case below.
    if len(sys.argv) > 1:
        lexicalParser = LexicalParser(sys.argv[1]).parse()
    else:
        lexicalParser = LexicalParser(code, from_text=True).parse()
    #print to console all the tokens found in script
    #lexicalParser.print_tokens()
    statementParser = StatementParser(lexicalParser.token_list).parse()
    #print to console all the statements parsed from the tokens found
    #statementParser.print_statements()
    statementParser.execute()
    
    # For execution log:
    
    #  -Logs() - to print all logs
    
    #  -Logs(key) - to print {key} filtered logs
    
    #  -LogKeys() - for a list of log keys
    
    
    

