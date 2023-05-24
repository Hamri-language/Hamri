class Stack:
    def __init__(self):
        self.stack = []  # Initialize an empty list to represent the stack

    def push(self, item):
        self.stack.append(item)  # Add an item to the top of the stack

    def pop(self):
        if not self.is_empty():
            return self.stack.pop()  # Remove and return the top item from the stack
        else:
            raise IndexError("Stack is empty")  # Raise an exception if the stack is empty

    def peek(self):
        if not self.is_empty():
            return self.stack[-1]  # Return the top item from the stack without removing it
        else:
            raise IndexError("Stack is empty")  # Raise an exception if the stack is empty

    def is_empty(self):
        return len(self.stack) == 0  # Check if the stack is empty

    def size(self):
        return len(self.stack)  # Return the size (number of items) of the stack



stack = Stack()
