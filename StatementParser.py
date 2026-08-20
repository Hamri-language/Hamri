import sys

from ExpressionParser import ExpressionParser

from Objects import * 

from SymbolTable import symbolTable

from Logger import Log

from LexicalParser import LexicalParser, TokenObj

# tkinter isn't guaranteed to be installed in every environment this
# interpreter runs in (e.g. a headless server has no display), but the
# desktop Notepad IDE still passes a real Tk Text widget as the
# 'console' object. Fall back to a tiny stand-in so `tk.END` still
# resolves everywhere, even without tkinter installed.
try:
    import tkinter as tk
except ImportError:
    class _FakeTk:
        END = 'end'
    tk = _FakeTk()

# Module-level handle to whatever console object (Tk Text widget, web
# console shim, ...) the current run is using - set once via the
# 'the console gets wired up' statement further below and read back
# everywhere PrintStatement/TypeStatement/the run-start and run-end
# banners need to write output. `global console` here just declares
# that this name lives at module scope, so any function below that
# also writes `global console` before assigning to it is modifying
# this same shared variable rather than creating a local one.
global console
console = None


class StatementParser:
    
    def __init__(self,tokens):
        self.tokens = tokens
        self.token_position = 0
        self.if_counter = 0
        self.loop_counter = 0
        # Tracks the currently-open (not yet closed by 'kwisha')
        # IfStatement objects, so 'sivyo' knows which one to attach
        # its else-branch to.
        self.if_stack = []

        # Name of the darasa (class) currently being defined, if any -
        # lets 'eleza' know to register the method under a class-
        # qualified name ('darasa-ClassName-methodName') instead of a
        # bare one. A stack rather than a single value in case classes
        # ever end up defined in a nested position.
        self.class_stack = []

        # Tracks, for every currently-open block, whether entering it
        # pushed a symbolTable scope ('scoped' - kwanza/kama/eleza/wakati/
        # huku, all of which need the matching 'kwisha' to pop that scope
        # via EndBlockStatement) or not ('darasa' - a class body doesn't
        # push a scope at all, it only tracks class_stack, so its
        # matching 'kwisha' must NOT also trigger a pop_scope()).
        self.block_stack = []

        

        

    def parseStatement(self,parse_token):
        next_ = self.next_token() if self.token_position < len(self.tokens)-1 else None
        prev_ = self.prev_token() if self.token_position > 0 else None
        Log(parse_token.value,"parsing token")
        
        statement = None
        
        if parse_token.value == 'chapa' and next_ != None:
            Log('case for print')
            statement = PrintStatement(self.parse_expression_value())
        elif parse_token.value == 'aina' and next_ != None:
            Log('case for type introspection')
            statement = TypeStatement(self.parse_expression_value())
        elif parse_token.value == '=' and next_ != None and prev_ != None:
            Log('case for assignment')

            value = self.parse_expression_value()
            # qualify=True - this is an ordinary user assignment, so if
            # it's local it should be isolated to whichever call is
            # actually executing at runtime (see Var/SymbolTable.write_local),
            # not shared flatly across every function in the program.
            obj = Var((prev_.value,value,symbolTable.get_scope('var-scope'),True))
            statement = AssignmentStatement(obj)
        elif parse_token.value == 'eleza':
            Log('case for function definition')
            symbolTable.def_flag = True
            raw_name = next_.value
            # Inside a darasa block, a method's name gets class-qualified
            # ('darasa-Mtu-jenga' instead of just 'jenga') so it can't
            # collide with a top-level function or a method of the same
            # name on a different class - everything else (parameter
            # placeholders, calling, scoping) then works completely
            # unchanged, since it's still just a normal function under
            # the hood.
            function_name = 'darasa-{}-{}'.format(self.class_stack[-1],raw_name) if self.class_stack else raw_name
            self.token_position = next_.position() + 1

            statement = FunctionDefinitionStatement((function_name,self.fetch_express()))


        elif parse_token.value == 'kama':
            Log('case for if block')
            self.if_counter = self.if_counter + 1
            block_name = 'kama-{}'.format(self.if_counter)
            condition = ExpressionParser(self.fetch_express()).parse()

            statement = IfStatement((block_name,condition))
            self.if_stack.append(statement)

        elif parse_token.value == 'sivyo':
            Log('case for otherwise')
            # Attaches an else-branch to the innermost still-open kama;
            # does NOT push/pop the scope stack - it swaps the current
            # block in place, since 'kwisha' still only fires once for
            # the whole kama...sivyo...kwisha construct.
            if self.if_stack:
                current_if = self.if_stack[-1]
                self.if_counter = self.if_counter + 1
                else_name = 'sivyo-{}'.format(self.if_counter)
                current_if.set_else(else_name)
                symbolTable.set_function(else_name)
                symbolTable.context['function-scope'] = else_name

        elif parse_token.value == 'wakati':
            Log('case for while loop')
            self.loop_counter = self.loop_counter + 1
            loop_name = 'wakati-{}'.format(self.loop_counter)
            condition = ExpressionParser(self.fetch_express()).parse()

            statement = WhileStatement((loop_name,condition))

        elif parse_token.value == 'huku':
            Log('case for for-loop')
            # Two forms: 'huku <var> kutoka <start> hadi <end>' (counted
            # range) or 'huku <var> kwenye <list>' (for-each over a
            # list's items). fetch_express() already stops on its own
            # once it hits a non-operator token, so it naturally stops
            # right at 'kutoka'/'hadi'/'kwenye' without any extra
            # bookkeeping - we just need to manually step over those
            # marker keywords in between.
            self.loop_counter = self.loop_counter + 1
            loop_name = 'huku-{}'.format(self.loop_counter)

            var_name = self.next_token().value
            self.token_position = self.token_position + 1  # land on <var>

            marker = self.next_token()

            if marker is not None and marker.value == 'kwenye':
                self.token_position = self.token_position + 1  # land on 'kwenye'
                list_name = self.next_token().value
                self.token_position = self.token_position + 1  # land on <list-name>

                statement = ForEachStatement((loop_name,var_name,list_name))

            else:
                self.token_position = self.token_position + 1  # land on 'kutoka'
                start_expr = self.parse_expression_value()

                self.token_position = self.token_position + 1  # land on 'hadi'
                end_expr = self.parse_expression_value()

                statement = ForStatement((loop_name,var_name,start_expr,end_expr))

        elif parse_token.value == 'rudisha':
            Log('case for return statement')
            # 'rudisha' can stand alone (just exits the function early,
            # e.g. as a guard clause) or carry a value: 'rudisha <expr>'.
            # A bare rudisha is always immediately followed by 'kwisha'
            # (every block ends with exactly one) - keyword-typed tokens
            # never start a real expression, so that's how "no value" is
            # told apart from an actual expression starting here.
            if next_ is None or next_.token_type == 'keyword':
                expr = None
            else:
                expr = self.parse_expression_value()

            statement = ReturnStatement(expr)

        elif parse_token.value == 'weka':
            Log('case for list append')
            # 'weka <value-expr> kwenye <list-name>' - "put <value> into
            # <list>". fetch_express() naturally stops at 'kwenye' (a
            # keyword, not an operator), same trick as kutoka/hadi.
            value_expr = self.parse_expression_value()

            self.token_position = self.token_position + 1  # land on 'kwenye'
            list_name = self.next_token().value
            self.token_position = self.token_position + 1  # land on <list-name>

            statement = AppendStatement(list_name,value_expr)

        elif parse_token.value == 'ondoa':
            Log('case for list remove')
            # 'ondoa <index-expr> kutoka <list-name>' - "remove <index>
            # from <list>". Removes by position (like Python's `del
            # lst[i]`), not by matching a value - reuses the existing
            # 'kutoka' ("from") keyword as the marker, same trick as
            # weka's 'kwenye'.
            index_expr = self.parse_expression_value()

            self.token_position = self.token_position + 1  # land on 'kutoka'
            list_name = self.next_token().value
            self.token_position = self.token_position + 1  # land on <list-name>

            statement = RemoveStatement(list_name,index_expr)

        elif parse_token.value == 'darasa':
            Log('case for class definition')
            # 'darasa ClassName ... kwisha' - a class body only ever
            # contains 'eleza' method definitions (no loose statements),
            # so unlike kwanza/kama/wakati/huku there's no need to push a
            # symbolTable scope here at all - we just need 'eleza' below
            # to know it should class-qualify method names until the
            # matching 'kwisha'. That's tracked via class_stack; the
            # matching 'kwisha' is told apart from a "real" scoped
            # block's kwisha via block_stack (see below).
            class_name = next_.value
            self.token_position = self.token_position + 1  # land on <class-name>
            symbolTable.set_class(class_name)
            self.class_stack.append(class_name)
            self.block_stack.append('darasa')

        elif parse_token.value == 'leta':
            Log('case for import')
            # Two forms, both starting with a comma-separated name list:
            #   leta Mtu, Mnyama kutoka "faili"          - whole class(es)
            #   leta salamu, tembea kutoka Mtu kutoka "faili"  - specific
            #     method(s) of one class, imported standalone
            # Told apart by what follows the first 'kutoka': a string
            # literal means "that's the file" (whole-class form); a bare
            # name means "that's a class name" (selective-method form),
            # with a second 'kutoka' + string still to come. This is all
            # resolved immediately, at parse time - like 'darasa'/'eleza',
            # 'leta' has no runtime behaviour of its own, it just makes
            # names available for the rest of the file to use.
            names = [next_.value]
            self.token_position = self.token_position + 1  # land on first name

            while self.next_token() is not None and self.next_token().value == ',':
                self.token_position = self.token_position + 1  # land on ','
                self.token_position = self.token_position + 1  # land on next name
                names.append(self.tokens[self.token_position].value)

            self.token_position = self.token_position + 1  # land on 'kutoka'
            after_kutoka = self.next_token()

            # leta has no runtime behaviour of its own (see _parse_module),
            # so a failed import is reported right here, at parse time -
            # symbolTable.current_line/current_column (updated only as
            # statements *execute*) wouldn't reflect this location, so
            # it's passed through explicitly instead.
            leta_line = parse_token.line + 1
            leta_column = parse_token.start + 1

            if after_kutoka is not None and after_kutoka.token_type == 'string':
                self.token_position = self.token_position + 1  # land on the filename string
                filename = self.tokens[self.token_position].value
                self.import_classes(names,filename,leta_line,leta_column)
            else:
                class_name = after_kutoka.value if after_kutoka is not None else None
                self.token_position = self.token_position + 1  # land on <class-name>
                self.token_position = self.token_position + 1  # land on 'kutoka'
                self.token_position = self.token_position + 1  # land on the filename string
                filename = self.tokens[self.token_position].value
                self.import_methods(names,class_name,filename,leta_line,leta_column)

        elif parse_token.value == 'kwanza':
            Log('case for main block')
            # kwanza ("first") is the program's required entry point -
            # only code inside kwanza...kwisha actually runs. Statements
            # outside it (e.g. helper function definitions) are still
            # parsed but never auto-executed. No statement object is
            # needed here; opening the block is just a scope change.
            symbolTable.push_scope('kwanza')
            self.block_stack.append('scoped')

        elif parse_token.value == 'kwisha':
            Log('case for end block')
            symbolTable.reset_flags()
            current_scope = symbolTable.get_scope('function-scope')
            if self.if_stack and current_scope in (self.if_stack[-1].true_name,self.if_stack[-1].else_name):
                # This kwisha closes the kama (and its sivyo, if any)
                # that's currently on top of the stack.
                self.if_stack.pop()

            # darasa doesn't push a scope (see above), so its matching
            # kwisha must skip EndBlockStatement/pop_scope entirely -
            # otherwise it would incorrectly pop whatever scope was
            # already active *before* the class definition started.
            block_kind = self.block_stack.pop() if self.block_stack else 'scoped'

            if block_kind == 'darasa':
                if self.class_stack:
                    self.class_stack.pop()
            else:
                statement = EndBlockStatement(symbolTable.context)
            
        elif parse_token.value == 'jaza':
            Log('case for user input')
            #Log(type(self.fetch_express()))

            # Note: fetch_express() already reads relative to "current
            # position + 1", same as the 'chapa' case above - advancing
            # token_position first (as this used to) skips the prompt
            # string entirely and misreads the storage variable.
            statement = InputStatement(self.fetch_express())
            
        elif parse_token.token_type == 'variable' and next_.value == '(':
            Log('case for function call')
            function_name = parse_token.value

            self.token_position = self.token_position + 1 #advance by one to fly over the first divider
            #Log(self.fetch_express())

            statement = FunctionCallStatement((function_name,self.fetch_express()))

        elif parse_token.token_type == 'variable' and next_.value == '[':
            Log('case for list indexing')
            # `orodha[i]` - either read-as-part-of-a-larger-statement
            # (handled by try_parse_index(), used from '=' and 'chapa'
            # above, so this branch only ever sees it as the *start* of
            # its own statement) or a full index-assignment,
            # `orodha[i] = <value>`.
            list_name = parse_token.value
            self.token_position = self.token_position + 1  # land on '['
            index_expr = ExpressionParser(self.fetch_express()).parse()  # stops at ']'

            after_bracket = self.tokens[self.token_position + 2] if self.token_position + 2 < len(self.tokens) else None

            if after_bracket is not None and after_bracket.value == '=':
                self.token_position = self.token_position + 2  # skip ']', land on '='
                value_expr = self.parse_expression_value()
                statement = IndexAssignmentStatement(list_name,index_expr,value_expr)
            else:
                # A bare `orodha[i]` with nothing capturing it has no
                # observable effect - there's nothing to execute. The
                # closing ']' is skipped harmlessly as a phantom token,
                # same as the ')' left over after any function call.
                statement = None

        elif parse_token.token_type == 'variable' and next_.value == '.':
            Log('case for property/method access')
            # `obj.member` - either a property write (`obj.jina = value`),
            # a method call used as its own statement (`obj.sema()`), or
            # (like a bare `orodha[i]`) a no-op read with nothing to
            # capture it. Reading a property/calling a method as *part*
            # of a larger expression is handled separately by
            # try_parse_property_access(), used from '=' and 'chapa'.
            object_name = parse_token.value
            self.token_position = self.token_position + 1  # land on '.'
            member_name = self.next_token().value
            self.token_position = self.token_position + 1  # land on <member-name>

            after_member = self.next_token()

            if after_member is not None and after_member.value == '(':
                self.token_position = self.token_position + 1  # land on '('
                args = self.fetch_express()
                statement = MethodCallStatement(object_name,member_name,args)
            elif after_member is not None and after_member.value == '=':
                self.token_position = self.token_position + 1  # land on '='
                value_expr = self.parse_expression_value()
                statement = PropertyAssignmentStatement(object_name,member_name,value_expr)
            else:
                statement = None

        else:
            Log('default case')
            
            
            

        #statement = switcher[parse_token.token_type][parse_token.value] if parse_token.token_type in switcher.keys() else None

        return statement

    def _parse_module(self,filename):
        # Fetches and parses an external file's *definitions* (darasa/
        # eleza) into the shared symbolTable, for 'leta' to import from -
        # via a completely independent StatementParser instance (its own
        # token_position/if_stack/class_stack/block_stack) that just
        # happens to register everything into the same symbolTable
        # singleton, exactly as if it had been typed directly into this
        # file. Returns True if the file was found and parsed, False if
        # symbolTable.load_module_source() couldn't find/read it.
        source = symbolTable.load_module_source(filename)
        if source is None:
            return False

        kwanza_before = len(symbolTable.table['functions']['kwanza'])

        tokens = LexicalParser(source,from_text=True).parse()
        sub_parser = StatementParser(tokens.token_list)
        sub_parser.parse(symbolTable.console)

        # A library file might (e.g. for its own standalone testing) have
        # its own 'kwanza' block - only its definitions are wanted here,
        # not its main block's statements running as though they were
        # part of *this* program's kwanza.
        del symbolTable.table['functions']['kwanza'][kwanza_before:]

        return True

    def import_classes(self,names,filename,line=None,column=None):
        # 'leta A, B kutoka "faili"' - pulls in one or more whole classes.
        if not self._parse_module(filename):
            Error.throwException('leta',filename,line,column)
            return
        for name in names:
            if name not in symbolTable.table['classes']:
                Error.throwException('leta','{} ({})'.format(name,filename),line,column)

    def import_methods(self,names,class_name,filename,line=None,column=None):
        # 'leta a, b kutoka ClassName kutoka "faili"' - pulls in one or
        # more specific methods of a class, callable standalone (see
        # SymbolTable.alias_function).
        if not self._parse_module(filename):
            Error.throwException('leta',filename,line,column)
            return
        for name in names:
            qualified_name = 'darasa-{}-{}'.format(class_name,name)
            if not symbolTable.alias_function(name,qualified_name):
                Error.throwException('leta','{}.{} ({})'.format(class_name,name,filename),line,column)

    def try_parse_special_value(self):
        # Tries each of the "not a plain fetch_express() expression"
        # shapes in turn - a list literal, a length lookup, a property
        # read/method call, an indexed read, or a function call - and
        # returns the first one that matches (or None if none do, letting
        # the caller fall back to a plain fetch_express()). Every one of
        # these leaves self.token_position sitting exactly ON the last
        # token it consumed (the closing ']'/')' or the bare name/value
        # itself), so parse_expression_value() below can seamlessly keep
        # reading a trailing operator + operand after it, the same way
        # fetch_express() does for a plain value.
        return (self.try_parse_list_literal()
                or self.try_parse_length()
                or self.try_parse_property_access()
                or self.try_parse_index()
                or self.try_parse_call())

    def parse_expression_value(self):
        # Shared by every place that used to do
        # "try_parse_special_value(), falling back to a plain
        # fetch_express()" - now also keeps reading past the special
        # value if it's followed by an operator, e.g.
        # `jina = nafsi.jina + " Mkenya"` or `chapa square(2) + 1`,
        # instead of the special value silently swallowing the rest of
        # the expression.
        special = self.try_parse_special_value()
        if special is not None:
            value = ExpressionParser(self.continue_express(special)).parse()
        else:
            value = ExpressionParser(self.fetch_express()).parse()
        return self.try_parse_ternary(value)

    def try_parse_ternary(self,true_value):
        # Detects a trailing '<true_value> kama <condition> sivyo
        # <false_value>' ternary suffix right after an already-parsed
        # value - a real inline conditional expression (like Python's
        # 'x if cond else y'), e.g.
        # `jina kama jina sawa na "Cookie" sivyo "Guest"`. 'kama' is a
        # keyword, not an operator, so fetch_express()'s own
        # operand-reading loop already stops cleanly right before it -
        # this picks up exactly where that left off.
        #
        # Requires 'sivyo' - if it's missing (a malformed/incomplete
        # ternary), token_position is rewound to right where it was
        # before this method ever looked at 'kama', so the caller falls
        # back to treating 'kama' as the start of a brand new statement
        # (an ordinary if-block) exactly as it always has, rather than
        # this method guessing at what a half-written ternary meant.
        if self.next_token() is None or self.next_token().value != 'kama':
            return true_value

        rollback_position = self.token_position
        self.token_position = self.token_position + 1  # land on 'kama'
        condition = ExpressionParser(self.fetch_express()).parse()

        if self.next_token() is None or self.next_token().value != 'sivyo':
            self.token_position = rollback_position
            return true_value

        self.token_position = self.token_position + 1  # land on 'sivyo'
        # Recursing (rather than a single fetch_express()) lets the
        # false-branch itself be another ternary, so
        # 'a kama x sivyo b kama y sivyo c' chains like an else-if
        # ladder, evaluated left to right.
        false_value = self.parse_expression_value()

        return ConditionalExpression(true_value,condition,false_value)

    def continue_express(self,first):
        # Same operator-chaining loop as fetch_express()'s own while-loop,
        # but starting from an already-parsed first value (e.g. a
        # PropertyExpression or CallExpression) instead of casting the
        # current token - lets a special value returned by
        # try_parse_special_value() combine with a trailing operator,
        # e.g. continuing to read "+ ' Mkenya'" after `nafsi.jina`.
        # Uses read_operand() (not a plain token cast) for every later term
        # too, same as fetch_express()'s own loop - otherwise a *second*
        # special value further along the same chain (e.g. the nafsi.sauti
        # in `nafsi.jina + " anasema " + nafsi.sauti`) would silently fall
        # back to being cast as a bare variable reference instead of being
        # recognized as its own property read.
        return_val = [first]
        while self.next_token() is not None and self.next_token().token_type == 'operator':
            operator_token = self.next_token()
            if operator_token.value != ',':
                return_val.append(operator_token)
            self.token_position = self.token_position + 1
            return_val.append(self.read_operand())
        return return_val

    def try_parse_property_access(self):
        # Detects `name.member` (property read, e.g. `x = mtu1.jina`) or
        # `name.member(args)` (method call, e.g. `x = mtu1.sema_habari()`)
        # starting right after the current token.
        first = self.next_token()
        second = self.tokens[self.token_position + 2] if self.token_position + 2 < len(self.tokens) else None

        if first is not None and first.token_type == 'variable' and second is not None and second.value == '.':
            object_name = first.value
            third = self.tokens[self.token_position + 3] if self.token_position + 3 < len(self.tokens) else None
            if third is None:
                return None
            member_name = third.value
            fourth = self.tokens[self.token_position + 4] if self.token_position + 4 < len(self.tokens) else None

            if fourth is not None and fourth.value == '(':
                self.token_position = self.token_position + 4  # land on '('
                args = self.fetch_express()
                self.token_position = self.token_position + 1  # land on ')' (fetch_express stops one token early)
                return MethodCallExpression(object_name,member_name,args)
            else:
                self.token_position = self.token_position + 3  # land on <member-name>
                return PropertyExpression(object_name,member_name)

        return None

    def try_parse_list_literal(self):
        # Detects a `[...]` list literal starting right after the current
        # token - e.g. `[1, 2, 3]` or `[1, [2, 3], 4]`. Unlike
        # fetch_express()'s comma handling (used for flat argument lists),
        # this recurses into itself for any element that's itself a `[`,
        # so lists can nest to any depth. Fully consumes through its own
        # closing ']' (leaves self.token_position sitting ON it) rather
        # than relying on a later "phantom skip" - important so that,
        # when called recursively for a nested element, the *outer* list
        # can correctly see what comes right after the inner ']' (a ','
        # or the outer ']').
        first = self.next_token()

        if first is None or first.value != '[':
            return None

        self.token_position = self.token_position + 1  # land on '['
        elements = []

        if self.next_token() is not None and self.next_token().value == ']':
            self.token_position = self.token_position + 1  # land on ']' (empty list)
            return ListLiteral(elements)

        while True:
            nested = self.try_parse_list_literal()
            if nested is not None:
                elements.append(nested)
            else:
                # An element can also be a `name(args)` call - most
                # importantly, a class constructor call like `Mtu("Amara")`,
                # so a list of instances (`[Mtu("Amara"), Mtu("Juma")]`) can
                # be built directly. CallExpression already transparently
                # handles "name is actually a darasa" via
                # FunctionCallStatement.execute(), so no extra branching is
                # needed here for that case.
                elem_token = self.tokens[self.token_position + 1] if self.token_position + 1 < len(self.tokens) else None
                after_elem = self.tokens[self.token_position + 2] if self.token_position + 2 < len(self.tokens) else None
                if elem_token is not None and elem_token.token_type == 'variable' and after_elem is not None and after_elem.value == '(':
                    function_name = elem_token.value
                    self.token_position = self.token_position + 2  # land on '('
                    args = self.fetch_express()
                    self.token_position = self.token_position + 1  # land on ')' (fetch_express stops one token early)
                    elements.append(CallExpression(function_name,args))
                else:
                    self.token_position = self.token_position + 1  # move onto the element token
                    elements.append(Object(self.tokens[self.token_position]).cast())

            after = self.next_token()
            if after is not None and after.value == ',':
                self.token_position = self.token_position + 1  # land on ','
                continue
            elif after is not None and after.value == ']':
                self.token_position = self.token_position + 1  # land on ']'
                break
            else:
                # Malformed (missing closing bracket) - bail out rather
                # than looping forever or crashing.
                break

        return ListLiteral(elements)

    def try_parse_length(self):
        # Detects `idadi <list-name>` (length of a list) starting right
        # after the current token.
        first = self.next_token()

        if first is not None and first.value == 'idadi':
            self.token_position = self.token_position + 1  # land on 'idadi'
            list_name = self.next_token().value
            self.token_position = self.token_position + 1  # land on <list-name>
            return LengthExpression(list_name)

        return None

    def try_parse_index(self):
        # Detects a `name[index-expr]` indexed read starting right after
        # the current token - e.g. the right-hand side of `x = orodha[0]`
        # or `chapa orodha[0]`. (The left-hand-side/assignment-target
        # case, `orodha[0] = value`, is handled separately in
        # parseStatement, since it needs to become a whole statement
        # rather than a value.)
        first = self.next_token()
        second = self.tokens[self.token_position + 2] if self.token_position + 2 < len(self.tokens) else None

        if first is not None and first.token_type == 'variable' and second is not None and second.value == '[':
            list_name = first.value
            self.token_position = self.token_position + 2  # land on '['
            index_expr = ExpressionParser(self.fetch_express()).parse()
            self.token_position = self.token_position + 1  # land on ']' (fetch_express stops one token early)
            return IndexExpression(list_name,index_expr)

        return None

    def try_parse_call(self):
        # Lets a function's return value be captured as part of a larger
        # statement - `x = square(5)` or `chapa square(5)` - by detecting
        # a `name(...)` shape starting right after the current token and,
        # if found, consuming it and returning a CallExpression. Returns
        # None *without* consuming anything if the shape doesn't match,
        # so the caller falls back to the normal fetch_express() path.
        first = self.next_token()
        second = self.tokens[self.token_position + 2] if self.token_position + 2 < len(self.tokens) else None

        if first is not None and first.token_type == 'variable' and second is not None and second.value == '(':
            function_name = first.value
            self.token_position = self.token_position + 2  # land on '('
            args = self.fetch_express()
            self.token_position = self.token_position + 1  # land on ')' (fetch_express stops one token early)
            return CallExpression(function_name,args)

        return None

    def read_operand(self):
        # Tries every "special value" shape first - list literal, length,
        # property/method access, indexed read, function call - so an
        # operand ANYWHERE in an expression (not just a leading one) can
        # be one of these, e.g. the `mtu1.jina` in `"Habari, " + mtu1.jina`,
        # or the `orodha[0]` in `f(orodha[0], 5)`. Falls back to casting
        # the current token directly (the original, single-token-only
        # behaviour) if none of them match.
        special = self.try_parse_special_value()
        if special is not None:
            return special
        operand = Object(self.next_token()).cast()
        self.token_position = self.token_position + 1
        return operand

    def fetch_express(self):
        next_ = self.next_token()

        Log('Fetching expression ')

        if next_ is None:
            # Statement was the last token in the script (e.g. a lone
            # 'chapa "hi"' with nothing after it) - nothing more to read.
            return_val = []

        elif next_.token_type == 'divider':
            return_val = []


        else:

            # Read one operand, then keep alternating
            # "operator, operand, operator, operand, ..." for as long as
            # the token right after the current position is tagged as an
            # operator - this builds up the flat list that
            # ExpressionParser.parse() later folds left-to-right into a
            # tree of Expression objects (see ExpressionParser.py).
            return_val = [self.read_operand()]
            Log(return_val[0],'First Token')

            while self.next_token() is not None and self.next_token().token_type == 'operator':
                operator_token = self.next_token()
                if operator_token.value != ',':
                    # A comma is tagged as an 'operator' token by the
                    # lexer too (see Tokens.operator in LexicalParser.py)
                    # purely so it's recognized here as "keep reading,
                    # there's another operand coming" - but it isn't a
                    # real operator ExpressionParser knows how to
                    # evaluate, so it's deliberately never appended to
                    # the list, only used to decide whether to loop again.
                    return_val.append(operator_token) #add our operator

                self.token_position = self.token_position + 1 #advance our execution loop

                return_val.append(self.read_operand()) #add our term

        Log(return_val,'Evaluated expression')
        return return_val
        
    
    def print_statements(self):
        # Debug helper - dumps the whole interpreter-wide variable/
        # function/class table as it currently stands. Never called
        # during normal execution; handy to uncomment a call to this
        # while troubleshooting a script that isn't behaving as expected.
        print(symbolTable.table)
            
    def next_token(self):
        # The token one position ahead of wherever parsing currently is.
        # Returns None instead of raising an IndexError when that would
        # run past either end of the token list, so callers can simply
        # check "is next_token() None?" instead of wrapping every call
        # in a try/except.
        pos = self.token_position + 1
        return self.tokens[pos] if 0 <= pos < len(self.tokens) else None

    def prev_token(self):
        # Same idea as next_token(), but one position behind instead of
        # ahead.
        pos = self.token_position - 1
        return self.tokens[pos] if 0 <= pos < len(self.tokens) else None

    def parse(self,arg=None):
        global console

        console = arg
        symbolTable.console = arg

        Log('=======================')
        Log('Statement Parsing')
        Log('=======================')        
        
        while self.token_position < len(self.tokens):

            # Captured *before* parseStatement() runs, since parsing a
            # statement advances self.token_position to wherever it
            # finished (its last consumed token) - only the token it
            # started on tells us the line the statement actually began
            # on. TokenObj.line is 0-indexed (see LexicalParser); +1
            # here so every line number that ever reaches the user
            # (error messages) matches what they'd count in an editor.
            start_line = self.tokens[self.token_position].line + 1

            # Same idea as start_line above, but for the column: how many
            # characters into that line the statement's first token
            # starts (TokenObj.start, from LexicalParser - also 0-indexed,
            # so +1 here too, matching how a text editor numbers columns
            # starting from 1 rather than 0).
            start_column = self.tokens[self.token_position].start + 1

            statement = self.parseStatement(self.tokens[self.token_position])

            if statement is not None:
                statement.line = start_line
                statement.column = start_column

            #print('Function definition flag:',symbolTable.def_flag)

            Log(statement,'Evaluated statement')
            Log(symbolTable.get_scope('function-scope'),'Current context')
            
            symbolTable.table['functions'][symbolTable.get_scope('function-scope')].append(statement) if statement else None
            
            Log(symbolTable.table,'Current symbol table state')
            
            if type(statement).__name__ == 'FunctionDefinitionStatement':

                #change to a fresh local scope for the function body;
                #'kwisha' will pop back to whatever scope we came from

                symbolTable.push_scope(statement.name,'local')
                self.block_stack.append('scoped')

            elif type(statement).__name__ == 'IfStatement':

                #route subsequent statements into this if-block until 'kwisha'
                #(or into its sivyo branch, see the 'sivyo' case
                #above); variables stay in the enclosing (not a fresh
                #local) scope

                symbolTable.push_scope(statement.true_name)
                self.block_stack.append('scoped')

            elif type(statement).__name__ == 'WhileStatement':

                #route subsequent statements into this loop's body until
                #'kwisha'; variables stay in the enclosing scope, same as kama

                symbolTable.push_scope(statement.name)
                self.block_stack.append('scoped')

            elif type(statement).__name__ in ('ForStatement','ForEachStatement'):

                #same idea as WhileStatement - body statements are routed
                #into this loop's own scope until 'kwisha', while the loop
                #variable and everything else stay in the enclosing scope

                symbolTable.push_scope(statement.name)
                self.block_stack.append('scoped')

            self.token_position = self.token_position + 1

                
            
        return self
        

    def execute(self):
        #clear our console
        
        global console
        
        # Falls back to plain print() whenever no console object was
        # supplied (e.g. running a script directly via main.py, with no
        # Tk widget/web console in the picture) - the same fallback
        # Errors._report() already uses, so a script never runs
        # completely silently just because .parse() wasn't given a
        # console.
        if console is not None:
            console.insert(1.0,'=====================================\nRunning Hamri script\n=====================================\n')
        else:
            print('=====================================\nRunning Hamri script\n=====================================')
        Log('=======================')
        Log('Statement Execution')
        Log('=======================')

        # Only the explicit 'kwanza' (main) block actually runs. This is
        # a fixed name, not "whatever scope parsing ended on" - after a
        # properly closed kwanza...kwisha, the parser scope will already
        # have popped back to 'nje' by the time we get here.
        if not symbolTable.table['functions']['kwanza']:
            message = 'Hakuna kwanza (no main block found) - wrap the code you want to run in kwanza ... kwisha.\n'
            if console is not None:
                console.insert(tk.END,message)
            else:
                print(message)
            Log(message,'Execution')

        for i in symbolTable.table['functions']['kwanza']:

            # A bare 'rudisha' reaching all the way out here (not inside
            # any function) has no caller left to return to - treat it as
            # an early, intentional stop of the whole program.
            if symbolTable.exit() == 0 and not symbolTable.is_returning():
                Log('kwanza','Executing from scope')
                Log(i,'Executing statement')
                symbolTable.current_line = i.line
                symbolTable.current_column = i.column
                i.execute()

            else:
                break
            
        if symbolTable.exit() == 0:
            if console is not None:
                console.insert(tk.END,'\n=====================================\nHamri script execution success with exit code 0\n=====================================')
            else:
                print('\n=====================================\nHamri script execution success with exit code 0\n=====================================')

            Log('\n=====================================\nHamri script execution success with exit code 0\n=====================================','Executing Success')
        else:
            if console is not None:
                console.insert(tk.END,'\n=====================================\nHamri script execution fail with exit code 1\n=====================================')
            else:
                print('\n=====================================\nHamri script execution fail with exit code 1\n=====================================')
        
        
        #try:
            
            #for i in symbolTable.table['functions'][symbolTable.get_scope('function-scope')]:
                
                #Log(symbolTable.get_scope('function-scope'),'Executing from scope')
                
                #Log(i,'Executing statement')
                #i.execute()
                
                
            #print('\n=====================================\nHamri script execution success with exit code 0\n=====================================')
                    
        #except Exception as e:
            #Log(e,'Exception')
            #print('\n=====================================\nHamri script execution failed with exit code 1\n=====================================')






