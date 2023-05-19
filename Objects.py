from SymbolTable import symbolTable  # Importing the symbolTable module
from Errors import Error  # Importing the Error module

# The Object class represents a generic object.
class Object:
    def __init__(self, value):
        self.token = value  # Initialize the token attribute with the provided value
        
    def return_type(self):
        pass
        
        
    def cast(self):
        casted_val = self.token  # Start with the original token value
        data_types = {
            'string': Str,  # Mapping the string data type to the Str class
            'integer': Int,  # Mapping the integer data type to the Int class
            'boolean': Bool,  # Mapping the boolean data type to the Bool class
            'variable': Var  # Mapping the variable data type to the Var class
        }
        if self.token.token_type in data_types.keys():
            # If the token's type is in the data_types dictionary, create an instance of the corresponding class
            casted_val = data_types[self.token.token_type](self.token.value)

        return casted_val  # Return the casted value


# The Var class represents a variable object.
class Var(Object):
    def __init__(self, value):
        self.mode = 1 if type(value).__name__ == 'tuple' else 2  # Determine the mode based on the type of the value

        if self.mode == 1:
            # If mode is 1, it means the value is a tuple containing name, value, and scope
            self.name, self.value, self.scope = value
        else:
            self.name = value  # If mode is 2, it means the value is only the variable name
            
    def return_type(self):
        return '<\'Anwani\'>'

    def evaluate(self):
        result = False  # Initialize the result variable as False

        if self.mode == 1:
            # If mode is 1, it means the variable is being assigned a value
            symbolTable.table['variables'][self.scope][self.name] = self.value  # Assign the value to the variable
            result = True  # Set the result as True, indicating successful assignment
        else:
            result = symbolTable.fetch_variable(self.name)  # Fetch the value of the variable from the symbol table
            if result:
                result = symbolTable.fetch_variable(self.name).evaluate()
                # If the variable is found, evaluate its value recursively
            else:
                Error.throwException('anwani', self.name)
                # If the variable is not found, throw an exception and set the result as False

        return result  # Return the result


# The Int class represents an integer object.
class Int(Object):
    def evaluate(self):
        return int(self.token)  # Return the integer value of the token


# The Str class represents a string object.
class Str(Object):
    def evaluate(self):
        return '{}'.format(self.token)  # Return the string value of the token


# The Bool class represents a boolean object.
class Bool(Object):
    def evaluate(self):
        return bool(self.token.capitalize())  # Return the boolean value of the token


# The code above defines several classes for different types of objects, such as variables, integers, strings, and booleans.
# These classes inherit from the Object class and provide the evaluate method, which returns the evaluated value of the object.
# The Var class handles variable assignments and retrieval, the Int class converts the token to an integer, the Str class converts the token to a string,
# and the Bool class converts the token to a boolean value.
# The Object class also provides the cast method, which allows for type casting of objects.

