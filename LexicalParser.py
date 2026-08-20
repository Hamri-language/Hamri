import re
import enum
import os
import sys

#set holding our lexeme units

# Word forms of some operators, so scripts can read more like Swahili
# sentences instead of leaning on symbols. Normalized down to their
# canonical symbol during tokenizing (see LexicalParser.parse) so the
# rest of the interpreter (StatementParser, ExpressionParser) never has
# to know these words exist - it only ever sees '>' / '<' / '='.
WORD_OPERATORS = {
   'inazidi': '>',   # "exceeds" -> greater than
   'haizidi': '<',   # "does not exceed" -> less than
   'ni': '=',        # "is" -> assignment
   'ongeza': '+',    # "add/increase" -> addition
   'punguza': '-',   # "reduce/decrease" -> subtraction
   'mara': '*',      # "times" -> multiplication
   'gawa': '/',      # "divide/share" -> division
   'sawa': '==',     # "equal/okay" -> loose equality
}

# Word-form operators that don't map onto an existing symbol - there's no
# '===' in Hamri's symbol set, so 'kabisa'/'hakika' ("completely/exactly",
# "certainly/truly") keep their own name but still need to be tagged as an
# 'operator' token (rather than 'keyword') so fetch_express() in
# StatementParser knows to keep reading the right-hand operand after them.
# Both are synonyms for the same strict-equality check.
OPERATOR_KEYWORDS = {'kabisa','hakika'}

class Tokens(enum.Enum):


   # Word-operators are wrapped in \b so they only match as whole words -
   # without that, 'ni' would also match inside ordinary variable names
   # like "kani" or "nina". 'huku' (for-loop), 'kutoka' (from), 'hadi'
   # (to/until), 'rudisha' (return), 'weka' (append to a list), 'kwenye'
   # (into/at - the target marker for 'weka' and for-each 'huku'),
   # 'idadi' (length of a list), 'ondoa' (remove an item from a list) and
   # 'darasa' (class) are plain structural keywords, same idea as kama/
   # wakati - not operators, so they aren't in WORD_OPERATORS/
   # OPERATOR_KEYWORDS.
   # NOTE: 'nafsi' ("self") is deliberately NOT a keyword here - unlike
   # darasa/kama/etc it doesn't trigger its own parsing branch, it's just
   # an ordinary variable name that happens to get auto-bound to the
   # current instance before a method call runs (see FunctionCallStatement).
   # Tagging it 'keyword' would stop it matching the 'variable'-typed
   # token checks that all the dot-access parsing relies on.
   # 'leta' ("bring") is the import keyword - 'leta X kutoka "faili"'
   # (whole class) or 'leta x kutoka X kutoka "faili"' (one specific
   # method of a class), reusing 'kutoka' ("from") the same way huku/ondoa
   # already do.
   # 'aina' ("kind/type") prints what kind of value an expression holds -
   # a small teaching/debugging aid carried over from the original Hamri
   # project (github.com/Hamri-language/Hamri), reimplemented properly
   # here as a bare-expression statement (matching chapa/rudisha's own
   # style) rather than the original's now-defunct 'aina(x)' call form.
   keyword = r'(chapa|kama|jaza|kwisha|kwanza|eleza|sivyo|wakati|huku|\bkutoka\b|\bhadi\b|\brudisha\b|\bweka\b|\bkwenye\b|\bidadi\b|\bondoa\b|\bdarasa\b|\bleta\b|\baina\b|\binazidi\b|\bhaizidi\b|\bni\b|\bkabisa\b|\bhakika\b|\bongeza\b|\bpunguza\b|\bmara\b|\bgawa\b|\bsawa\b)'
   # NOTE: '[' and ']' used to be written as '\\[' and '\\]' here, which in
   # a raw string is an escaped literal BACKSLASH followed by a bracket -
   # not the bracket itself. That silently meant square brackets were
   # never actually tokenized at all (finditer just skipped over them).
   # Fixed to a single backslash so they're matched like '(' and ')' are.
   # '.' (property/method access, e.g. mtu1.jina) lives here too - it's a
   # structural separator, not a computable operator.
   divider = r'(\[|\]|\(|\)|\.)'
   boolean = r'true|false'
   integer = r'\.\b[0-9]+|[0-9]+'
   string = r'"(.*?)"|\'(.*?)\'|\b[0-9]+'
   # NOTE: this used to also match a trailing (?:\.[a-z_]\w*)* on both
   # identifier alternatives, which silently fused a dotted path like
   # "mtu1.jina" into ONE variable token instead of three ('mtu1', '.',
   # 'jina') - nothing ever relied on that (dot access wasn't supported
   # at all), so it's removed now that '.' is its own divider token.
   variable = r'((\'[^\']*\'|([A-Za-z_]\w*))(?!\"\')|("[^"]*"|([a-z_]\w*))(?!\"\'))'
   # Order matters: multi-character operators must be tried before their
   # single-character prefixes (e.g. '==' before '=', '<=' before '<'),
   # otherwise the regex engine greedily matches the shorter one first.
   operator = r'(==|!=|<=|>=|<|>|\+|\-|\*|\/|\=|\,)'
   


