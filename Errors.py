from SymbolTable import symbolTable

class Errors:
    def __init__(self):
        self.exceptions = {
            'anwani': VariableReferenceException  # Define an exception with key 'anwani' and value as VariableReferenceException class
        }
        
    def throwException(self, arg, args=''):
        self.exceptions[arg](args).execute()  # Instantiate the exception class based on the provided argument and execute it
        
class VariableReferenceException:
    def __init__(self, arg):
        self.name = arg
        
    def execute(self):
        print('Kosa La Anwani: Jina hili {' + self.name + '} halijulikani')  # Print an error message indicating unknown variable name
        symbolTable.exit(1)  # Set the exit flag of the symbolTable instance to 1
        
class Exception:
    def __init__(self, arg):
        self.name = arg
        
    def execute(self):
        pass  # Placeholder method for generic exception execution

Error = Errors()  # Create an instance of the Errors class

# Explanation:
# - The Errors class handles exceptions and provides a mechanism to throw exceptions.
# - It defines a dictionary, 'exceptions', which maps exception keys to exception classes.
# - The 'throwException' method takes an argument to specify the type of exception and an optional argument.
# - Based on the exception argument, the corresponding exception class is instantiated and executed.
# - The 'VariableReferenceException' class handles variable reference exceptions.
# - It prints an error message indicating an unknown variable name and sets the exit flag in the symbolTable instance.
# - The 'Exception' class is a generic placeholder for other exceptions.
# - The 'Errors' class is instantiated as 'Error'.
