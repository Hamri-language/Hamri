class SymbolTable:
    def __init__(self):
        self.symbol_table = {}

    def add_symbol(self, name, value):
        self.symbol_table[name] = value

    def lookup_symbol(self, name):
        if name in self.symbol_table:
            return self.symbol_table[name]
        else:
            return None

    def remove_symbol(self, name):
        if name in self.symbol_table:
            del self.symbol_table[name]
            
    def print_symbol_table(self):
        return self.symbol_table


class Scope:
    def __init__(self, parent=None):
        self.symbol_table = SymbolTable()
        self.parent = parent

    def add_symbol(self, name, value):
        self.symbol_table.add_symbol(name, value)

    def lookup_symbol(self, name):
        value = self.symbol_table.lookup_symbol(name)
        if value is None and self.parent is not None:
            return self.parent.lookup_symbol(name)
        else:
            return value

    def remove_symbol(self, name):
        self.symbol_table.remove_symbol(name)
        
    def print_scope_table(self):
        return self.symbol_table.print_symbol_table()



global_scope = Scope()

symboltable = SymbolTable()