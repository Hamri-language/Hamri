import sys

from ExpressionParser import ExpressionParser

from Objects import * 

from SymbolTable import symbolTable

from Logger import Log

from LexicalParser import TokenObj

import tkinter as tk

from Console import console

from pprint import pprint as print_


global variables

variables= {"variables" :{
"global":{},
"local":{}
},
"functions":{
    "kwanza":[]
},
"classes":{
    "kwanza":[]
}
}


context = {"var-scope": "global","function-scope":"kwanza","class-scope":"kwanza"}
definition_flag = False
call_flag = False

            
class StatementParser:
    # Initialize the compound statement dictionary with empty lists for 'kwanza' and 'functions'
    compound_statement = {"kwanza": [], "functions": {}}
    
    # Set the context to the 'kwanza' list in the compound_statement
    context = compound_statement['kwanza']
    
    # Set the prev_context to the 'kwanza' list in the compound_statement
    prev_context = compound_statement['kwanza']
    
    # Declare the global variables call_flag and definition_flag
    global call_flag
    global definition_flag

    # Set the function_flag to 'kwanza'
    function_flag = 'kwanza'
    
    def __init__(self, tokens):
        # Initialize the StatementParser instance with the given tokens
        self.tokens = tokens
        
        # Set the token_position to 0 (start position)
        self.token_position = 0

        

        

    def parseStatement(self, parse_token):
        global call_flag
        
        # Get the next and previous tokens for context analysis
        next_ = self.next_token() if self.token_position < len(self.tokens) - 1 else None
        prev_ = self.prev_token() if self.token_position > 0 else None
        Log(parse_token.value, "parsing token")
        
        statement = None #value to be returned. Initiated to None
        
        # Check for the "chapa" keyword indicating a print statement
        if parse_token.value == 'chapa' and next_ is not None:
            Log('case for print')
            # Parse the expression inside the parentheses and create a PrintStatement object
            statement = PrintStatement(ExpressionParser(self.fetch_express()).parse())
        
        # Check for the "=" symbol indicating an assignment statement
        elif parse_token.value == '=' and next_ is not None and prev_ is not None:
            Log('case for assignment')
            # Create a Var object with the variable name, the evaluated expression, and the variable scope,
            # then create an AssignmentStatement object with the Var object
            obj = Var((prev_.value, ExpressionParser(self.fetch_express()).parse(), symbolTable.get_scope('var-scope')))
            statement = AssignmentStatement(obj)
        
        # Check for the "kwisha" keyword indicating the end of a block
        elif parse_token.value == 'kwisha':
            Log('case for end block')
            # Reset the definition flag and create an EndBlockStatement object with the current context
            symbolTable.reset_flags()
            statement = EndBlockStatement(symbolTable.context)
        
        # Check for the "jaza" keyword indicating an input statement
        elif parse_token.value == 'jaza':
            Log('case for user input')
            self.token_position = self.token_position + 1
            # Create an InputStatement object with the input prompt and the variable to store the input value
            statement = InputStatement(self.fetch_express())
            
        #check for the 'aina' keyword indicating return of object type
        elif parse_token.value == 'aina':
            Log('case for return object type')
            self.token_position = self.token_position + 1
            # Create an InputStatement object with the input prompt and the variable to store the input value
            statement = ReturnObjectTypeStatement(ExpressionParser(self.fetch_express()).parse())        
        
        # Check for a function call by identifying a variable followed by '('
        elif parse_token.token_type == 'function':
            
            if prev_.value == 'eleza':
                
                Log('case for function definition')
                # Set the function definition flag and extract the function name and parameters
                symbolTable.def_flag = True
                function_name = parse_token.value        
                # Create a FunctionDefinitionStatement object with the function name and parameters
                expression = self.fetch_express()
                statement = FunctionDefinitionStatement((function_name, expression))
                
            else:
                Log('case for function call')
                # Set the call flag and extract the function name
                call_flag = True
                function_name = parse_token.value
                
                # Create a FunctionCallStatement object with the function name and the parsed expressions as parameters
                
                statement = FunctionCallStatement((function_name, self.fetch_express()))
                
        elif parse_token.value == 'rudisha':
            Log('case for function return statement')
            statement = FunctionReturnStatement(ExpressionParser(self.fetch_express()).parse())
            
        
        else:
            Log('default case')
        
        return statement


    
        
    def fetch_express(self):
        next_ = self.next_token()  # Get the next token
        
        Log('Fetching expression ')
        
        
        if next_.token_type == 'divider':
            return_val = []  # If the next token is a divider, return an empty list to represent an empty expression i.e func()
            
        else:
            # Evaluate the first token and add it to the return value list
            return_val = [Object(self.next_token()).cast()]
            Log(return_val[0], 'First Token')
            
            self.token_position = self.token_position + 1  # Advance the execution loop
            
            # Process additional tokens if they are operators followed by terms
            while self.next_token().token_type == 'operator':
                return_val.append(Object(self.next_token()).cast()) if self.next_token().value != ',' else None  # Add the operator to the return value
                
                self.token_position = self.token_position + 1  # Advance the execution loop
                
                return_val.append(Object(self.next_token()).cast())  # Add the term to the return value
                
                self.token_position = self.token_position + 1
        
        Log(return_val, 'Evaluated expression')
        
        return return_val

        
    
    def print_statements(self):
        #print the symbol table
        print_(symbolTable.table)
            
    def next_token(self):
        #fetch the next token in our loop
        
        return self.tokens[self.token_position + 1]
    
    def prev_token(self):
        #fetch the previous token in our loop
        
        return self.tokens[self.token_position - 1]    

    def parse(self):
    
        Log('=======================')
        Log('Statement Parsing')
        Log('=======================')
    
        # Iterate through the tokens
        while self.token_position < len(self.tokens):
            # Parse the current token and get the corresponding statement
            statement = self.parseStatement(self.tokens[self.token_position])
    
            # Log the evaluated statement and current context
            Log(statement, 'Evaluated statement')
            Log(symbolTable.get_scope('function-scope'), 'Current context')
    
            # Append the statement to the current function scope
            symbolTable.table['functions'][symbolTable.get_scope('function-scope')].append(statement) if statement else None
    
            # Log the current symbol table state
            Log(symbolTable.table, 'Current symbol table state')
    
            # Handle function definitions
            if type(statement).__name__ == 'FunctionDefinitionStatement':
                # Change to function scope
                symbolTable.set_scope(('var-scope', 'local'))
                symbolTable.set_scope(('function-scope', statement.name))
    
            self.token_position = self.token_position + 1  # Move to the next token
    
        return self

        

    def execute(self):
        #clear our console first with some beginning text
            
        
        Log('=======================')
        Log('Statement Execution')
        Log('=======================')
        
        
        #start our console
        console.start_console()
        
        
        
        #Hamri's main execution loop is this right here
        
        for i in symbolTable.table['functions'][symbolTable.get_scope('function-scope')]:
            
            #check if the exit code in the symbol table is set to 0 
             
            if symbolTable.exit() == 0:
                Log(symbolTable.get_scope('function-scope'),'Executing from scope')
                Log(i,'Executing statement')
                
                #execute the statement if the exit is 0
                i.execute()
                
            else:
                #break the execution loop
                break
            
        #print out execution code statement at the end of the execution loop
        
        Log('=======================')
        Log('Statement Execution Completed')
        Log('=======================')
        
        #stop our console and clear the symbolTable
        console.close_console()
        symbolTable.reset_table()
        




