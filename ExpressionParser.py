from Objects import *
from Logger import Log
        
class ExpressionParser:
    def __init__(self,args):
        self.tokens = args

        self.operators = {

        '+': AdditionExpression,
        '-': SubtractionExpression,
        '*': MultiplicationExpression,
        '/': DivisionExpression,
        '==': EqualsExpression,
        '!=': NotEqualsExpression,
        '<': LessThanExpression,
        '>': GreaterThanExpression,
        '<=': LessEqualExpression,
        '>=': GreaterEqualExpression,
        'kabisa': StrictEqualsExpression,
        'hakika': StrictEqualsExpression

        }


    def parse(self):
        
        #print("tokens before parsing: ",self.tokens)
        
        return_val = self.tokens[0]
        
        #for the first value in expression
        
        for count,i in enumerate(self.tokens[1:]):
            if type(i).__name__ == 'TokenObj':
                if i.value in self.operators.keys():
                    #print('found operator ',i.value,' in pass ',count)
                    #print('operands: left ',return_val," right ",self.tokens[count + 2])
                    return_val = self.operators[i.value]((return_val,self.tokens[count + 2]))
                    #print('result object: ',return_val)

        
        #print("tokens results after parsing: ",self.tokens)
        #print('results after parsing: ',return_val)
        return return_val
                
        
class AdditionExpression:
    
    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]
        
        
    def evaluate(self):

        Log(self.left,'Addition operation')
        Log(self.right,'Addition operation')

        left = self.left.evaluate()
        right = self.right.evaluate()

        # Auto-stringify when mixing text with a number (e.g. "x is: " + x)
        # instead of letting Python's str+int TypeError leak through -
        # numeric + numeric still adds normally.
        if isinstance(left,str) or isinstance(right,str):
            return '{}{}'.format(left,right)
        return left + right


class MultiplicationExpression:

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() * self.right.evaluate()


class DivisionExpression:

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        # True division (e.g. 7/2 -> 3.5) since there's no separate Float
        # type in this language yet - a whole-number result like 10/2
        # still comes back as a plain 5 thanks to the int() cast below.
        result = self.left.evaluate() / self.right.evaluate()
        return int(result) if result == int(result) else result


class SubtractionExpression:

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        Log(self.left,'Subtraction operation')
        Log(self.right,'Subtraction operation')

        return self.left.evaluate() - self.right.evaluate()


class EqualsExpression:

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() == self.right.evaluate()


class NotEqualsExpression:

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() != self.right.evaluate()


class LessThanExpression:

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() < self.right.evaluate()


class GreaterThanExpression:

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() > self.right.evaluate()


class LessEqualExpression:

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() <= self.right.evaluate()


class GreaterEqualExpression:

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() >= self.right.evaluate()


class StrictEqualsExpression:
    # 'kabisa' ("completely/exactly") - strict equality: true only if both
    # value AND type match. Plain '==' relies on Python's own equality,
    # where e.g. `true == 1` is True (bool is a subclass of int) - kabisa
    # is for when that distinction matters.

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        left = self.left.evaluate()
        right = self.right.evaluate()
        return type(left) == type(right) and left == right


class ArgumentConstructorExpression:

    def __init__(self,values):
        pass
