import json, requests, os, sys, math
from string import punctuation

API = "https://preview.nferx.com/semantics/v1/get_literature_evidence?only_meta=1&"
COOKIE = {"csrftoken": "XBVPbvzt6gIC2pigF7CPSGaORvPZsqRGSZknmLNhOHNi6wy96t8uO6oSdgRdTTg3", "sessionid": "s55g3459bwoc40m3fy3g2lois8wr7tiz;"}

FRAGMENTS_TO_PROCESS = 50

def strip_leading_trailing_special_char(str):
    strip_counter = 0
    while True:
        old = str
        str = str.strip(punctuation)
        str = str.strip('“”') # strip left and right quotation marks
        strip_counter += 1
        if str == old or strip_counter == 20:
            break
    
    print(strip_counter)
    print(str)
    return str

def process_input_fragment(fragment):
    """
    Process input fragment before extracting words for
    query

    Remove \n, \t, leading and trailing whitespaces

    Parameters:
    fragment: input fragment

    Returns:
    string: processed fragment
    """
    fragment = fragment.strip()
    fragment = fragment.replace("\\n", "")
    fragment = fragment.replace("\\t", "")
    return fragment

def process(word_list):
    """
    Process word list before forming query

    Removes characters that are not alphanumeric in the
    words of list and returns words concatenated into a
    string with '_' as delimiter

    Parameters:
    word_list: list of words
    
    Returns:
    string: concatenated words after removing non -alphanum
    with '_' delimiter
    """
    result = ""
    for word in word_list:
        for char in word:
            if char.isalnum():
                result += char
        result += '_'
    result = result[:-1] # remove last underscore
    return result

def containsNonAlphaNum(word_list):
    """
    Does list of words contain any special characters?

    Parameters:
    word_list: list of words
    
    Returns:
    bool: whether any word in the list contains a special
    character
    """
    chars = ["-", "_", "."]
    allow_chars = set(chars)
    for word in word_list:
        for char in word:
            if not(char.isalnum()) and char not in allow_chars:
                return True
    return False

def main():
    # Extract fragments from a v3/get_relevant_docs response
    print("Reading sample fragments from relevant docs response.")
    with open("response.json", 'r') as f:
        data = json.load(f)
        fragments = []

        for doc in data["result"]["literature"]:
            for sentence in doc["sentences"]:
                fragments.append(sentence)

        print("Writing fragments to a file.")
        i = 0
        with open("fragments.txt", "w", encoding="utf-8") as file:
            for fragment in fragments:
                fragment = fragment.replace("\n", "\\n")
                file.write(fragment)
                file.write('\n')
                i += 1
                if i == FRAGMENTS_TO_PROCESS:
                    break

    # Get the first five non-space starting and ending words of each fragment
    print("Extracting middle few words from fragments after reading fragments file.")
    with open("queries.txt", 'w') as queries_file:
        with open("fragments.txt", 'r') as fragments_file:
            for fragment in fragments_file:
                fragment = process_input_fragment(fragment)

                fragment_tokens = fragment.split()
                number_of_words = len(fragment_tokens)
                query = ""

                # single disjunction query
                if number_of_words <= 5:
                    query = '_'.join(fragment_tokens)
                    # conjunction of two disjunctions
                elif number_of_words <= 20:
                    start = '_'.join(fragment_tokens[5:10])
                    end = '_'.join(fragment_tokens[-10:-5])
                    query = start + ';' + end
                else:
                    # positions to pick multigrams
                    half_length = number_of_words / 2
                    quarter_length = number_of_words / 4
                    three_querter_length = (3 * number_of_words) / 4

                    # conjunction of three disjunctions
                    start = strip_leading_trailing_special_char('_'.join(fragment_tokens[4:8]))
                    end = strip_leading_trailing_special_char('_'.join(fragment_tokens[-8:-4]))

                    middle_disjunction_words = strip_leading_trailing_special_char('_'.join(fragment_tokens[ math.trunc(half_length-2) : math.trunc(half_length+2)]))
                    left_disjunction_words = strip_leading_trailing_special_char('_'.join(fragment_tokens[math.trunc(quarter_length-2): math.trunc(quarter_length+2)]))
                    right_disjunction_words = strip_leading_trailing_special_char('_'.join(fragment_tokens[math.trunc(three_querter_length-2): math.trunc(three_querter_length+2)]))

                    print("start: " + start)
                    print("left:" + left_disjunction_words)
                    print("middle: " + middle_disjunction_words)
                    print("right: " + right_disjunction_words)
                    print("end: " + end)

                    query = (start if not(containsNonAlphaNum(start)) else '') + ";" + \
                        (left_disjunction_words if not(containsNonAlphaNum(left_disjunction_words)) else '') + ";" + \
                            (middle_disjunction_words if not(containsNonAlphaNum(middle_disjunction_words)) else '') + ";" + \
                                (right_disjunction_words if not(containsNonAlphaNum(right_disjunction_words)) else '') + ";" + \
                                    (end if not(containsNonAlphaNum(end)) else '')
                
                print("Number of words:" + str(number_of_words))
                print("Formed query: " + query)

                queries_file.write(query)
                queries_file.write('\n')

    # Hit get_literature_evidence with the given queries
    print("Hitting get_literature_evidence with given queries")

    with open("queries.txt", 'r') as queries_file:
        for query in queries_file:
            input_params = {'only_meta': '1', 'doc_token': query}
            res = requests.get(API, params=input_params, headers="", cookies=COOKIE).json()["result"]
            # with open("response_1.json", 'w') as response_file:
            #     json.dump(res, response_file)
            print(res["num_results"])



    sys.exit()
    # Get the documents containing the start_doc_tokens
    print("Hit get articles with doc tokens and store documents")
    for doc_token in start_doc_tokens:
        start_doc_token_documents = {}
        filename = doc_token + ".json"

        if os.path.isfile(filename):
            with open(filename, 'r', encoding="utf-8") as f:
                response = json.load(f)
        else:
            doc_token = doc_token.replace(" ", "%2D")
            url = API + "token=" + doc_token
            print("Firing API: " + url)
            api_response = requests.get(url, cookies=COOKIE)
            response = json.loads(api_response.text)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=4)
        
        doc_ids = set()
        for doc in response["result"]["literature"]:
            doc_ids.add(doc["id"])
            start_doc_token_documents[doc["id"]] = doc

    # Get the documents containing the end_doc_tokens and start_doc_tokens
    print("End")
    end_doc_token_documents = {}
    for doc_token in end_doc_tokens:
        filename = doc_token + ".json"

        if os.path.isfile(filename):
            with open(filename, 'r', encoding="utf-8") as f:
                response = json.load(f)
        else:
            url = API + "token=" + doc_token
            print("Firing API: " + url)
            api_response = requests.get(url, cookies=COOKIE)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=4)

        for doc in response["result"]["literature"]:
            # if start start_doc_tokens also present in document
            if doc["id"] in start_doc_token_documents:
                end_doc_token_documents[doc["id"]] = doc

if __name__ == "__main__":
    main()
    