class Statement:
    def __init__(self):
        None

    def execute(self):
        None


    
class FunctionCallStatement(Statement):
    def __init__(self,arg):
        self.name = arg[0]
        self.params = arg[1]
        # Set when this call is actually a method call bound to a
        # specific object (see MethodCallExpression) or the constructor
        # step of instantiating a new object (see the 'darasa' branch
        # below) - the instance gets bound to a local 'nafsi' variable
        # before the body runs, exactly like any other parameter.
        self.instance = arg[2] if len(arg) > 2 else None
        # What 'rudisha' inside this function last produced, once
        # execute() has run - None if the function never hit a rudisha
        # (or was never called with a return value). For a class
        # instantiation call, this instead ends up holding the newly
        # created instance itself (see below).
        self.return_value = None



    def execute(self):

        if self.name in symbolTable.table['classes']:
            # `Mtu(args)` where 'Mtu' is a class, not a function -
            # construct a new instance instead of calling a function.
            # Reuses this same class for running the constructor (if the
            # class defines one) purely so argument-binding/nafsi/return-
            # flag handling don't need to be duplicated.
            instance = Instance(self.name)
            constructor_name = 'darasa-{}-jenga'.format(self.name)
            if constructor_name in symbolTable.table['functions']:
                constructor_call = FunctionCallStatement((constructor_name,self.params,instance))
                constructor_call.execute()
                # A constructor's own 'rudisha' (if it used one) is
                # intentionally discarded - instantiating a class always
                # yields the instance itself, not whatever the
                # constructor happened to return.
            self.return_value = instance
            return

        if self.name not in symbolTable.table["functions"]:
            # Calling something that was never defined with 'eleza' used
            # to raise a raw Python KeyError straight through to the user.
            Error.throwException('kazi',self.name)
            self.return_value = None
            return

        #assign our function definition arguments to the calling argument values before running function
        assignments = list(zip(symbolTable.get_function_arguments(self.name),self.params))

        Log(list(assignments),'Function Arguments')

        for i in assignments:

            Var((i[0],i[1],'local')).evaluate()

        if self.instance is not None:
            # Bind 'nafsi' the same way a normal parameter is bound - a
            # plain local variable, just namespaced under this call's
            # qualified name so it doesn't leak into unrelated calls.
            Var(('function-{}-nafsi'.format(self.name),self.instance,'local')).evaluate()

        #enable our call flag

        symbolTable.en_flag('call',self.name)

        # Defensive: make sure we're not somehow starting this call already
        # "returning" from something unrelated.
        symbolTable.clear_return()

        for i in symbolTable.table["functions"][self.name]:

            if symbolTable.exit() != 0 or symbolTable.is_returning():
                break

            Log(self.name,'Executing from function scope')

            Log(i,'Executing statement')

            symbolTable.current_line = i.line
            symbolTable.current_column = i.column
            i.execute()

        # This is the function-call boundary: absorb the return flag here
        # so it stops propagating - the caller's own control flow (the
        # loop/block it called us from) must not also think *it* should
        # return just because the function we called did.
        self.return_value = symbolTable.return_value
        symbolTable.clear_return()

        # Pop just this call off the call stack (restoring call_flag to
        # whichever call was running before it, if any) rather than
        # unconditionally clearing call_flag to False - that used to mean
        # a nested call (function A calling function B) would, the moment
        # B returned, make A's *own* remaining local variables look like
        # they were no longer "inside a call" at all, so they'd leak into
        # globals instead of staying isolated to A.
        symbolTable.def_flag = False
        symbolTable.pop_call()


