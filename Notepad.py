import tkinter
import os
import webbrowser
from tkinter import *
from tkinter.messagebox import *
from tkinter.filedialog import *
import tkinter as tk
import re
from tkinter import ttk


import LexicalParser,StatementParser

# Ubuntu 20.0.1 sudo apt install python3.8-tk for tkinter module

class CustomText(Text):
    
    def __init__(self, *args, **kwargs):
        """A text widget that report on internal widget commands"""
        Text.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
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

    __root = Tk()
    # default window width and height
    __Tokens = None
    __thisWidth = 300
    __thisTitle = 'Hamri IDE'
    __thisDefaultDir = '/home/bytefrost/Documents/Hamri/Projects/'
    __thisCodeFrame = None
    __thisConsoleFrame = None
    __thisHeight = 300
    __thisTextArea = None
    __thisConsole = None
    __thisMenuBar = Menu(__root)
    __thisFileMenu = Menu(__thisMenuBar, tearoff=0)
    __thisEditMenu = Menu(__thisMenuBar, tearoff=0)
    __thisHelpMenu = Menu(__thisMenuBar, tearoff=0)
    # To add scrollbar
    __thisScrollBar = None
    __thisConsoleScrollBar = None
    __file = None

    def __init__(self,**kwargs):
        # Set icon
        try:
            self.__root.wm_iconbitmap("Notepad.ico")
        except:
            pass
        # Set window size (the default is 300x300)
        try:
            self.__thisWidth = kwargs['width']
        except KeyError:
            pass

        try:
            self.__thisHeight = kwargs['height']
        except KeyError:
            pass
        
        

        # Set the window text
        self.__root.title(self.__thisTitle)
        
        # Center the window
        screenWidth = self.__root.winfo_screenwidth()
        screenHeight = self.__root.winfo_screenheight()
        # For left-alling
        left = (screenWidth / 2) - (self.__thisWidth / 2)
        # For right-allign
        top = (screenHeight / 2) - (self.__thisHeight /2)
        # For top and bottom

        self.__root.geometry('%dx%d+%d+%d' % (self.__thisWidth,self.__thisHeight,left, top))
        # To make the textarea auto resizable
        
        self.__root.resizable(1,1)
        

        # Add controls (widget)
        
        self.__thisCodeFrame = ttk.Frame(self.__root)    
                 
        self.__thisCodeFrame.pack(fill='both',expand=1)
        
        self.__thisTextArea = CustomText(self.__thisCodeFrame,font=("Courier", 12, "normal"))
        
        self.__thisTextArea.pack(side=TOP,fill='both',expand=1)     
        
        self.__thisConsole = CustomText(self.__thisCodeFrame,font=("Courier", 12, "normal"),height=18,bg="black",fg="white")
        self.__thisScrollBar = Scrollbar(self.__thisTextArea)
        self.__thisConsole.pack(side=TOP,fill='x')
        
        
        # To open new file
        self.__thisFileMenu.add_command(label="New",
                                                command=self.__newFile)
        # To open a already existing file
        self.__thisFileMenu.add_command(label="Open",
                                                command=self.__openFile)
        # To save current file
        self.__thisFileMenu.add_command(label="Save",
                                                command=self.__saveFile)
        #To execute current script
        self.__thisFileMenu.add_command(label="Execute",command=self.__execute)
        
        # To create a line in the dialog
        self.__thisFileMenu.add_separator()
        self.__thisFileMenu.add_command(label="Exit",
                                                command=self.__quitApplication)
        self.__thisMenuBar.add_cascade(label="File",
                                               menu=self.__thisFileMenu)
        # To give a feature of cut
        self.__thisEditMenu.add_command(label="Cut",
                                                command=self.__cut)
        # to give a feature of copy
        self.__thisEditMenu.add_command(label="Copy",
                                                command=self.__copy)
        # To give a feature of paste
        self.__thisEditMenu.add_command(label="Paste",
                                                command=self.__paste)
        # To give a feature of editing
        self.__thisMenuBar.add_cascade(label="Edit",
                                               menu=self.__thisEditMenu)
        # To create a feature of description of the notepad
        self.__thisHelpMenu.add_command(label="View Help",
                                                command=self.__showAbout)
        self.__thisMenuBar.add_cascade(label="Help",
                                               menu=self.__thisHelpMenu)
        self.__root.config(menu=self.__thisMenuBar)
        #self.__thisScrollBar.pack(side=RIGHT,fill=Y)
        # Scrollbar will adjust automatically according to the content
        #self.__thisScrollBar.config(command=self.__thisTextArea.yview)
        #self.__thisTextArea.config(yscrollcommand=self.__thisScrollBar.set)
    def __quitApplication(self):
        self.__root.destroy()
        # exit()
    def __showAbout(self):
        showinfo("Notepad",view =webbrowser.open("https://www.bing.com/search?q=get+help+with+notepad+in+windows+10&filters=guid:%224466414-en-dia%22%20lang:%22en%22&form=T00032&ocid=HelpPane-BingIA"))
    def __openFile(self):
        self.__file = askopenfilename(initialdir=self.__thisDefaultDir,defaultextension=".ham",filetypes=[("Hamri script","*.ham"),("Text Documents","*.txt")])
        if self.__file == "":
            # no file to open
            self.__file = None
        else:
            # Try to open the file
            # set the window title
            self.__root.title(self.__thisTitle +' - '+os.path.basename(self.__file))
            self.__thisTextArea.delete(1.0,END)
            file = open(self.__file,"r")
            self.__Tokens = LexicalParser.LexicalParser(self.__file).parse()
            self.__thisTextArea.bind("<<TextModified>>",self.__generateTags)
            self.__thisTextArea.insert(1.0,file.read())
            file.close()
            
            
    def __generateTags(self,event):
        
        if type(self.__file) == str and self.__file != '':
            
            tags_dir = {"keyword":"blue"}
            for i in self.__Tokens.token_list:
                if i.token_type in tags_dir.keys():
                    
                    self.__thisTextArea.tag_add('{}-{}'.format(i.token_type,i.position()), "{}.{}".format(i.line,i.start), "{}.{}".format(i.line,i.len_))
                    self.__thisTextArea.tag_config('{}-{}'.format(i.token_type,i.position()), foreground=tags_dir[i.token_type],font=("Courier", 11, "bold"))


    def __newFile(self):
        self.__root.title("Untitled - Notepad")
        self.__file = None
        self.__thisTextArea.delete(1.0,END)
        
    def __execute(self):
        
        self.__thisConsole.delete(1.0,END)
        
        if self.__Tokens != None:
            self.__Tokens = LexicalParser.LexicalParser(self.__file).parse()
            statementParser = StatementParser.StatementParser(self.__Tokens.token_list).parse(self.__thisConsole)
            statementParser.execute()
            
            

    def __saveFile(self):

        if self.__file == None:
            # Save as new file
            self.__file = asksaveasfilename(initialfile='Untitled.txt',
                                                        defaultextension=".txt",
                                                                                        filetypes=[("All Files","*.*"),
                                                                                                   ("Text Documents","*.txt")])

            if self.__file == "":
                self.__file = None
            else:
                # Try to save the file
                file = open(self.__file,"Untitled")
                file.write(self.__thisTextArea.get(1.0,END))
                file.close()

                # Change the window title
                self.__root.title(os.path.basename(self.__file) + " - Notepad")

        else:
            file = open(self.__file,"w")
            file.write(self.__thisTextArea.get(1.0,END))
            file.close()

    def __cut(self):
        self.__thisTextArea.event_generate("<<Cut>>")

    def __copy(self):
        self.__thisTextArea.event_generate("<<Copy>>")

    def __paste(self):
        self.__thisTextArea.event_generate("<<Paste>>")

    def run(self):
        # Run main application
        self.__root.mainloop()
        

# Run main application
notepad = Notepad(width=700,height=600)
notepad.run()
