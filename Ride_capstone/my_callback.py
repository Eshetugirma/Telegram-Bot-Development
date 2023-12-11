# my_callback.py

class MyCallback:
    def __init__(self, name, id):
        self.name = name
        self.id = id

    def pack(self):
        return {"name": self.name, "id": self.id}

# Additional callback functions or classes can be added here if needed.
