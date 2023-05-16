from SymbolTable import symbolTable

class Errors:
    def __init__(self):
        
        self.exceptions = {
        
        'anwani': VariableReferenceException
        
        }
        
    def throwException(self,arg,args=''):
        
        self.exceptions[arg](args).execute()
        
class VariableReferenceException:
    
    def __init__(self,arg):
        self.name = arg
        
    def execute(self):
        print('Kosa La Anwani: Jina hili {' +self.name +'} halijulikani')
        symbolTable.exit(1)           


Error = Errors()