class CallExpression(Object):
    # Lets a function's return value be used directly - `x = square(5)`
    # or `chapa square(5)` - instead of only being able to call a
    # function as its own standalone statement. Runs the call fresh every
    # time it's evaluated (so it re-reads current argument values each
    # time, same as any other expression), and yields whatever 'rudisha'
    # produced inside it - None if it never hit one.
    def __init__(self,name,args):
        self.call = FunctionCallStatement((name,args))

    def evaluate(self):
        self.call.execute()
        return self.call.return_value


def _fetch_list(list_name):
    # Shared lookup used by every list operation (index read/write,
    # append, length, for-each): finds the variable, makes sure it's
    # actually holding a list, and reports a clear error otherwise
    # instead of a raw Python crash. Returns None (with the relevant
    # error already thrown) if anything's wrong.
    stored = symbolTable.fetch_variable(list_name)
    if not stored:
        Error.throwException('anwani',list_name)
        return None
    value = stored.evaluate()
    if not isinstance(value,list):
        Error.throwException('orodha',list_name)
        return None
    return value


class Instance:
    # A single object created from a 'darasa' (class). Its properties
    # live in their own dedicated corner of symbolTable's variable
    # storage (keyed by scope_key, one per instance) - completely
    # separate from every other instance's properties, even instances of
    # the same class, and from ordinary local/global variables.
    def __init__(self,class_name):
        self.class_name = class_name
        self.scope_key = 'instance-{}-{}'.format(class_name,symbolTable.new_instance_id())
        symbolTable.table['variables'][self.scope_key] = {}

    def __str__(self):
        return '<{} instance>'.format(self.class_name)


