from SymbolTable import symbolTable

from Errors import Error

class Object:
    def __init__(self,value):
        self.token = value
        
    def cast(self):
        casted_val = self.token
        data_types = {
        
        'string':Str,
        'integer':Int,
        'boolean':Bool,
        'variable':Var
        
        }
        if self.token.token_type in data_types.keys():
            casted_val = data_types[self.token.token_type](self.token.value)
            
        return casted_val
            
        
        
        

class Var(Object):
    def __init__(self,value):
        
        self.mode = 1 if type(value).__name__ == 'tuple' else 2
        
        
        if self.mode == 1:
            self.name,self.value,self.scope = value
            
        else:
            self.name = value
            
        
        
    def evaluate(self):
        
        result = False
        
        if self.mode == 1:
            symbolTable.table['variables'][self.scope][self.name] = self.value
            result = True
        else:
            
            result = symbolTable.fetch_variable(self.name)
            if result:
                result = symbolTable.fetch_variable(self.name).evaluate()
            else:
                Error.throwException('anwani',self.name)            
                result = False
        
        return result

class Int(Object):
    def evaluate(self):
        
        return int(self.token)

class Str(Object):
    def evaluate(self):
        return '{}'.format(self.token)

class Bool(Object):
    def evaluate(self):
        return bool(self.token.capitalize())
    
    


