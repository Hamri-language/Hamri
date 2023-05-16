from LexicalParser import LexicalParser
from StatementParser import StatementParser
from Logger import Logs,LogKeys
path_ = '/home/bytefrost/Documents/Hamri/Projects/test.ham'


if __name__ == '__main__':
    lexicalParser = LexicalParser(path_).parse()
    lexicalParser.print_tokens()
    statementParser = StatementParser(lexicalParser.token_list).parse()
    statementParser.print_statements()
    statementParser.execute()
    
    # For execution log:
    
    #  -Logs() - to print all logs
    
    #  -Logs(key) - to print {key} filtered logs
    
    #  -LogKeys() - for a list of log keys
    
    
    

