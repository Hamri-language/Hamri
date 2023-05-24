class SymbolTable:
    def __init__(self):
        self.symbol_table = {}

    def add_symbol(self, name, value, scope):
        self.symbol_table[(name, scope)] = value

    def lookup_symbol(self, name, scope):
        if (name, scope) in self.symbol_table:
            return self.symbol_table[(name, scope)]
        else:
            return None

    def remove_symbol(self, name, scope):
        if (name, scope) in self.symbol_table:
            del self.symbol_table[(name, scope)]


class Scope:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.scope = None

    def set_scope(self, scope):
        self.scope = scope

    def add_symbol(self, name, value):
        if self.scope is not None:
            self.symbol_table.add_symbol(name, value, self.scope)

    def lookup_symbol(self, name):
        if self.scope is not None:
            return self.symbol_table.lookup_symbol(name, self.scope)
        else:
            return None

    def remove_symbol(self, name):
        if self.scope is not None:
            self.symbol_table.remove_symbol(name, self.scope)
            
    def return_scope(self):
        return self.scope



scope = Scope()