def _fetch_instance(name):
    # Shared lookup used by every property/method operation: finds the
    # variable, makes sure it's actually holding an object (an Instance),
    # and reports a clear error otherwise instead of a raw Python crash.
    stored = symbolTable.fetch_variable(name)
    if not stored:
        Error.throwException('anwani',name)
        return None
    value = stored.evaluate()
    if not isinstance(value,Instance):
        Error.throwException('darasa',name)
        return None
    return value


class ConditionalExpression(Object):
    # `<true_value> kama <condition> sivyo <false_value>` used as a
    # value - a real inline conditional expression (Python's ternary,
    # `x if cond else y`), e.g.
    # `nafsi.jina = jina kama jina sawa na "Cookie" sivyo "Guest"`.
    # Built by try_parse_ternary() (see parse_expression_value()) - not
    # tied to any ExpressionParser operator symbol, since it isn't a
    # binary operator at all, just two branches and a condition.
    #
    # Evaluated lazily: only the branch actually taken is ever
    # evaluated, exactly like the kama/sivyo *statement* form already
    # behaves - so a false_value that would itself error out (e.g.
    # reading a property that's only set on the true branch) is never
    # touched unless the condition actually picks it.
    def __init__(self,true_value,condition,false_value):
        self.true_value = true_value
        self.condition = condition
        self.false_value = false_value

    def evaluate(self):
        if self.condition.evaluate():
            return self.true_value.evaluate()
        return self.false_value.evaluate()


