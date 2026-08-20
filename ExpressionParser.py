# ExpressionParser turns a flat list of tokens/values that make up one
# expression (e.g. `2 + 3 * 4` already split into pieces) into a small
# tree of "Expression" objects that know how to compute their own
# result. Each Expression class below follows the same tiny pattern:
# remember its left and right operand in __init__, then combine them in
# evaluate(). Nothing here decides operator *precedence* - see the
# comment on ExpressionParser.parse() below for what that means in
# practice.
from Objects import *
from Logger import Log


class ExpressionParser:
    def __init__(self, args):
        # `args` is the token/value list this parser was built for -
        # kept as-is on self so parse() can look through it.
        self.tokens = args

        # Maps each operator's *symbol* (as it appears in the token
        # list, already normalized by the lexer - see WORD_OPERATORS in
        # LexicalParser.py for how a word like 'kabisa' ends up looking
        # like an operator here) to the Expression class that knows how
        # to evaluate it. Looking a symbol up in this dict is how
        # parse() below decides which class to build for each operator
        # it finds.
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
        # Builds the expression tree by walking the token list once,
        # left to right, and folding each operator into whatever's been
        # built so far. There is deliberately no concept of operator
        # precedence here (no "multiplication before addition" rule) -
        # `2 + 3 * 4` is evaluated strictly left to right as
        # `(2 + 3) * 4`, giving 20, not the 14 you'd get in ordinary
        # math notation. That's a known, documented limitation of the
        # language rather than a bug - see the "known pre-existing
        # limitations" note in CHANGELOG.md.

        #print("tokens before parsing: ",self.tokens)

        # Start with the very first item in the list as the running
        # result. If there's only one item and no operators at all
        # (e.g. just a single number), this is also the final answer -
        # the loop below simply never finds anything to do.
        return_val = self.tokens[0]

        #for the first value in expression

        # Walk everything *after* that first item. `enumerate` hands
        # back both a position (`count`) and the item at that position
        # (`i`) on each pass, which is what lets the operand lookup
        # below (`self.tokens[count + 2]`) find the right-hand value
        # that sits two slots after the item currently being checked.
        for count,i in enumerate(self.tokens[1:]):
            # Only a real token (as opposed to an already-built operand
            # like a Var or a number) can possibly be one of our
            # operators, so skip anything that isn't a TokenObj first.
            if type(i).__name__ == 'TokenObj':
                if i.value in self.operators.keys():
                    #print('found operator ',i.value,' in pass ',count)
                    #print('operands: left ',return_val," right ",self.tokens[count + 2])
                    # Fold the running result and the next operand
                    # together into a new Expression object of whichever
                    # class this operator maps to, then keep going -
                    # this new object becomes the running "left" operand
                    # for whatever operator comes after it, which is
                    # exactly what makes the left-to-right chaining work.
                    return_val = self.operators[i.value]((return_val,self.tokens[count + 2]))
                    #print('result object: ',return_val)


        #print("tokens results after parsing: ",self.tokens)
        #print('results after parsing: ',return_val)
        return return_val


class AdditionExpression:
    # Represents `left + right`. Every Expression class in this file
    # follows this same two-step shape: __init__ just stores its two
    # operands (which might be plain values, Var references, or another
    # nested Expression object - it doesn't matter which, since
    # everything supports .evaluate()); evaluate() is only called later,
    # once the surrounding statement actually needs the result, and is
    # where the real work happens.

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]


    def evaluate(self):

        Log(self.left,'Addition operation')
        Log(self.right,'Addition operation')

        # Resolve both sides down to plain Python values (numbers,
        # strings, etc) right before combining them - evaluate() is
        # only ever called once we actually need the answer, not when
        # the expression tree was first built.
        left = self.left.evaluate()
        right = self.right.evaluate()

        # Auto-stringify when mixing text with a number (e.g. "x is: " + x)
        # instead of letting Python's str+int TypeError leak through -
        # numeric + numeric still adds normally.
        if isinstance(left,str) or isinstance(right,str):
            return '{}{}'.format(left,right)
        return left + right


class MultiplicationExpression:
    # Represents `left * right`.

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() * self.right.evaluate()


class DivisionExpression:
    # Represents `left / right`.

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
    # Represents `left - right`.

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        Log(self.left,'Subtraction operation')
        Log(self.right,'Subtraction operation')

        return self.left.evaluate() - self.right.evaluate()


class EqualsExpression:
    # Represents `left == right` - Python's own equality rules apply,
    # so e.g. `true == 1` is True (a bool is a subclass of int in
    # Python). Use StrictEqualsExpression (`kabisa`/`hakika`) below when
    # that distinction needs to matter.

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() == self.right.evaluate()


class NotEqualsExpression:
    # Represents `left != right`.

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() != self.right.evaluate()


class LessThanExpression:
    # Represents `left < right`.

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() < self.right.evaluate()


class GreaterThanExpression:
    # Represents `left > right`.

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() > self.right.evaluate()


class LessEqualExpression:
    # Represents `left <= right`.

    def __init__(self,values):
        self.left = values[0]
        self.right = values[1]

    def evaluate(self):
        return self.left.evaluate() <= self.right.evaluate()


class GreaterEqualExpression:
    # Represents `left >= right`.

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