class LexicalParser:
   def __init__(self,script,from_text=False):
      # from_text=True lets callers pass raw Hamri source code directly
      # (e.g. from main.py's embedded sample, or a GUI text widget)
      # instead of a file path on disk.
      self.script = script.splitlines(keepends=True) if from_text else self.read_source(script)
      self.token_list = []

   def read_source(self,arg):
      # Only reached when from_text=False - 'arg' is meant to be a path
      # to a .ham script file on disk. Fail with a clear message instead
      # of a raw traceback for the two most common mistakes: a typo'd
      # path, or accidentally passing literal source text here without
      # from_text=True.
      if not os.path.exists(arg):
         print('The file path you provided does not exist: {}'.format(arg))
         sys.exit(1)
      if not arg.endswith('.ham'):
         print('The file you provided is not a Hamri script file (expected a .ham extension): {}'.format(arg))
         sys.exit(1)
      content = open(arg, "r")
      script = content.readlines()
      content.close()
      return script
      
   def strip_comment(self,line):
      # Everything from an unquoted '#' to the end of the line is a
      # comment. Track quote state char-by-char so a '#' inside a string
      # literal (e.g. chapa "Price: #1") isn't mistaken for one.
      in_single = False
      in_double = False
      for idx,ch in enumerate(line):
         if ch == "'" and not in_double:
            in_single = not in_single
         elif ch == '"' and not in_single:
            in_double = not in_double
         elif ch == '#' and not in_single and not in_double:
            return line[:idx] + '\n'
      return line

   def parse(self):
      index = 0
      all_tokens = []

      for i,v in enumerate(self.script):
         v = self.strip_comment(v)

         tokens = [
               (x.group(),x.span()[0],i) for x in re.compile(r'{}'.format(
                   '|'.join(
                      [t.value for t in Tokens]
                      )
                   )
               ).finditer(v)
            ]
         
         for n in tokens:
            all_tokens.append(n)

      
      #build one humongous re pattern to find all our lexemes

      
      #print('{}'.format('|'.join([t.value for t in Tokens])))
      
      #tag all tokens with a type
      id_ = 0
      for t_ in all_tokens:
         for t in Tokens:
            if self.find_token_match(t_[0],t.value):

               token_type = t.name
               value = t_[0]

               # Word-form operators (inazidi/haizidi/ni) tag as 'keyword'
               # like any other reserved word, but the rest of the
               # interpreter expects to see the symbol ('>','<','=') it
               # already knows how to handle - so swap it in here, once,
               # at the source.
               if value in WORD_OPERATORS:
                  token_type = 'operator'
                  value = WORD_OPERATORS[value]
               elif value in OPERATOR_KEYWORDS:
                  token_type = 'operator'

               self.token_list.append(
                  TokenObj(token_type,
                        value.replace('"','').replace('\'','') if token_type == 'string' else value,#remove string quotes statements
                        t_[1],t_[2],id_
                        )
                  )
               break
         id_ = id_+1
                          
            
      return self
   
   def print_tokens(self,type_ = 'all'):
      for i in self.token_list:
         if type_ == 'all':
            print('-----------\nType: {}\nValue: {}\nLine: {}\nPosition: ({},{})\nOffset: {}\n-----------'.format(
               i.token_type,
               i.value,
               i.line,
               i.span()[0],
               i.span()[0]+i.size(),
               i.position()
            ))
         else:
            if type_ == i.token_type:
               print('-----------\nType: {}\nValue: {}\n-----------'.format(
                  i.token_type,
                  i.value,i.start,
                  i.start+i.len_))

         
   def count_tokens(self):
      count = len(self.token_list)
      print('-----------\nTokens: {}\n-----------'.format(count))
      return count
      
   def find_token_match(self,search_str,pat_):

      pattern = re.compile(pat_)

      # Must match the WHOLE extracted token, not just find pat_ somewhere
      # inside it - otherwise a string like "(you are an adult)" gets
      # misclassified as a divider just because it contains parentheses.
      return_match = pattern.fullmatch(search_str) is not None


      #strict check for to make sure integers in strings are avoided
      if pat_ == Tokens.integer.value:
         
         if len(re.compile(r'[\"\']').findall(search_str))>0:
            return_match = False
      
      return return_match
  

            

   
class TokenObj:
   def __init__(self, token_type, value,start,line,offset):
      self.token_type = token_type
      self.value = value
      self.line = line
      self.start = start
      self.offset = offset
      self.len_ = len(self.value)
   def value(self):
      return self.value
   
   def position(self):
      return self.offset
   
   def type(self):
      return self.token_type
   
   def size(self):
      return self.len_

   def span(self):
      return (self.start,self.start+self.len_)
   
   def evaluate(self):
      return self
         
 
   
