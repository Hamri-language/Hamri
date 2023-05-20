import tkinter as tk
from tkinter import *
from tkinter.messagebox import *
from tkinter.filedialog import *
import webbrowser
from tkinter import ttk
import os


from LexicalParser import LexicalParser
from StatementParser import StatementParser
from Console import console
from Logger import Logs,LogKeys

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
        result = self.tk.call(cmd)

        if command in ("insert", "delete", "replace"):
            self.event_generate("<<TextModified>>")

        return result


class Notepad:
    def __init__(self, **kwargs):
        self.__root = Tk()
        self.__thisWidth = kwargs.get('width', 300)
        self.__thisHeight = kwargs.get('height', 300)
        self.__thisTitle = 'Hamri IDE'
        self.__thisDefaultDir = '/home/bytefrost/Documents/Hamri/Projects/'
        self.__thisFile = None
        self.__Tokens = None

        self.__root.title(self.__thisTitle)
        self.__root.geometry(f"{self.__thisWidth}x{self.__thisHeight}")
        self.__root.resizable(1, 1)

        # Create the code frame
        self.__thisCodeFrame = ttk.Frame(self.__root)
        self.__thisCodeFrame.pack(fill='both', expand=1)

        # Create the text area for code editing
        self.__thisTextArea = CustomText(self.__thisCodeFrame, font=("Courier", 12, "normal"))
        self.__thisTextArea.pack(side=TOP, fill='both', expand=1)

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
        self.__thisFileMenu.add_command(label="Exit", command=self.__quitApplication)
        self.__thisMenuBar.add_cascade(label="File", menu=self.__thisFileMenu)

        # Create the Edit menu
        self.__thisEditMenu = Menu(self.__thisMenuBar, tearoff=0)
        self.__thisEditMenu.add_command(label="Cut", command=self.__cut)
        self.__thisEditMenu.add_command(label="Copy", command=self.__copy)
        self.__thisEditMenu.add_command(label="Paste", command=self.__paste)
        self.__thisMenuBar.add_cascade(label="Edit", menu=self.__thisEditMenu)

        # Create the Help menu
        self.__thisHelpMenu = Menu(self.__thisMenuBar, tearoff=0)
        self.__thisHelpMenu.add_command(label="About Hamri IDE", command=self.__showAbout)
        self.__thisHelpMenu.add_command(label="Open Hamri Documentation", command=self.__openDocumentation)
        self.__thisMenuBar.add_cascade(label="Help", menu=self.__thisHelpMenu)

        # Bind events to the text area
        self.__thisTextArea.bind("<<TextModified>>", self.__generateTags)

    def __generateTags(self, event=None):
        """Generates tags for syntax highlighting"""
        # Clear existing tags
        self.__thisTextArea.tag_delete("Token.Keyword")
        self.__thisTextArea.tag_delete("Token.Identifier")
        self.__thisTextArea.tag_delete("Token.Operator")
        self.__thisTextArea.tag_delete("Token.Literal")

        # Parse code and generate tokens
        code = self.__thisTextArea.get("1.0", "end-1c")
        lexer = LexicalParser(code).parse()
        self.__Tokens = lexer.token_list
        

        # Configure tags for different token types
        for token in self.__Tokens:
            if token.type == "Keyword":
                self.__thisTextArea.tag_add("Token.Keyword", token.start, token.end)
                self.__thisTextArea.tag_configure("Token.Keyword", foreground="blue", font=("Courier", 12, "bold"))
            elif token.type == "Identifier":
                self.__thisTextArea.tag_add("Token.Identifier", token.start, token.end)
                self.__thisTextArea.tag_configure("Token.Identifier", foreground="black", font=("Courier", 12, "normal"))
            elif token.type == "Operator":
                self.__thisTextArea.tag_add("Token.Operator", token.start, token.end)
                self.__thisTextArea.tag_configure("Token.Operator", foreground="green", font=("Courier", 12, "normal"))
            elif token.type == "Literal":
                self.__thisTextArea.tag_add("Token.Literal", token.start, token.end)
                self.__thisTextArea.tag_configure("Token.Literal", foreground="purple", font=("Courier", 12, "normal"))

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
        code = self.__thisTextArea.get("1.0", "end-1c")

        # Perform lexical analysis
        lexer = LexicalParser(code).parse()
        tokens = lexer.token_list

        # Perform statement parsing
        statements = StatementParser(tokens).parse()
        
        #pass our console object to the runtime sequence and clear it
        
        console.use_console(self.__thisConsole)

        # Execute the statements and capture the output
        
        result = statements.execute()

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