class PropertyExpression(Object):
    # `obj.jina` used as a value - `x = mtu1.jina` or `chapa mtu1.jina`.
    def __init__(self,object_name,property_name):
        self.object_name = object_name
        self.property_name = property_name

    def evaluate(self):
        instance = _fetch_instance(self.object_name)
        if instance is None:
            return None
        properties = symbolTable.table['variables'][instance.scope_key]
        if self.property_name not in properties:
            # Reads the same way an undefined plain variable would -
            # this property was simply never set on this object.
            Error.throwException('anwani',self.property_name)
            return None
        return properties[self.property_name].evaluate()


class PropertyAssignmentStatement(Statement):
    # `obj.jina = <value>` - sets (or creates) a property directly on an
    # existing object. Used both for external assignment (`mtu1.jina =
    # "Amara"`) and, just as importantly, for `nafsi.jina = jina` inside
    # a method - 'nafsi' is nothing special here, just a local variable
    # that happens to hold the current instance.
    def __init__(self,object_name,property_name,value_expr):
        self.object_name = object_name
        self.property_name = property_name
        self.value_expr = value_expr

    def execute(self):
        instance = _fetch_instance(self.object_name)
        if instance is None:
            return
        value = self.value_expr.evaluate()
        if symbolTable.exit() != 0:
            return
        symbolTable.table['variables'][instance.scope_key][self.property_name] = Literal(value)


