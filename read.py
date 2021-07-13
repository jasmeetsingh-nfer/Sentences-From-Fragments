import json, requests, os, sys, math

API = "https://preview.nferx.com/semantics/v1/get_literature_evidence?only_meta=1&"
COOKIE = {"csrftoken": "XBVPbvzt6gIC2pigF7CPSGaORvPZsqRGSZknmLNhOHNi6wy96t8uO6oSdgRdTTg3", "sessionid": "s55g3459bwoc40m3fy3g2lois8wr7tiz;"}

FRAGMENTS_TO_PROCESS = 1
WORDS_IN_CONJUNCTION = 4

def process_input_fragment(fragment):
    """
    Process input fragment before extracting words for
    query

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
    for word in word_list:
        for char in word:
            if not(char.isalnum()):
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
    with open("fragments.txt", 'r') as f:
        n_fragment = 0
        for fragment in f:
            fragment = process_input_fragment(fragment)

            # print(fragment)

            splitted_line = fragment.split()
            number_of_words = len(splitted_line)
            query = ""

            # single disjunction query
            if number_of_words <= 5:
                query = '_'.join(splitted_line)
                # conjunction of two disjunctions
            elif number_of_words <= 20:
                start = '_'.join(splitted_line[5:10])
                end = '_'.join(splitted_line[-10:-5])
                query = start + '%3B' + end
            else:
                # positions to pick multigrams
                half_length = number_of_words / 2
                quarter_length = number_of_words / 4
                three_querter_length = (3 * number_of_words) / 4

                # conjunction of three disjunctions
                start = splitted_line[5:7]
                end = splitted_line[-7:-5]

                middle_disjunction_words = splitted_line[ math.trunc(half_length-1) : math.trunc(half_length+1)]   
                left_disjunction_words = splitted_line[math.trunc(quarter_length-1): math.trunc(quarter_length+1)]
                right_disjunction_words = splitted_line[math.trunc(three_querter_length-1): math.trunc(three_querter_length+1)]

                print("start: ")
                print(start)
                print("left:")
                print(left_disjunction_words)
                print("middle")
                print(middle_disjunction_words)
                print("right")
                print(right_disjunction_words)
                print("end")
                print(end)

                query = (start if not(containsNonAlphaNum(start)) else '') + "%3B" + \
                     (left_disjunction_words if not(containsNonAlphaNum(left_disjunction_words)) else '') + "%3B" + \
                         (middle_disjunction_words if not(containsNonAlphaNum(middle_disjunction_words)) else '') + "%3B" + \
                             (right_disjunction_words if not(containsNonAlphaNum(right_disjunction_words)) else '') + "%3B" + \
                                 (end if not(containsNonAlphaNum(end)) else '')
            
            print("Number of words:" + str(number_of_words))
            print("Formed query: " + query)

            # # Hit get_literature_evidence
            # params = "&only_meta=1"
            # url = API + "token=" + query + params
            # print("Firing API: " + url)
            # api_response = requests.get(url, cookies=COOKIE)
            # json_response = json.loads(api_response.text)

            # print(json_response)

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