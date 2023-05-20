import re
import enum
import sys
from os.path import exists

# Set holding our lexeme units. We use a set of regular expressions to match for lexemes for parsing later.
class Tokens(enum.Enum):
    keyword = r'(chapa|kama|jaza|kwisha|kwanza|eleza|aina)'  # Regular expression for keywords
    divider = r'(\\[|\\]|\(|\))'  # Regular expression for dividers
    boolean = r'true|false'  # Regular expression for booleans
    integer = r'\.\b[0-9]+|[0-9]+'  # Regular expression for integers
    string = r'"(.*?)"|\'(.*?)\'|\b[0-9]+'  # Regular expression for strings
    variable = r'((\'[^\']*\'|([A-Za-z_]\w*(?:\.[a-z_]\w*)*))(?!\"\')|("[^"]*"|([a-z_]\w*(?:\.[a-z_]\w*)*))(?!\"\'))'  # Regular expression for variables
    operator = r'[\*\/\+\-\=\,]'  # Regular expression for operators

class LexicalParser:
    def __init__(self, script,flag=None):
        # Class constructor with script (Hamri script) and an empty token_list array
        self.script = self.read_source(script) if flag== 'f' else script.split('\n')
        self.token_list = []

    def read_source(self, arg):
        # Function to read in our Hamri script from source
        script = None
        
        # function to return the file extension

        if exists(arg):
            import pathlib
            
            if pathlib.Path(arg).suffix == '.ham':
                content = open(arg, "r")
                script = content.readlines()
                content.close()
                
            else:
                print('The file you provided is not a hamri script file')
                
                sys.exit(1)
        else:
            print('The file path you provided does not exist')
            sys.exit(1)
            
        return script

    def parse(self):
        index = 0
        all_tokens = []

        for i, v in enumerate(self.script):
            # Iterate over each line in the script

            # Find all matches for the regular expressions defined in Tokens enum
            tokens = [
                (x.group(), x.span()[0], i) for x in re.compile(r'{}'.format('|'.join(
                    [t.value for t in Tokens]
                    )
                                                                             )
                                                                ).finditer(v)
            ]

            # Append the found tokens to the all_tokens list
            for n in tokens:
                all_tokens.append(n)

        id_ = 0
        # Assign a unique identifier to each token and store them in the token_list
        for t_ in all_tokens:
            for t in Tokens:
                if self.find_token_match(t_[0], t.value):
                    self.token_list.append(
                        TokenObj(t.name,
                                 t_[0].replace('"', '').replace('\'', '') if t.name == 'string' else t_[0],
                                 t_[1], t_[2], id_
                                 )
                    )
                    break
            id_ = id_ + 1

        return self

    def print_tokens(self, type_='all'):
        # Print the tokens stored in the token_list
        for i in self.token_list:
            if type_ == 'all':
                print('-----------\nType: {}\nValue: {}\nLine: {}\nPosition: ({},{})\nOffset: {}\n-----------'.format(
                    i.token_type,
                    i.value,
                    i.line,
                    i.span()[0],
                    i.span()[0] + i.size(),
                    i.position()
                ))
            else:
                if type_ == i.token_type:
                    print('-----------\nType: {}\nValue: {}\n-----------'.format(
                        i.token_type,
                        i.value, i.start,
                        i.start + i.len_
                    ))

    def count_tokens(self):
        # Count the number of tokens in the token_list and print the count
        count = len(self.token_list)
        print('-----------\nTokens: {}\n-----------'.format(count))
        return count

    def find_token_match(self, search_str, pat_):
        # Check if the search string matches the given pattern
        pattern = re.compile(pat_)
        return_match = True if len(pattern.findall(search_str)) > 0 else False

        # Strict check to make sure integers in strings are avoided
        if pat_ == Tokens.integer.value:
            if len(re.compile(r'[\"\']').findall(search_str)) > 0:
                return_match = False

        return return_match


class TokenObj:
    def __init__(self, token_type, value, start, line, offset):
        # Initialize a token object with its properties
        self.token_type = token_type
        self.value = value
        self.line = line
        self.start = start
        self.offset = offset
        self.len_ = len(self.value)

    def value(self):
        #the value of the actual token
        return self.value

    def position(self):
        #the offset of the token in the script
        return self.offset

    def type(self):
        #the type of the token as matched by the various regex expressions
        return self.token_type

    def size(self):
        #the size (count) of the token type
        return self.len_

    def span(self):
        #a tuple representing the start and end positions of the token
        return (self.start, self.start + self.len_)

    def evaluate(self):
        return self



##- This code defines a lexical parser for the Hamri programming language. 
##- It uses regular expressions defined in the 'Tokens' enum to match and extract different lexemes from the Hamri script. 
##- The 'LexicalParser' class reads the source script, parses it line by line, and identifies the tokens based on the regular expressions. 
##- The tokens are stored in the 'token_list' as 'TokenObj' instances. 
##- The code also provides methods to print the tokens, count the tokens, and find token matches. 
##- The 'TokenObj' class represents a token object with various properties to store information about the token.

