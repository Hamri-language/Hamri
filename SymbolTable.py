from Logger import Log

class SymbolTable:
    def __init__(self):
        # Initialize the symbol table with empty dictionaries for variables, functions, and classes
        self.table = {
            "variables" :{
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
        
        # Initialize the context with default values for variable scope, function scope, and class scope
        self.context =  {"var-scope": "global", "function-scope": "kwanza", "class-scope": "kwanza"}
        
        # Initialize flags for function definition, function call, and program exit
        self.def_flag = False
        self.call_flag = False
        self.exit_flag = 0
        
    def reset_flags(self):
        # Reset the function definition and function call flags
        self.def_flag = False
        self.call_flag = False
        
    def en_flag(self, arg, value=True):
        # Enable a specific flag (function call or function definition) with the given value
        if arg == 'call':
            #if it is a function being called, set the call flag
            self.call_flag = value
        else:
            #a function is being defined so set the definition flag
            self.def_flag = value
        
    def fetch_variable(self, key):
        # Retrieve the value of a variable with the given key
        
        Log('fetching.......: ' + key)
        
        return_val = None
        
        #check first if its a function being called, in this case, the variable is a parameter of the function
        
        if self.call_flag and 'function-{}-{}'.format(self.call_flag, key) in self.table['variables']['local'].keys():
            # Variable found in function's local scope
            Log('found in function local scope')
            val = 'function-{}-{}'.format(self.call_flag, key)
            return_val = self.table['variables']['local'][val]
        elif key in self.table['variables']['local'].keys():
            # Variable found in local scope
            Log('found in local scope')
            return_val = self.table['variables']['local'][key]
        elif key in self.table['variables']['global'].keys():
            # Variable found in global scope
            Log('found in global scope')
            return_val = self.table['variables']['global'][key]
        else:
            # Variable not found
            return_val = False
        
        Log('result.......: {}'.format(return_val))    
        return return_val
    
    def exit(self, arg='get'):
        # Get or set the exit flag of the program
        
        result = False
        
        if arg == 'get':
            # Return the current exit flag value
            result = self.exit_flag
        else:
            # Set the exit flag to the given value
            self.exit_flag = arg
            result = True 
            
        return result
    
    def set_variable(self, obj):
        # Set a variable with the given name, value, and scope
        
        name, value, scope = obj
        
        self.table['variables'][scope][name] = value
        
    def set_function(self, arg):
        # Set a function with the given name in the symbol table
        
        self.table['functions'][arg] = []
        
    def get_function_arguments(self, arg):
        # Get the arguments of a function with the given name
        
        res = []
        
        ## Issue: Could combine all this into one long list comprehension. Current code is not efficient
        
        keys = [k for k in self.table['variables']['local'].keys()]
        
        for k in keys:
            if k.startswith('function-{}-'.format(arg)):
                # Found an argument of the function
                res.append(k)
        #only return if more than one argument
        return res if len(res) > 0 else []
    
    def set_scope(self, arg):
        # Set the value of a specific scope (variable scope, function scope, or class scope)
        
        name, value = arg
        
        self.context[name] = value
        
    def get_scope(self, arg):
        # Get the value of a specific scope (variable scope, function scope, or class scope)
        
        return self.context[arg]
        
        
symbolTable = SymbolTable()


# The provided code implements a Symbol Table, which is a data structure used by compilers and interpreters
# to store and manage information about variables, functions, and classes in a programming language.


# Importing the Log class from the Logger module.

# The SymbolTable class is defined, which represents the symbol table.

# The __init__ method initializes the symbol table with empty dictionaries for variables, functions, and classes.

# The 'table' dictionary has the following structure:
# "variables": Contains dictionaries for global and local variables.
# "functions": Contains a dictionary of function names and their associated arguments.
# "classes": Contains a dictionary of class names.

# The 'context' dictionary is initialized with default values for variable scope, function scope, and class scope.
# It keeps track of the current scope in the symbol table.

# The 'def_flag', 'call_flag', and 'exit_flag' variables are initialized as flags for function definition,
# function call, and program exit, respectively.

# The 'reset_flags' method is used to reset the function definition and function call flags.

# The 'en_flag' method is used to enable a specific flag (function call or function definition) with the given value.

# The 'fetch_variable' method retrieves the value of a variable with the given key. It checks the current scope,
# starting from the local scope, then the global scope. If the variable is not found, it returns False.

# The 'exit' method is used to get or set the exit flag of the program. If called without an argument,
# it returns the current exit flag value. If called with an argument, it sets the exit flag to the given value.

# The 'set_variable' method is used to set a variable with the given name, value, and scope.
# It adds the variable to the appropriate scope in the symbol table.

# The 'set_function' method is used to set a function with the given name in the symbol table.
# It adds an empty list for the function in the "functions" dictionary.

# The 'get_function_arguments' method retrieves the arguments of a function with the given name.
# It searches for variables in the local scope that have names starting with "function-{function_name}-",
# indicating they are function arguments.

# The 'set_scope' method is used to set the value of a specific scope (variable scope, function scope, or class scope)
# in the 'context' dictionary.

# The 'get_scope' method is used to get the value of a specific scope from the 'context' dictionary.

# Finally, an instance of the 'SymbolTable' class is created and assigned to the 'symbolTable' variable.

# The Symbol Table is a fundamental component of language processing systems, as it allows for the storage and retrieval
# of information about variables, functions, and classes during the compilation or interpretation process.
# It enables proper scoping and lookup of symbols, ensuring correct handling of identifiers in a programming language.

