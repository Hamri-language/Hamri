class Queue:
    #our queue class initializer
    def __init__(self):
        self.items = []

    #add item to queue
    def enqueue(self, item):
        self.items.append(item)

    #remove item from our queue
    def dequeue(self):
        if self.is_empty():
            return None
        return self.items.pop(0)
    
    #check whether the queue is empty
    def is_empty(self):
        return len(self.items) == 0
    
    #check the size of our queue
    def size(self):
        return len(self.items)

    #check the item at the front of our queue
    def peek(self):
        if self.is_empty():
            return None
        return self.items[0]
    

queue = Queue()