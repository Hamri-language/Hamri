import tkinter as tk
from tkinter import *
from tkinter.messagebox import *
from tkinter.filedialog import *
from tkinter.simpledialog import askstring
import webbrowser
from tkinter import ttk
import os


from LexicalParser import LexicalParser
from StatementParser import StatementParser
from SymbolTable import symbolTable
from Logger import Logs,LogKeys

# NOTE: Console.py's singleton `console` (previously imported here) is no
# longer used - StatementParser now takes the console widget directly as
# an argument to .parse(), instead of routing print/error output through
# a separate global. See __execute() below.

class CustomText(Text):
    def __init__(self, *args, **kwargs):
        """A text widget that reports on internal widget commands"""
        super().__init__(*args, **kwargs)

        # Create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        try:
            result = self.tk.call(cmd)
        except tk.TclError:
            # Benign Tcl-level errors happen here routinely - e.g. a
            # <<Paste>> triggers "delete sel.first sel.last" even when
            # nothing is selected, which Tcl reports as an error ("text
            # doesn't contain any characters tagged with sel") rather than
            # just a no-op. Uncaught, that exception propagates straight
            # out of Tk's mainloop and kills the whole application instead
            # of just skipping the no-op delete. Swallow it here and let
            # the rest of the command (e.g. the actual insert half of a
            # paste) proceed normally.
            return ""

        if command in ("insert", "delete", "replace"):
            self.event_generate("<<TextModified>>")

        # Every way the visible portion of this widget can change funnels
        # through here too, not just edits - "yview" is exactly what
        # scrolling (mouse wheel, Page Up/Down, dragging a scrollbar, an
        # arrow key that pushes the cursor past the visible area, ...)
        # actually calls under the hood, since it's the same underlying
        # Tcl widget command we renamed and took over above. The line-
        # number gutter needs to redraw on any of these - an edit can add
        # or remove lines just as much as a scroll can bring new ones
        # into view - so it listens for this broader event instead of
        # <<TextModified>>, which stays scoped to "the text itself
        # changed" for syntax highlighting's sake (re-tokenizing on every
        # scroll tick would be wasted work, and visibly slower on a long
        # script).
        if command in ("insert", "delete", "replace", "yview"):
            self.event_generate("<<TextViewChanged>>")

        return result


