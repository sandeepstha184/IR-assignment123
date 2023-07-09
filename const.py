from dataclasses import dataclass, asdict
WARNING = '\033[93m'
ENDC = '\033[0m'

INDEX_FILENAME = "index.json"

@dataclass
class Person:
    name: str
    personal_url: str
    org: str
    title: str

    def __str__(self):
        return f"<{self.name}, {self.title} at {self.org}>"

@dataclass
class Publication:
    title: str
    url: str
    slug: str                   # last part of the publication's url. Guaranteed to be unique, right?
    our_authors: list       # list of indexes into the list of persons (order in OUTPUT_FILENAME)
    co_authors: list
    co_lastnames: list     # only last names; for indexing
    pub_date: str       #datetime
    # TODO: add genre
    

    def stringify_me(self, keywords, persons):
        urls = [person.personal_url for person in persons]
        stri = ''
        for word in self.title.split():
            if word.lower() in keywords:
                stri += WARNING + word + ENDC + " "
                continue

            # else, just add
            stri += word + " "

        return stri[:-1] 
    



        return f"{self.title}\n"