class MethodCallExpression(Object):
    # `obj.method(args)` used as a value - `x = mtu1.sema()` or
    # `chapa mtu1.sema()`. Resolves which class's method to run from the
    # object's own class (not from however the variable happens to be
    # named), then reuses FunctionCallStatement so argument binding,
    # nafsi-binding, and rudisha/return handling all work exactly the
    # same as a plain function call.
    def __init__(self,object_name,method_name,args):
        self.object_name = object_name
        self.method_name = method_name
        self.args = args

    def evaluate(self):
        instance = _fetch_instance(self.object_name)
        if instance is None:
            return None
        qualified_name = 'darasa-{}-{}'.format(instance.class_name,self.method_name)
        if qualified_name not in symbolTable.table['functions']:
            Error.throwException('kazi',self.method_name)
            return None
        call = FunctionCallStatement((qualified_name,self.args,instance))
        call.execute()
        return call.return_value


class MethodCallStatement(Statement):
    # `obj.method(args)` used as its own statement - any return value is
    # simply discarded.
    def __init__(self,object_name,method_name,args):
        self.expr = MethodCallExpression(object_name,method_name,args)

    def execute(self):
        self.expr.evaluate()


class ListLiteral(Object):
    # `[1, 2, 3]` - evaluates each element fresh every time (same as any
    # other expression) into a plain Python list, which is what actually
    # gets stored via a normal assignment. Elements are read the same way
    # function-call arguments are (fetch_express() splitting on commas),
    # so - like call arguments - each element needs to be a single value
    # (a literal or variable), not a compound expression with its own
    # operators.
    def __init__(self,elements):
        self.elements = elements

    def evaluate(self):
        return [e.evaluate() for e in self.elements]


class LengthExpression(Object):
    # `idadi orodha` - how many items are currently in a list.
    def __init__(self,list_name):
        self.list_name = list_name

    def evaluate(self):
        lst = _fetch_list(self.list_name)
        return len(lst) if lst is not None else 0


