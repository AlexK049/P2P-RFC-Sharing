#this is just for easy of initializing objects in a way reminiscent of javascript
class JSObject:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __str__(self):
        return str(self.__dict__)