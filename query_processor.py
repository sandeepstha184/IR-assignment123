import json

def process_query(reverse_map, query):
    ## our heuristic: prioritize results that match the most
    ## keywords
    keywords = query.split()
    result_map = {}     # map of publication index to occurence count

    for keyword in keywords:
        # Case-insensitive
        if keyword.lower() not in reverse_map:
            continue
        print("FOR KEY WORD ", keyword)

        res_publications = reverse_map[keyword]
        print("publications are : ", res_publications)
        for pub in res_publications:
            if pub in result_map:
                result_map[pub] += 1
            else:
                result_map[pub] = 1
    
    # reverse the map
    final_map = {}
    for pub in result_map:
        count = result_map[pub]
        if count in final_map:
            final_map[count].append(pub)
        else:
            final_map[count] = [pub]


    ## send the results
    ## TODO: add alphabetical order or any other kind 
    result_pubs = []
    #return [*final_map[c] for c in sorted(final_map.keys(), reverse=True)]
    # in decreasing order of matches
    for count in sorted(final_map.keys(), reverse=True):
        result_pubs.extend(final_map[count])

    return keywords, result_pubs
       

    
      

