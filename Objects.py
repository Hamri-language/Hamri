# Objects.py defines the small set of classes used to represent every
# individual value and variable reference that shows up inside a Hamri
# expression - a number, a string, a boolean, or a plain variable name.
# Every class here shares the same interface: it gets built once (when
# the source is parsed) with whatever raw token or tuple it needs, and
# later has .evaluate() called on it to actually produce a usable
# Python value (int, str, bool, ...). Splitting "build" from "evaluate"
# like this is what lets an expression tree be assembled once during
# parsing and then run - possibly many times, e.g. inside a loop -
# without re-parsing anything.
from SymbolTable import symbolTable

from Errors import Error

class Object:
    # Base class every value-holder below inherits from. On its own it
    # just remembers whatever it was built with as self.token; the
    # useful behavior (evaluate()) is added by each subclass.
    def __init__(self,value):
        self.token = value

    def cast(self):
        # Given a raw TokenObj (see LexicalParser.py), picks the right
        # subclass for its token_type and wraps the token's value in it -
        # e.g. a token_type of 'integer' becomes an Int object. Used
        # while parsing to turn a bare lexer token into something that
        # knows how to evaluate() itself. If the token's type isn't one
        # of the four listed here (for instance, an operator token),
        # cast() just hands back the original token unchanged.
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
    # Represents a reference to a variable - either reading its current
    # value, or (re)assigning it. Which one depends on how it was built;
    # see the two "modes" below.
    def __init__(self,value):

        # `value` is either a plain variable name (mode 2 - "read this
        # variable"), or a tuple describing a full assignment (mode 1 -
        # "write this variable"). Python's type(value).__name__ check
        # here is just asking "was I handed a tuple, or a bare name?" -
        # there's no separate flag passed in, the *shape* of what was
        # passed in is itself the signal.
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
            # Mode 2: just a bare variable name to look up later - see
            # the `else` branch of evaluate() below.
            self.name = value



    def evaluate(self):
        # Mode 1 (assignment) *writes* a value and reports whether it
        # succeeded; mode 2 (reference) *reads* a value back. Both paths
        # end up returning through this one method since callers don't
        # need to know or care which mode a given Var is in - they just
        # call .evaluate() either way.

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
            # Mode 2: look the name up in the symbol table instead of
            # writing to it. fetch_variable returns False if the name
            # isn't defined anywhere reachable, which is treated here as
            # a real error ('anwani' = "address"/reference error) rather
            # than silently returning something like None or 0.
            result = symbolTable.fetch_variable(self.name)
            if result:
                result = symbolTable.fetch_variable(self.name).evaluate()
            else:
                Error.throwException('anwani',self.name)            
                result = False

        return result

class Int(Object):
    # Wraps a numeric literal token (its raw text, e.g. "42" or "3.14")
    # and turns it into a real Python number only when evaluate() is
    # actually called. The class name stays "Int" (rather than being
    # renamed to something like "Number") to keep the ripple from this
    # change small - every other file that already refers to this class
    # (Object.cast()'s data_types dict, etc.) keeps working unchanged.
    # Whether the result comes back as an int or a float depends purely
    # on whether the literal's own text contains a '.' - the lexer only
    # ever hands this class digit-only or digit-dot-digit text (see
    # Tokens.integer in LexicalParser.py), so this check is unambiguous.
    def evaluate(self):

        text = str(self.token)
        return float(text) if '.' in text else int(text)

class Str(Object):
    # Wraps a string literal token. '{}'.format(...) is just a safe way
    # to get a plain string back regardless of what self.token already
    # is (it's normally already a string by this point, coming from the
    # lexer with its surrounding quotes stripped off).
    def evaluate(self):
        return '{}'.format(self.token)

class Bool(Object):
    # Wraps a boolean literal token ("true" / "false", as raw text).
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
