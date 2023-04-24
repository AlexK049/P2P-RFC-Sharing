import random
import string
from datetime import datetime

class RFC:
    def __init__(self, rfc_number, title, last_modified, content_length, content_type, content):
        self.rfc_number = rfc_number
        self.title = title
        self.last_modified = last_modified
        self.content_length = content_length
        self.content_type = content_type
        self.content = content

    @classmethod
    def from_number_and_title(cls, rfc_number: str, title: str):
        rfc = RFC.generate_random_rfc()
        rfc.rfc_number = rfc_number
        rfc.title = title
        return rfc

    @staticmethod
    def generate_random_rfc():
        #generate random data for the RFC object
        rfc_number = "RFC " + str(random.randint(100, 999))
        rfc_title = "Random Title " + str(random.randint(1, 1000000))
        last_modified = datetime.fromtimestamp(random.randint(0, 1000000000)).strftime("%a, %d %b %Y %H:%M:%S GMT")
        content_length = random.randint(100, 1000)
        content_type = random.choice(["text/plain", "application/pdf", "image/jpeg"])
        content = ''.join(random.choices(string.ascii_uppercase + string.digits, k=content_length))

        #create and return an RFC object with the random data
        return RFC(rfc_number, rfc_title, last_modified, content_length, content_type, content)
    
    def __str__(self) -> str:
        return "RFC-Number: {}\nRFC-Title: {}\nLast-Modified: {}\nContent-Length: {}\nContent-Type: {}\n\n{}\n".format(self.rfc_number, self.title, self.last_modified, self.content_length, self.content_type, self.content)