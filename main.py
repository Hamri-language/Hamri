from LexicalParser import LexicalParser
from StatementParser import StatementParser
from Logger import Logs,LogKeys
path_ = 'path_to_hamri_file'

##Note: hamri script files end in the extension ' .ham '

##Here is a sample Hamri script

code = '''

kwanza

    hamri_v = "Hamri v1.02"

    eleza sayHi(name)

        chapa "Hello world. " + "I am " + name

    kwisha


    sayHi(hamri_v)

    chapa 10 / 2

    aina(hamri_v)


kwisha



'''


if __name__ == '__main__':
    #lexicalParser = LexicalParser(path_,'f').parse() #add 'f' flag for file paths
    lexicalParser = LexicalParser(code).parse()
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
    
    
    