class IndexExpression(Object):
    # `orodha[i]` used as a value - `x = orodha[i]` or `chapa orodha[i]`.
    def __init__(self,list_name,index_expr):
        self.list_name = list_name
        self.index_expr = index_expr

    def evaluate(self):
        lst = _fetch_list(self.list_name)
        if lst is None:
            return None
        index = self.index_expr.evaluate()
        if symbolTable.exit() != 0:
            return None
        if not isinstance(index,int) or index < 0 or index >= len(lst):
            Error.throwException('fahirisi',self.list_name)
            return None
        return lst[index]


class IndexAssignmentStatement(Statement):
    # `orodha[i] = <value>` - mutates an existing element in place.
    def __init__(self,list_name,index_expr,value_expr):
        self.list_name = list_name
        self.index_expr = index_expr
        self.value_expr = value_expr

    def execute(self):
        lst = _fetch_list(self.list_name)
        if lst is None:
            return
        index = self.index_expr.evaluate()
        value = self.value_expr.evaluate()
        if symbolTable.exit() != 0:
            return
        if not isinstance(index,int) or index < 0 or index >= len(lst):
            Error.throwException('fahirisi',self.list_name)
            return
        lst[index] = value


class AppendStatement(Statement):
    # `weka <value> kwenye orodha` - "put <value> into orodha", adding it
    # to the end of the list.
    def __init__(self,list_name,value_expr):
        self.list_name = list_name
        self.value_expr = value_expr

    def execute(self):
        lst = _fetch_list(self.list_name)
        if lst is None:
            return
        value = self.value_expr.evaluate()
        if symbolTable.exit() != 0:
            return
        lst.append(value)


class RemoveStatement(Statement):
    # `ondoa <index> kutoka orodha` - "remove <index> from orodha",
    # discarding the item at that position and shifting the rest down,
    # same as Python's `del lst[i]`.
    def __init__(self,list_name,index_expr):
        self.list_name = list_name
        self.index_expr = index_expr

    def execute(self):
        lst = _fetch_list(self.list_name)
        if lst is None:
            return
        index = self.index_expr.evaluate()
        if symbolTable.exit() != 0:
            return
        if not isinstance(index,int) or index < 0 or index >= len(lst):
            Error.throwException('fahirisi',self.list_name)
            return
        del lst[index]


class FunctionDefinitionStatement(Statement):
    def __init__(self,arg):
        self.name = arg[0]
        self.params = arg[1]
        symbolTable.set_function(self.name)
        Log('created new function {}'.format(self.name),'Function Definition')

        #create new argument placeholders in the local variable scope
        #immediately at parse/definition time, not in execute() - the
        #definition itself may live outside kwanza (e.g. a helper
        #function defined before main) and so may never be "executed"
        #as a statement, but it must still be callable.
        for i in self.params:

            Var(('function-{}-{}'.format(self.name,i.name),'','local')).evaluate()

            Log("created new argument: {}".format(i),'Function Definition')

    def execute(self):
        # Parameter placeholders are set up in __init__ (see above).
        pass


class InputStatement(Statement):

    def __init__(self,arg):

        self.value = arg[0].evaluate()

        # arg[1] is the jaza destination. Almost always a plain variable
        # (`jaza "prompt:", jina`), in which case read_operand() casts it
        # to a Var with a `.name`. But read_operand() also runs
        # try_parse_property_access() first, so `jaza "...", nafsi.jina`
        # (or any `obj.member`) - a natural thing to write inside a
        # constructor - comes back as a PropertyExpression instead, which
        # has no `.name`. Keep the raw target here and branch on its
        # actual type in execute() rather than assuming .name exists.
        self.target = arg[1]


    def execute(self):

        # symbolTable.read_input() falls back to a plain terminal input()
        # prompt unless a host environment (e.g. the desktop Notepad) has
        # set symbolTable.input_handler to something else, like a GUI
        # dialog - see SymbolTable.read_input().
        raw = symbolTable.read_input(str(self.value))

        # Auto-detect plain integers (e.g. from a numeric prompt like age)
        # so the result can be used with comparisons/arithmetic in 'kama'
        # blocks; anything else is kept as text.
        token_type = 'integer' if raw.lstrip('-').isdigit() else 'string'

        var = Object(TokenObj(token_type,raw,0,0,0)).cast()
        value = Literal(var.evaluate())

        if isinstance(self.target,PropertyExpression):
            # Write straight onto the instance's own property table, the
            # same way PropertyAssignmentStatement does for a plain
            # `obj.jina = ...` - 'nafsi' inside a method is nothing
            # special, just a local variable holding the current
            # instance, same as everywhere else in the language.
            instance = _fetch_instance(self.target.object_name)
            if instance is None:
                return
            symbolTable.table['variables'][instance.scope_key][self.target.property_name] = value
        else:
            # Same call_flag-based scope check as huku's loop variable (see
            # ForStatement.execute()) - symbolTable.get_scope('var-scope') only
            # reflects parse-time bookkeeping, which has already unwound by
            # the time this runs.
            var_scope = 'local' if symbolTable.call_flag else 'global'
            symbolTable.write_variable(var_scope,self.target.name,value)
        
        

class IfStatement(Statement):
    def __init__(self,arg):
        self.true_name,self.condition = arg
        self.else_name = None
        symbolTable.set_function(self.true_name)
        Log('created new if-block {}'.format(self.true_name),'If Definition')

    def set_else(self,else_name):
        self.else_name = else_name

    def execute(self):
        if self.condition.evaluate():
            Log('condition true, executing if-block {}'.format(self.true_name),'If Execution')
            for i in symbolTable.table['functions'][self.true_name]:
                if symbolTable.exit() != 0 or symbolTable.is_returning():
                    break
                symbolTable.current_line = i.line
                symbolTable.current_column = i.column
                i.execute()
        elif self.else_name is not None:
            Log('condition false, executing sivyo-block {}'.format(self.else_name),'If Execution')
            for i in symbolTable.table['functions'][self.else_name]:
                if symbolTable.exit() != 0 or symbolTable.is_returning():
                    break
                symbolTable.current_line = i.line
                symbolTable.current_column = i.column
                i.execute()
        else:
            Log('condition false, no sivyo branch, skipping','If Execution')


class WhileStatement(Statement):
    # Safety valve: a runaway loop (e.g. forgetting to update the loop
    # variable) would otherwise run forever with no way to stop it. This
    # caps total iterations and fails gracefully instead.
    MAX_ITERATIONS = 100000

    def __init__(self,arg):
        self.name,self.condition = arg
        symbolTable.set_function(self.name)
        Log('created new while-loop {}'.format(self.name),'While Definition')

    def execute(self):
        iterations = 0
        while self.condition.evaluate():
            if symbolTable.exit() != 0 or symbolTable.is_returning():
                break
            iterations = iterations + 1
            if iterations > self.MAX_ITERATIONS:
                # self.line/self.column (not symbolTable.current_line/
                # current_column, which by now would just hold wherever
                # the body statement last ran) - the loop's own header
                # position is more useful here than wherever execution
                # happened to be when it gave up.
                Error.throwException('mzunguko',self.name,self.line,self.column)
                break
            for i in symbolTable.table['functions'][self.name]:
                if symbolTable.exit() != 0 or symbolTable.is_returning():
                    break
                symbolTable.current_line = i.line
                symbolTable.current_column = i.column
                i.execute()
            if symbolTable.is_returning():
                break


