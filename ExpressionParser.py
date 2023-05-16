from Objects import *
from Logger import Log
        
class ExpressionParser:
    def __init__(self,args):
        self.tokens = args
        
        self.operators = {
        
        '+': AdditionExpression
        
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
        
        
        return self.left.evaluate() + self.right.evaluate()


class ArgumentConstructorExpression:
    
    def __init__(self,values):
        pass
        