# Class to represent a statement in the Hamri programming language
class Statement:
    def __init__(self):
        None

    def execute(self):
        None

# Class to represent a function call statement
class FunctionCallStatement(Statement):
    def __init__(self, arg):
        # Name of the function being called
        self.name = arg[0]
        # Parameters passed to the function
        self.params = arg[1]

    def execute(self):
        # Assign parameter values to function arguments
        #set the scope to the executing function's name
        symbolTable.set_scope(('function-scope',self.name))
        
        Log(symbolTable.get_function_arguments(self.params), 'Function Parameters')
        
        assignments = list(zip(symbolTable.get_function_arguments(self.name), self.params))
        
        Log(list(assignments), 'Function Arguments')

        # Evaluate and assign parameter values to local variables
        for i in assignments:
            #set new local variable with the intended value
            Var((i[0], i[1], 'local')).evaluate()

        # Set the function call flag in the symbol table
        symbolTable.en_flag('call', self.name)

        # Execute statements inside the function
        for i in symbolTable.table["functions"][self.name]:
            Log(self.name, 'Executing from function scope')
            Log(i, 'Executing statement')
            i.execute()

        # Reset flags after executing the function
        symbolTable.reset_flags()

# Class to represent a function definition statement
class FunctionDefinitionStatement(Statement):
    def __init__(self, arg):
        # Name of the function being defined
        self.name = arg[0]
        # Parameters of the function
        self.params = arg[1]
        # Set the current function scope in the symbol table
        symbolTable.set_function(self.name)
        Log('created new function {} with params: '.format(self.name), 'Function Definition')

    def execute(self):
        # Create local variables for function arguments
        Log('creating new arguments: {}'.format(self.params))
        for i in self.params:
            Log('setting function parameter {}'.format(i.name))
            Var(('function-{}-{}'.format(self.name, i.name), '', 'local')).evaluate()
            
        Log('{}'.format(symbolTable.table))
            
            
