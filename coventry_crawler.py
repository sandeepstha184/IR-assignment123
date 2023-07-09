#!/usr/bin/env python


from pathlib import Path
from datetime import datetime
from typing import List
import requests
import bs4
from dataclasses import dataclass, asdict
import json
import time
import nltk
from const import Person, Publication, INDEX_FILENAME
from query_processor import process_query

LIMIT_FACULTY = None        # just for testing None
OUTPUT_FILENAME = "faculty.json"
DATA_FILENAME = "data.json"         # real data: article title, pubdate, authors

PROFILES_URL = "https://pureportal.coventry.ac.uk/en/organisations/centre-for-intelligent-healthcare/persons/"
POLITENESS_FACTOR = 0.2



def crawl_names():
    persons = []

    resp = requests.get(PROFILES_URL)
    soup = bs4.BeautifulSoup(resp.text, "html.parser")

    results = soup.find_all("div", {"class": "result-container"})
    results_json = []

    ## assuming only one organization and one title at most
    for result in results:
        name_link = result.find("a", {"class": "person"})
        personal_url = name_link["href"]
        name = name_link.find("span").text

        orgs = result.find("ul", {"class": "organisations"})
        if orgs:
            organization = orgs.find("a", {"class": "organisation"})
            if organization:
                organization = organization.text
            title = orgs.find("span", {"class": "minor"})
            if title:
                title = title.text

            person = Person(name, personal_url, organization, title)
            persons.append(person)
            results_json.append(asdict(person))



    with open(OUTPUT_FILENAME, "w") as f:
        json.dump(results_json, f, indent=4)

        print(f"Dumped {len(results_json)} results")

    
    return persons


def search_publications(persons):
    pub_map = {}    # map publication slug to Publication object
    for i, person in enumerate(persons):
        print(f"Processing for {person.name}")
        if LIMIT_FACULTY and i == LIMIT_FACULTY:
            print(f"Stopping at faculty limit  {LIMIT_FACULTY}")
            break

        time.sleep(POLITENESS_FACTOR)

        url = f"{person.personal_url}/publications"
        resp  = requests.get(url)

        # skip if not HTTP 200
        if not resp.ok:
            print("Something went wrong with ", url)
            continue
        
        soup = bs4.BeautifulSoup(resp.text, "html.parser")

        # check num pages
        num_pages = 1
        nav = soup.find("nav", {"class": "pages"})
        if nav:
            last_link = nav.find("ul").find_all("li")[-1].find("a")
            ind = last_link["href"].rfind("=")
            num_pages = int(last_link["href"][ind+1:])
        

        publications = []

        def get_lastname(author_citation):
            ind = author_citation.find(",")
            return author_citation[:ind]


        def parse_page(page_num=1):
            nonlocal soup
            if page_num != 1:
                url = f"{person.personal_url}/publications/?page={page_num}"
                resp  = requests.get(url)
                soup = bs4.BeautifulSoup(resp.text, "html.parser")
            
            containers = soup.find_all("div", {"class": "result-container"})
            for cont in containers:
                # get title
                title = cont.css.select("div h3 a span")[0].text
                pub_url = cont.css.select("div h3 a")[0]["href"]
                ind = pub_url.rfind("/")
                slug = pub_url[ind+1:]  
                # check if slug exists:
                if slug in pub_map:
                    print(f"Crawler: duplicate publication {title}, author {person.name}")
                    # we already have other data, just add this new Coventry author, and skip
                    if i not in pub_map[slug].our_authors:
                        pub_map[slug].our_authors.append(i) 
                        # repeated person (Coventry) case
                        pub_map[slug].co_lastnames.extend( person.name.split() )
                        continue


                pub_date = None
                author_cont = cont.css.select("div")[0]
                coauthor_list = []
                coauthor_lastnames = []
                for child in author_cont.find_all("span", recursive=False):     # single level spans only
                    if child.has_attr("class") and  "date" in child["class"]:
                        pub_date = child.text
                        break
                    coauthor_list.append(child.text)
                    if "," in child.text:
                       coauthor_lastnames.append( get_lastname(child.text) )
                # our case 
                coauthor_lastnames.extend( person.name.split() )




                    

                pub_map[slug] = Publication(title, pub_url, slug, [i] , coauthor_list, coauthor_lastnames, pub_date)

        for page_no in range(1, num_pages+1):
            parse_page(page_no)

 
    return pub_map


def build_index(pub_map):
    reverse_map = {}
    for index, pub in enumerate(pub_map.values()):
        # get only nouns from the title, and co-author lastnames

        # Classification component
        li = [pub.title, *pub.co_lastnames]
        sentence = " ".join(li)
        tokens = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)
        nouns = [tag for (tag, type) in tagged if type[0] == "N"]

        ## use these nouns as keys to the index
        for noun in nouns:
            if noun.lower() in reverse_map:
                # add current publication to index
                reverse_map[noun.lower()].append(index)
            else:
                reverse_map[noun.lower()] = [index]


    return reverse_map
    


def load_persons():
    persons = []
    with open(OUTPUT_FILENAME, "r") as f:
        data = json.load(f)
        for p in data:
            persons.append(Person(**p))
        return persons


def load_publication_data():
    with open(DATA_FILENAME, "r") as f:
        pub_map = json.load(f)
        pub_map = {slug: Publication(**pub_json) for (slug, pub_json) in pub_map.items()}
        return pub_map


def load_reverse_map():
    with open(INDEX_FILENAME, "r") as f:
        return json.load(f)

def main():
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')


    if not Path(OUTPUT_FILENAME).exists():
        persons = crawl_names()
    else:
        persons = load_persons()
        print(f"{OUTPUT_FILENAME} exists, skipping name crawl for now")
    
    if not Path(DATA_FILENAME).exists():
        pub_map = search_publications(persons)
        pub_map = {slug: asdict(pub) for (slug, pub) in pub_map.items()}
        # write
        with open(DATA_FILENAME, "w") as f:
            json.dump(pub_map, f, indent=4)
    else:
        print(f"File {DATA_FILENAME} exists, skipping publication data download")
        pub_map = load_publication_data()

    
    if not Path(INDEX_FILENAME).exists():
        reverse_map = build_index(pub_map)
        # write
        with open(INDEX_FILENAME, "w") as f:
            json.dump(reverse_map, f, indent=4)
    else:
        print(f"File {INDEX_FILENAME} exists. Skipping buidling an index")
        reverse_map = load_reverse_map() 
    ## Query and results 
    query = input("Enter query: ") 
    pub_values = list(pub_map.values())
    if len(pub_values) == 0:
        print("No results found")
    else:
        print("\n\nResults: ")
        keywords, result_pubindices = process_query(reverse_map, query)
        for pub_index in result_pubindices:
            print(pub_values[pub_index].stringify_me(keywords, persons))


if __name__ == "__main__":
    main()