class TextLineNumbers(tk.Canvas):
    """A narrow strip drawn alongside a Text widget, showing a line
    number next to every visible line - the familiar "gutter" down the
    left edge of most code editors.

    A Canvas (rather than e.g. a second read-only Text widget) is the
    standard, lightweight way to do this in Tkinter: it draws only
    plain numbers, and Tk's own dlineinfo() (see redraw() below) already
    knows the exact pixel position of every currently-visible line, so
    the numbers always land in the right place without this class
    having to guess a fixed line height itself.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, highlightthickness=0, **kwargs)
        # Set via attach() right after construction, once the real code
        # editor Text widget it belongs to actually exists - kept as a
        # plain instance attribute rather than a constructor argument so
        # this class doesn't need to know Notepad's widget-creation order.
        self.text_widget = None
        # Overwritten by set_colors() below to match whichever editor
        # theme (light/dark) is active - this is just a safe fallback so
        # redraw() has *some* color even if set_colors() is never called.
        self._text_color = 'black'

    def attach(self, text_widget):
        """Point this gutter at the Text widget it should number."""
        self.text_widget = text_widget

    def set_colors(self, background, text_color):
        """Match the gutter's background/number color to the editor's
        current theme (see Notepad.__applyEditorTheme)."""
        self._text_color = text_color
        self.configure(bg=background)

    def redraw(self, *_event_args):
        """Erase and redraw every line number currently visible.

        *_event_args soaks up whatever Tkinter passes in when this is
        used directly as an event callback (an Event object) - redraw()
        never needs to look at it, it just always recomputes from
        scratch based on the text widget's current scroll position.
        """
        self.delete("all")

        if self.text_widget is None:
            return

        # "@0,0" asks the text widget "what character index is showing
        # at pixel position (0,0)?" - i.e. wherever the very first
        # visible line is right now, however far the user has scrolled.
        index = self.text_widget.index("@0,0")

        while True:
            # dlineinfo() returns None once `index` scrolls past the
            # last actually-visible display line (e.g. below the bottom
            # of the window) - the natural place for this loop to stop.
            dline_info = self.text_widget.dlineinfo(index)
            if dline_info is None:
                break

            # dlineinfo()'s 2nd element is the line's top-left y pixel
            # position within the text widget - exactly where this
            # number needs to be drawn to line up with it.
            y_position = dline_info[1]
            line_number = str(index).split('.')[0]
            self.create_text(
                2, y_position,
                anchor='nw',
                text=line_number,
                font=self.text_widget['font'],
                fill=self._text_color,
            )

            # Advance by one logical source line - not one *display*
            # line - so a long line that wraps onto several display rows
            # still only gets numbered once, at the top, the same way
            # every other code editor's gutter behaves.
            index = self.text_widget.index('{}+1line'.format(index))


class Notepad:
    def __init__(self, **kwargs):
        self.__root = Tk()
        self.__thisWidth = kwargs.get('width', 300)
        self.__thisHeight = kwargs.get('height', 300)
        self.__thisTitle = 'Hamri IDE'
        self.__thisDefaultDir = '/home/bytefrost/Documents/Hamri/Projects/'
        self.__thisFile = None
        self.__Tokens = None
        # Tracks which background the code editor (not the console, which
        # already has its own fixed dark look) is currently showing, so
        # toolbar button/View menu/syntax highlighting can all agree on
        # which palette to use. Starts light - matches the editor's
        # original unstyled (default Tk white) appearance, so existing
        # behavior is unchanged until someone actually switches it.
        self.__editorDarkMode = False

        self.__root.title(self.__thisTitle)
        self.__root.geometry(f"{self.__thisWidth}x{self.__thisHeight}")
        self.__root.resizable(1, 1)

        # Create the code frame
        self.__thisCodeFrame = ttk.Frame(self.__root)
        self.__thisCodeFrame.pack(fill='both', expand=1)

        # A visible in-window toolbar with a Run button - on macOS the Menu
        # bar below is drawn in the system menu bar at the top of the
        # screen (not inside the window itself), and a Tk app launched
        # from a terminal (rather than a real .app bundle) doesn't always
        # grab menu focus reliably. This button guarantees there's always
        # a way to run the script without depending on that.
        self.__thisToolbar = ttk.Frame(self.__thisCodeFrame)
        self.__thisToolbar.pack(side=TOP, fill='x')
        self.__thisRunButton = ttk.Button(self.__thisToolbar, text="Run ▶", command=self.__execute)
        self.__thisRunButton.pack(side=LEFT, padx=4, pady=4)
        self.__thisClearEditorButton = ttk.Button(self.__thisToolbar, text="Clear Editor", command=self.__clearEditor)
        self.__thisClearEditorButton.pack(side=LEFT, padx=4, pady=4)
        self.__thisClearConsoleButton = ttk.Button(self.__thisToolbar, text="Clear Console", command=self.__clearConsole)
        self.__thisClearConsoleButton.pack(side=LEFT, padx=4, pady=4)
        self.__thisThemeButton = ttk.Button(self.__thisToolbar, text="Dark Mode", command=self.__toggleEditorTheme)
        self.__thisThemeButton.pack(side=LEFT, padx=4, pady=4)

        # The code editor itself, plus its line-number gutter, side by
        # side in their own frame - keeping them together like this
        # means the status bar and console below can be packed against
        # the codeFrame without needing to know anything about the
        # gutter living next to the text area.
        self.__thisEditorFrame = ttk.Frame(self.__thisCodeFrame)
        self.__thisEditorFrame.pack(side=TOP, fill='both', expand=1)

        # Create the text area for code editing
        self.__thisTextArea = CustomText(self.__thisEditorFrame, font=("Courier", 12, "normal"))

        # The gutter needs to exist before it can be told which text
        # widget to number (attach(), right after), and packed to the
        # left of it so the numbers appear on the left edge of the
        # editor, matching the convention every other code editor uses.
        self.__thisLineNumbers = TextLineNumbers(self.__thisEditorFrame, width=40)
        self.__thisLineNumbers.attach(self.__thisTextArea)
        self.__thisLineNumbers.pack(side=LEFT, fill='y')

        self.__thisTextArea.pack(side=LEFT, fill='both', expand=1)

        # A thin status bar just below the editor, showing where the
        # text cursor currently is - updated by __updateCursorPosition,
        # bound further below.
        self.__thisStatusBar = ttk.Frame(self.__thisCodeFrame)
        self.__thisStatusBar.pack(side=TOP, fill='x')
        self.__thisPositionLabel = ttk.Label(self.__thisStatusBar, text="Line 1, Col 1", anchor='w')
        self.__thisPositionLabel.pack(side=LEFT, padx=6, pady=2)

        # Create the console for displaying output
        self.__thisConsole = CustomText(self.__thisCodeFrame, font=("Courier", 12, "normal"), height=18, bg="black", fg="white")
        self.__thisConsole.pack(side=TOP, fill='x')

        # Create the menu bar
        self.__thisMenuBar = Menu(self.__root)
        self.__root.config(menu=self.__thisMenuBar)

        # Create the File menu
        self.__thisFileMenu = Menu(self.__thisMenuBar, tearoff=0)
        self.__thisFileMenu.add_command(label="New", command=self.__newFile)
        self.__thisFileMenu.add_command(label="Open", command=self.__openFile)
        self.__thisFileMenu.add_command(label="Save", command=self.__saveFile)
        self.__thisFileMenu.add_command(label="Execute", command=self.__execute)
        self.__thisFileMenu.add_separator()
        self.__thisFileMenu.add_command(label="Clear Editor", command=self.__clearEditor)
        self.__thisFileMenu.add_command(label="Clear Console", command=self.__clearConsole)
        self.__thisFileMenu.add_separator()
        self.__thisFileMenu.add_command(label="Exit", command=self.__quitApplication)
        self.__thisMenuBar.add_cascade(label="File", menu=self.__thisFileMenu)

        # Create the Edit menu
        self.__thisEditMenu = Menu(self.__thisMenuBar, tearoff=0)
        self.__thisEditMenu.add_command(label="Cut", command=self.__cut)
        self.__thisEditMenu.add_command(label="Copy", command=self.__copy)
        self.__thisEditMenu.add_command(label="Paste", command=self.__paste)
        self.__thisMenuBar.add_cascade(label="Edit", menu=self.__thisEditMenu)

        # Create the View menu - also mirrored by the "Dark Mode" toolbar
        # button above, for the same reason the Run/Clear buttons exist:
        # on macOS this menu bar renders in the system menu bar, not the
        # window itself, and isn't always reliably reachable.
        self.__thisViewMenu = Menu(self.__thisMenuBar, tearoff=0)
        self.__thisViewMenu.add_command(label="Dark Mode", command=lambda: self.__applyEditorTheme(True))
        self.__thisViewMenu.add_command(label="Light Mode", command=lambda: self.__applyEditorTheme(False))
        self.__thisMenuBar.add_cascade(label="View", menu=self.__thisViewMenu)

        # Create the Help menu
        self.__thisHelpMenu = Menu(self.__thisMenuBar, tearoff=0)
        self.__thisHelpMenu.add_command(label="About Hamri IDE", command=self.__showAbout)
        self.__thisHelpMenu.add_command(label="Open Hamri Documentation", command=self.__openDocumentation)
        self.__thisMenuBar.add_cascade(label="Help", menu=self.__thisHelpMenu)

        # Bind events to the text area. add='+' on every binding past the
        # first one for the same event is required here - Tkinter's
        # .bind() *replaces* any existing callback for a given sequence
        # on a widget by default, so without it each of these would
        # silently discard whatever was bound right before it instead of
        # running alongside it.
        self.__thisTextArea.bind("<<TextModified>>", self.__generateTags)
        # The gutter redraws on <<TextViewChanged>> (see CustomText._proxy)
        # rather than <<TextModified>> - it needs to catch scrolling too,
        # not just edits, which <<TextModified>> deliberately doesn't cover.
        self.__thisTextArea.bind("<<TextViewChanged>>", self.__thisLineNumbers.redraw, add='+')
        self.__thisTextArea.bind("<KeyRelease>", self.__updateCursorPosition, add='+')
        self.__thisTextArea.bind("<ButtonRelease-1>", self.__updateCursorPosition, add='+')
        # Catches the editor being resized (e.g. the whole window being
        # resized) - dlineinfo()'s pixel positions shift when that
        # happens, even without any scrolling or editing taking place.
        self.__thisLineNumbers.bind("<Configure>", self.__thisLineNumbers.redraw)

        # Keyboard shortcut for running the script (Cmd+R on macOS,
        # Ctrl+R elsewhere) as a second fallback alongside the Run button,
        # independent of the File menu / menu bar entirely.
        self.__root.bind_all("<Command-r>", lambda event: self.__execute())
        self.__root.bind_all("<Control-r>", lambda event: self.__execute())

        # Give the gutter and status bar their correct starting
        # appearance/content immediately, rather than waiting for the
        # first keystroke or click to trigger it via the bindings above.
        self.__thisLineNumbers.set_colors('#f0f0f0', '#666666')
        self.__thisLineNumbers.redraw()
        self.__updateCursorPosition()

    # Maps each of the lexer's actual token type strings (see the `Tokens`
    # enum in LexicalParser.py - 'keyword', 'variable', 'operator',
    # 'divider', 'boolean', 'integer', 'string') to one of the four
    # highlight tags below. Previously this compared against
    # "Keyword"/"Identifier"/"Operator"/"Literal" - capitalized names that
    # don't match any of the lexer's real (lowercase) token types at all,
    # so no token was ever colored. 'divider' (brackets/parens/dot) is
    # deliberately left unmapped - punctuation, not worth its own color.
    _TOKEN_TAGS = {
        'keyword': 'Token.Keyword',
        'variable': 'Token.Identifier',
        'operator': 'Token.Operator',
        'boolean': 'Token.Literal',
        'integer': 'Token.Literal',
        'string': 'Token.Literal',
    }

    # Per-theme foreground colors for each highlight tag. Keyword/Operator/
    # Literal (blue/green/purple) stay readable on both a white and a dark
    # background as-is, but "Token.Identifier" was hardcoded to plain
    # black - invisible against a dark editor background - so it's the one
    # that actually needs to change between themes.
    _TOKEN_COLORS = {
        False: {  # light background
            'Token.Keyword': 'blue',
            'Token.Identifier': 'black',
            'Token.Operator': 'green',
            'Token.Literal': 'purple',
        },
        True: {  # dark background
            'Token.Keyword': '#569cd6',
            'Token.Identifier': '#f1f1f1',
            'Token.Operator': '#6a9955',
            'Token.Literal': '#c586c0',
        },
    }

    def __generateTags(self, event=None):
        """Generates tags for syntax highlighting"""
        # Remove previous highlighting (tag_remove clears the ranges but
        # keeps the tag's style configured below, rather than deleting
        # and recreating the tag on every keystroke).
        for tag in ("Token.Keyword", "Token.Identifier", "Token.Operator", "Token.Literal"):
            self.__thisTextArea.tag_remove(tag, "1.0", "end")

        colors = self._TOKEN_COLORS[self.__editorDarkMode]
        self.__thisTextArea.tag_configure("Token.Keyword", foreground=colors['Token.Keyword'], font=("Courier", 12, "bold"))
        self.__thisTextArea.tag_configure("Token.Identifier", foreground=colors['Token.Identifier'], font=("Courier", 12, "normal"))
        self.__thisTextArea.tag_configure("Token.Operator", foreground=colors['Token.Operator'], font=("Courier", 12, "normal"))
        self.__thisTextArea.tag_configure("Token.Literal", foreground=colors['Token.Literal'], font=("Courier", 12, "normal"))

        # Parse code and generate tokens. from_text=True is required here -
        # without it, LexicalParser treats its argument as a *file path* by
        # default (see main.py) rather than literal source text, which
        # would raise on every keystroke since this text isn't a real file.
        code = self.__thisTextArea.get("1.0", "end-1c")
        try:
            lexer = LexicalParser(code, from_text=True).parse()
        except Exception:
            # Mid-edit source (e.g. an unterminated string) shouldn't be
            # able to raise out of a text-modified event handler - just
            # skip highlighting for this keystroke and try again on the
            # next one.
            return
        self.__Tokens = lexer.token_list

        for token in self.__Tokens:
            tag = self._TOKEN_TAGS.get(token.token_type)
            if tag is None:
                continue
            # Tkinter Text indices are "line.column" strings, with lines
            # 1-indexed - token.line/token.start are plain 0-indexed
            # character offsets within the source (see TokenObj in
            # LexicalParser.py), which is a different scheme entirely and
            # can't be passed to tag_add() directly.
            start_index = "{}.{}".format(token.line + 1, token.start)
            end_index = "{}.{}".format(token.line + 1, token.start + token.size())
            self.__thisTextArea.tag_add(tag, start_index, end_index)

    def __newFile(self):
        """Create a new file"""
        self.__root.title("Untitled - Hamri IDE")
        self.__thisFile = None
        self.__thisTextArea.delete("1.0", "end")

    def __openFile(self):
        """Open an existing file"""
        self.__thisFile = askopenfilename(defaultextension=".txt", filetypes=[("All Files", "*.*"), ("Text Documents", "*.txt")])

        if self.__thisFile:
            self.__root.title(f"{os.path.basename(self.__thisFile)} - Hamri IDE")
            self.__thisTextArea.delete("1.0", "end")

            with open(self.__thisFile, "r") as file:
                self.__thisTextArea.insert("1.0", file.read())

    def __saveFile(self):
        """Save the current file"""
        if self.__thisFile:
            with open(self.__thisFile, "w") as file:
                file.write(self.__thisTextArea.get("1.0", "end-1c"))
        else:
            self.__saveFileAs()

    def __saveFileAs(self):
        """Save the current file with a new name"""
        self.__thisFile = asksaveasfilename(defaultextension=".txt", filetypes=[("All Files", "*.*"), ("Text Documents", "*.txt")])

        if self.__thisFile:
            with open(self.__thisFile, "w") as file:
                file.write(self.__thisTextArea.get("1.0", "end-1c"))
            self.__root.title(f"{os.path.basename(self.__thisFile)} - Hamri IDE")

    def __cut(self):
        """Cut the selected text"""
        self.__thisTextArea.event_generate("<<Cut>>")

    def __copy(self):
        """Copy the selected text"""
        self.__thisTextArea.event_generate("<<Copy>>")

    def __paste(self):
        """Paste the clipboard content"""
        self.__thisTextArea.event_generate("<<Paste>>")

    def __execute(self):
        """Execute the code and display output in the console"""
        # Clear any output left over from a previous run first, so the
        # console only ever shows this run's output rather than this
        # run's output appended after a stale previous one.
        self.__clearConsole()

        code = self.__thisTextArea.get("1.0", "end-1c")

        # Reset the interpreter's global state before each run, so a
        # previous Execute click's variables/classes/functions don't leak
        # into this one. reset() rebuilds SymbolTable via __init__, which
        # sets input_handler back to None - so it has to be (re)assigned
        # after reset(), not before.
        symbolTable.reset()
        symbolTable.input_handler = self.__askForInput

        # Perform lexical analysis (from_text=True - see __generateTags)
        lexer = LexicalParser(code, from_text=True).parse()
        tokens = lexer.token_list

        # Perform statement parsing, passing the console Text widget
        # straight in - StatementParser routes all chapa/error output to
        # whatever's passed here (or falls back to a bare print() if
        # nothing is), rather than through the old Console.py singleton.
        statements = StatementParser(tokens).parse(self.__thisConsole)

        # Execute the parsed statements
        result = statements.execute()

    def __askForInput(self, prompt):
        """GUI counterpart of jaza's terminal input() fallback.

        Wired in as symbolTable.input_handler (see __execute above) so a
        script's 'jaza' statement pops up an actual dialog box in this
        window instead of silently blocking on whatever terminal
        Notepad.py happened to be launched from - which is easy to miss
        entirely if the window doesn't obviously look "stuck".
        """
        result = askstring("Hamri - Input", prompt, parent=self.__root)
        # A cancelled/closed dialog returns None - jaza still needs a
        # string back (it decides for itself whether the text looks like
        # a number), so treat that the same as an empty response.
        return result if result is not None else ""

    def __updateCursorPosition(self, event=None):
        """Refresh the status bar with the text cursor's current line
        and column, e.g. after the user types or clicks somewhere new.

        Text widget indices come back as a "line.column" string, with
        the line already 1-indexed the way an editor shows it - but the
        column half is 0-indexed, so it needs its own +1 here to match
        (and to match the 1-indexed "Nafasi" position Errors.py quotes
        in a runtime error message, for the same underlying reason).
        """
        line, column = self.__thisTextArea.index(INSERT).split(".")
        self.__thisPositionLabel.config(text="Line {}, Col {}".format(line, int(column) + 1))

    def __clearEditor(self):
        """Clear all text out of the code editor"""
        self.__thisTextArea.delete("1.0", "end")

    def __clearConsole(self):
        """Clear all output out of the console pane"""
        self.__thisConsole.delete("1.0", "end")

    def __applyEditorTheme(self, dark):
        """Switch the code editor's background between light and dark.

        Scoped to the editor (and its line-number gutter) only - the
        console already has its own fixed black/white look (see
        __init__) and isn't affected here.
        """
        self.__editorDarkMode = dark
        if dark:
            bg, fg, insertbg, selectbg = '#1e1e1e', '#f1f1f1', '#f1f1f1', '#3d5a73'
            gutter_bg, gutter_fg = '#1e1e1e', '#6e7681'
        else:
            bg, fg, insertbg, selectbg = '#ffffff', '#000000', '#000000', '#c3d9ff'
            gutter_bg, gutter_fg = '#f0f0f0', '#666666'
        self.__thisTextArea.config(bg=bg, fg=fg, insertbackground=insertbg, selectbackground=selectbg)
        self.__thisThemeButton.config(text="Light Mode" if dark else "Dark Mode")
        self.__thisLineNumbers.set_colors(gutter_bg, gutter_fg)
        self.__thisLineNumbers.redraw()

        # Re-apply syntax highlighting immediately with the new theme's
        # colors (see _TOKEN_COLORS) rather than waiting for the next
        # keystroke to trigger __generateTags via <<TextModified>>.
        self.__generateTags()

    def __toggleEditorTheme(self):
        """Flip the editor background between light and dark."""
        self.__applyEditorTheme(not self.__editorDarkMode)

    def __quitApplication(self):
        """Quit the application"""
        self.__root.destroy()

    def __showAbout(self):
        """Display information about the application"""
        showinfo("Hamri IDE", "A simple IDE for the Hamri programming language.")

    def __openDocumentation(self):
        """Open the Hamri documentation in a web browser"""
        webbrowser.open("https://example.com/hamri-documentation")

    def run(self):
        """Run the application"""
        self.__root.mainloop()


# Create an instance of the Notepad class and run the application
notepad = Notepad(width=800, height=600)
notepad.run()
