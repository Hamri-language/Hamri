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
            # A 4th tuple element ('qualify') is optional - True means
            # this is an ordinary user-level local variable (from a plain
            # '=' assignment, or a huku/jaza-created variable) that should
            # be isolated to whichever function/method call is currently
            # executing (see SymbolTable.write_local). Callers that
            # already pass a fully call-qualified name themselves
            # (function parameter binding, 'nafsi' binding, parameter
            # placeholder creation) omit it / leave it False, since
            # qualifying an already-qualified key again would double it up.
            if len(value) == 4:
                self.name,self.value,self.scope,self.qualify = value
            else:
                self.name,self.value,self.scope = value
                self.qualify = False

        else:
            self.name = value



    def evaluate(self):

        result = False

        if self.mode == 1:
            # Evaluate the right-hand side NOW and store the plain result
            # (wrapped in Literal), not the unevaluated expression object.
            # Storing the raw expression broke self-referential assignment
            # (e.g. "i = i + 1"): the stored expression for 'i' would
            # itself contain a reference to 'i', so reading it back later
            # tried to evaluate 'i' in terms of itself forever - fine for
            # one-shot code, but fatal for any loop counter.
            # Not every caller passes an expression Object here - function
            # parameter placeholders assign a plain '' string directly -
            # so only call .evaluate() when there's actually one to call.
            evaluated = self.value.evaluate() if hasattr(self.value,'evaluate') else self.value
            if self.qualify and self.scope == 'local':
                symbolTable.write_local(self.name,Literal(evaluated))
            else:
                symbolTable.table['variables'][self.scope][self.name] = Literal(evaluated)
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
        # bool(str) in Python is True for ANY non-empty string - including
        # "false" itself - so this used to make every boolean true.
        return str(self.token).strip().lower() == 'true'

class Literal(Object):
    # Wraps an already-evaluated plain Python value (bool/int/float/str)
    # so it can be stored in a variable and re-read later through the
    # same .evaluate() interface as every other Object, without needing
    # to re-parse or re-cast it from text.
    def evaluate(self):
        return self.token
    
    