class ForStatement(Statement):
    # 'huku <var> kutoka <start> hadi <end>' - a counted loop, for when you
    # know how many times to repeat rather than watching a condition
    # (that's what wakati is for). The end bound is exclusive, matching
    # Python's range(): 'huku i kutoka 0 hadi 5' visits i = 0,1,2,3,4.
    # If the end is lower than the start, it counts down instead of
    # looping forever - 'huku i kutoka 5 hadi 0' visits i = 5,4,3,2,1.
    MAX_ITERATIONS = 100000

    def __init__(self,arg):
        self.name,self.var_name,self.start,self.end = arg
        symbolTable.set_function(self.name)
        Log('created new for-loop {}'.format(self.name),'For Definition')

    def execute(self):
        start_val = self.start.evaluate()
        end_val = self.end.evaluate()

        if symbolTable.exit() != 0:
            return

        # Whether this loop variable should live in 'local' or 'global'
        # storage depends on whether we're *currently executing* inside a
        # function/method call - not on symbolTable.get_scope('var-scope'),
        # which only reflects parse-time bookkeeping and, by the time
        # execute() runs (well after parsing has fully finished), has
        # already unwound back to its top-level default regardless of
        # where this huku loop actually lives.
        step = 1 if end_val >= start_val else -1
        current = start_val
        iterations = 0

        while (current < end_val) if step == 1 else (current > end_val):
            if symbolTable.exit() != 0 or symbolTable.is_returning():
                break
            iterations = iterations + 1
            if iterations > self.MAX_ITERATIONS:
                # self.line/self.column (not symbolTable.current_line/
                # current_column, which by now would just hold wherever
                # the body statement last ran) - the loop's own header
                # position is more useful here than wherever execution
                # happened to be when it gave up.
                Error.throwException('mzunguko',self.name,self.line,self.column)
                break

            # Same storage path as a normal assignment (Var mode 1) -
            # wrap the plain number in a Literal so later reads of the
            # loop variable evaluate back out to it correctly. Isolated
            # per-call the same way an ordinary local assignment is, so a
            # loop variable inside a function can't shadow a same-named
            # variable elsewhere in the script.
            var_scope = 'local' if symbolTable.call_flag else 'global'
            symbolTable.write_variable(var_scope,self.var_name,Literal(current))

            for i in symbolTable.table['functions'][self.name]:
                if symbolTable.exit() != 0 or symbolTable.is_returning():
                    break
                symbolTable.current_line = i.line
                symbolTable.current_column = i.column
                i.execute()

            if symbolTable.is_returning():
                break

            current = current + step


class ForEachStatement(Statement):
    # 'huku <var> kwenye <list>' - iterates <var> over each item already
    # in <list>, in order. Unlike the counted huku/wakati forms, there's
    # no runaway-loop risk here (it's bounded by however many items the
    # list has), so no MAX_ITERATIONS safety cap is needed. Iterates over
    # a snapshot taken at the start, so appending to the same list from
    # inside the loop body doesn't change how many passes this loop runs.
    def __init__(self,arg):
        self.name,self.var_name,self.list_name = arg
        symbolTable.set_function(self.name)
        Log('created new for-each loop {}'.format(self.name),'For-Each Definition')

    def execute(self):
        lst = _fetch_list(self.list_name)
        if lst is None:
            return

        for item in list(lst):
            if symbolTable.exit() != 0 or symbolTable.is_returning():
                break

            # See ForStatement.execute() - call_flag (not the stale
            # parse-time var-scope) is what tells us whether this loop is
            # currently running inside a function/method call.
            var_scope = 'local' if symbolTable.call_flag else 'global'
            symbolTable.write_variable(var_scope,self.var_name,Literal(item))

            for i in symbolTable.table['functions'][self.name]:
                if symbolTable.exit() != 0 or symbolTable.is_returning():
                    break
                symbolTable.current_line = i.line
                symbolTable.current_column = i.column
                i.execute()

            if symbolTable.is_returning():
                break


class EndBlockStatement(Statement):
    def __init__(self,value):
        self.value = value
        #pop back to whichever scope was active before this block opened
        symbolTable.pop_scope()


def format_value(value):
    # Python's default str()/format() on a list reprs each element (so
    # strings show up with quotes around them, e.g. "['Amara', 'Juma']"),
    # which doesn't match how chapa prints a plain string (no quotes).
    # Format lists element-by-element ourselves instead, recursively, so
    # a list of strings prints the same unquoted way a lone string would.
    if isinstance(value,list):
        return '[' + ', '.join(format_value(v) for v in value) + ']'
    return '{}'.format(value)


def describe_type(value):
    # Backs 'aina' ("kind/type") - a small teaching/debugging aid: what
    # kind of value does this expression currently hold? bool is checked
    # before int/float since Python's bool is itself a subclass of int
    # (isinstance(True, int) is True), so it would otherwise be
    # misreported as a number.
    if isinstance(value,Instance):
        return value.class_name
    if isinstance(value,bool):
        return 'boolean'
    if isinstance(value,(int,float)):
        return 'namba'
    if isinstance(value,str):
        return 'neno'
    if isinstance(value,list):
        return 'orodha'
    return 'haijulikani'


class TypeStatement(Statement):
    # 'aina <expr>' - prints what kind of value an expression holds, e.g.
    # 'namba' (number), 'neno' (text), 'boolean', 'orodha' (list), or the
    # class name itself for a darasa instance.
    def __init__(self,value):
        self.value = value

    def execute(self):
        value = self.value.evaluate()
        if symbolTable.exit() == 0:
            if console is not None:
                console.insert(tk.END,'{}\n'.format(describe_type(value)))
            else:
                print(describe_type(value))
            Log("{}".format(describe_type(value)),"Type Statement")


class PrintStatement(Statement):
    def __init__(self,value):
        self.value = value

    def execute(self):
        # Evaluate first, then gate on whether that evaluation itself
        # raised an error (e.g. an undefined variable, which sets the
        # exit flag) - not on the value's truthiness. The old
        # `if self.value.evaluate():` meant chapa silently printed
        # nothing at all for legitimate 0/false/"" values.
        value = self.value.evaluate()
        if symbolTable.exit() == 0:
            if console is not None:
                console.insert(tk.END,'{}\n'.format(format_value(value)))
            else:
                print(format_value(value))
            Log("{}".format(format_value(value)),"Print Statement")
        

class AssignmentStatement(Statement):
    def __init__(self,value):
        self.value = value


    def execute(self):
        self.value.evaluate()


class ReturnStatement(Statement):
    # 'rudisha' - stops the current function immediately (a bare rudisha
    # is a guard-clause style early exit) and optionally carries a value
    # back out. Doesn't unwind anything itself - it just records the
    # value and sets symbolTable's return flag; every enclosing kama/
    # wakati/huku loop checks that flag and breaks out on its own, all
    # the way up to FunctionCallStatement.execute(), which is what
    # actually absorbs it and hands the value back to the caller.
    def __init__(self,expr):
        self.expr = expr

    def execute(self):
        if symbolTable.exit() != 0:
            return
        value = self.expr.evaluate() if self.expr is not None else None
        if symbolTable.exit() != 0:
            return
        symbolTable.set_return(value)


'''

    def parse_next_expression(self):
        
        results = None
        
        expressions = [] 
        
        value = self.next_token().value if self.next_token().token_type != 'variable' else getattr(sys.modules['__main__'], self.value)
        
        
        
        while(self.get_token_by_index(self.token_position + 2).token_type == 'operator'):
            val_ = self.get_token_by_index(self.token_position + 2).value
            next_val = self.get_token_by_index(self.token_position + 3).value 
            
            if val_ == '+' :
                value = value + next_val if next_val != 'variable' else getattr(sys.modules['__main__'], next_val)
                self.token_position = self.token_position + 

'''