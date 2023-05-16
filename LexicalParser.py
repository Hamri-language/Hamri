import re
import enum

#set holding our lexeme units

class Tokens(enum.Enum):
   
   
   keyword = r'(chapa|kama|jaza|kwisha|kwanza|eleza)'
   divider = r'(\\[|\\]|\(|\))'
   boolean = r'true|false'
   integer = r'\.\b[0-9]+|[0-9]+'
   string = r'"(.*?)"|\'(.*?)\'|\b[0-9]+'
   variable = r'((\'[^\']*\'|([A-Za-z_]\w*(?:\.[a-z_]\w*)*))(?!\"\')|("[^"]*"|([a-z_]\w*(?:\.[a-z_]\w*)*))(?!\"\'))'
   operator = r'[\+\-\=\,]'
   


class LexicalParser:
   def __init__(self,script):
      self.script = self.read_source(script)
      self.token_list = []
      
   def read_source(self,arg):
      content = open(arg, "r")
      script = content.readlines()
      content.close(
      return script
      
   def parse(self):
      index = 0
      all_tokens = []
      
      for i,v in enumerate(self.script):
         

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
               
               self.token_list.append(
                  TokenObj(t.name,
                        t_[0].replace('"','').replace('\'','') if t.name == 'string' else t_[0],#remove string quotes statements
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
      
      return_match = True if len(pattern.findall(search_str)) > 0 else False
      
      
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
         
 
   
