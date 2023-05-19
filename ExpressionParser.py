from Objects import *
from Logger import Log

class ExpressionParser:
    def __init__(self, args):
        # Initialize the ExpressionParser with the given arguments (tokens)
        self.tokens = args
        
        # Define the operators and their corresponding Expression classes
        self.operators = {
            '+': AdditionExpression,
            '-': SubtractionExpression,
            '*': MultiplicationExpression,
            '/': DivisionExpression
        }
    
    def parse(self):
        # Set the return value to the value of the first token in the token list
        return_val = self.tokens[0]
        
        # Iterate through the tokens starting from the second token
        for count, i in enumerate(self.tokens[1:]):
            # Check if the next element in the list is a token
            if type(i).__name__ == 'TokenObj':
                # If the token is an operator, use its value to match the correct Expression class from self.operators
                if i.value in self.operators.keys():
                    return_val = self.operators[i.value]((return_val, self.tokens[count + 2]))
        
        return return_val


class Expression:
    def __init__(self, values):
        # Initialize an Expression with the given values (left and right operands)
        self.left = values[0]
        self.right = values[1]
        
    def evaluate(self):
        pass
        

class AdditionExpression(Expression):
    def evaluate(self):
        # Log the left and right operands for addition operation
        Log(self.left, "Addition operation")
        Log(self.right, "Addition operation")
        
        # Evaluate and return the addition of the left and right operands
        return self.left.evaluate() + self.right.evaluate()
    
class SubtractionExpression(Expression):
    def evaluate(self):
        # Log the left and right operands for subtraction operation
        Log(self.left, "Subtraction operation")
        Log(self.right, "Subtraction operation")
        
        # Evaluate and return the subtraction of the left and right operands
        return self.left.evaluate() - self.right.evaluate()
    
class MultiplicationExpression(Expression):
    def evaluate(self):
        # Log the left and right operands for multiplication operation
        Log(self.left, "Multiplication operation")
        Log(self.right, "Multiplication operation")
        
        # Evaluate and return the multiplication of the left and right operands
        return self.left.evaluate() * self.right.evaluate()
    
class DivisionExpression(Expression):
    def evaluate(self):
        # Log the left and right operands for division operation
        Log(self.left, "Division operation")
        Log(self.right, "Division operation")
        
        # Evaluate and return the division of the left and right operands
        return self.left.evaluate() / self.right.evaluate()


class ArgumentConstructorExpression:
    def __init__(self, values):
        pass

# The code defines an `ExpressionParser` class responsible for parsing expressions using the given tokens.
# The `parse` method of the `ExpressionParser` class iterates through the tokens, evaluates the expression, and returns the result.
# The `ExpressionParser` class also contains an `operators` dictionary that maps operators to their corresponding `Expression` classes (`AdditionExpression`, `SubtractionExpression`, etc.).
# The `Expression` class represents a generic expression with a left operand (`self.left`) and a right operand (`self.right`).
# Each specific expression class (e.g., `AdditionExpression`, `SubtractionExpression`, etc.) extends the `Expression` class and overrides the `evaluate` method to perform the corresponding operation.
# The overridden `evaluate` method logs the left and right operands for the specific operation and returns the evaluated result.
# The `ArgumentConstructorExpression` class is empty and does not contain any specific functionality.