class FunctionReturnStatement(Statement):
    
    def __init__(self,arg):
        self.return_value = arg
        
        
    def execute(self):
        #get current context (function name) and set the return value
        symbolTable.set_return_value(symbolTable.get_scope("function-scope"),self.return_value)
        
        #self.return_value = self.return_value.evaluate()
        
        Log('{}'.format(self.return_value),'Evaluated return statement')
        
        Log('setting return value for function: {} to {}'.format(symbolTable.get_scope("function-scope"),self.return_value))
        
        #set our return value in the symbolTable (function_name,value)
        symbolTable.set_return_value(symbolTable.get_scope("function-scope"),self.return_value)
        p

# Class to represent an input statement
class InputStatement(Statement):
    def __init__(self, arg):
        # Prompt message for input
        self.value = arg[0].evaluate()
        # Variable name to store the input value
        self.storage = arg[1].name

    def execute(self):
        # Get input from the user
        var = Object(TokenObj('string', input(str(self.value)), 0, 0, 0)).cast()
        # Assign the input value to the specified variable
        Var((self.storage, var, symbolTable.get_scope('var-scope'))).evaluate()

# Class to represent an end block statement
class EndBlockStatement(Statement):
    def __init__(self, value):
        # Value indicating the end of a block
        self.value = value
        # Reset the scope to the global variable scope and the function scope to the starting function
        symbolTable.set_scope(('var-scope', 'global'))
        symbolTable.set_scope(('function-scope', 'kwanza'))

# Class to represent a print statement
class PrintStatement(Statement):
    def __init__(self, value):
        # Value to be printed
        self.value = value

    def execute(self):
        # Print the value to console
        if self.value.evaluate():
            console.print_to_console('{}\n'.format(self.value.evaluate()))
            Log("{}".format(self.value.evaluate()), "Print Statement")
            
        

# Class to represent an assignment statement
class AssignmentStatement(Statement):
    def __init__(self, value):
        # Assigned value
        self.value = value

    def execute(self):
        # Evaluate and assign the value to the variable
        self.value.evaluate()

#class to represent a return-object-type statement        
class ReturnObjectTypeStatement(Statement):
    def __init__(self, value):
        # Assigned value
        self.value = value

    def execute(self):
        # Evaluate and assign the value to the variable
        #self.value.evaluate()
        print(self.value.return_type())

            
        
        
'''



   - The code defines a global dictionary variable named "variables" that stores information about variables, functions, and classes.
   - It initializes this dictionary with empty "global" and "local" variables, an empty list of functions, and an empty list of classes.


   - The code defines a global variable named "console" and initializes it as None.

Context and Flags:
   - The code defines a global dictionary variable named "context" that stores the current context of the program, such as variable and function scopes.
   - It also defines two global flags: "definition_flag" and "call_flag" to track function and variable definitions and function calls, respectively.

StatementParser Class:
   - The code defines a class named "StatementParser" that handles the parsing and execution of Hamri statements.
   - It initializes the class with a list of tokens representing the Hamri script.
   - The class provides methods for parsing different types of statements and executing them.
   - The "parseStatement" method takes a token as input, determines the type of statement, and parses it accordingly.
   - The "fetch_express" method is used to fetch expressions from the tokens.
   - The "next_token" and "prev_token" methods return the next and previous tokens, respectively.
   - The "parse" method parses all the statements in the script.
   - The "execute" method executes the parsed statements.

Statement Class:
   - The code defines a base class named "Statement" that serves as the parent class for different types of statements in Hamri.

FunctionCallStatement Class:
   - The code defines a class named "FunctionCallStatement" that represents a function call statement in Hamri.
   - It takes the function name and its parameters as input.
   - The "execute" method assigns parameter values to function arguments and executes the function's statements.

FunctionDefinitionStatement Class:
   - The code defines a class named "FunctionDefinitionStatement" that represents a function definition statement in Hamri.
   - It takes the function name and its parameters as input.
   - The "execute" method creates new argument variables for the function.

InputStatement Class:
    - The code defines a class named "InputStatement" that represents an input statement in Hamri.
    - It takes the input message and the variable to store the input value as input.
    - The "execute" method prompts the user for input and assigns the entered value to the specified variable.

EndBlockStatement Class:
    - The code defines a class named "EndBlockStatement" that represents the end of a block (function or script) in Hamri.
    - It takes the current context as input and resets the variable and function scopes.

PrintStatement Class:
    - The code defines a class named "PrintStatement" that represents a print statement in Hamri.
    - It takes the value to be printed as input.
    - The "execute" method evaluates the value and prints it.

13. AssignmentStatement Class:
    - The code defines a class named "AssignmentStatement" that represents an assignment statement in Hamri.
    - It takes the variable name and its assigned value as input.
    - The "execute" method evaluates the assigned value and assigns it to the variable.

Explanation:
    - The code includes comments throughout the script explaining various parts and functionalities.

Execution:
    - The code checks if there is a console (text widget) provided and inserts execution logs and output into it.
    - The "parse" method is called to parse all the statements in the script.
    - The "execute" method is called to execute the parsed statements.
    - After execution, an exit code is logged and displayed in the console (if provided).
    
    
'''
