import json, requests, os, sys, math, random, nltk
from nltk import PunktSentenceTokenizer as punkt
from string import punctuation

API = "https://preview.nferx.com/semantics/v1/get_literature_evidence?"
COOKIE = {"csrftoken": "XBVPbvzt6gIC2pigF7CPSGaORvPZsqRGSZknmLNhOHNi6wy96t8uO6oSdgRdTTg3", "sessionid": "s55g3459bwoc40m3fy3g2lois8wr7tiz;"}

FRAGMENTS_TO_PROCESS = 2
N_MULTIGRAMS = 4
N_WORDS_IN_MULTIGRAM = 4

TOTAL_TRIES_WITH_N_MULTIGRAMS = 5

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

def get_multigrams_from_fragment(fragment):
    multigrams = []
    start = 0
    end = 0
    n_multigram = 0
    # Form 4 multigrams
    while end < len(fragment) and start <= end and n_multigram < N_MULTIGRAMS:
        # Form one multigram
        n_word = 0
        while end < len(fragment) and start <= end and n_word < 4:
            restart = False
            # Move to next word end
            while end < len(fragment) and fragment[end] != ' ':
                # Move start of fragment to here if not alphanum
                if not fragment[end].isalnum():
                    # Move to end of word
                    while end < len(fragment) and fragment[end] != ' ':
                        end += 1
                    start = end + 1
                    end = start
                    restart = True
                    break
                else:
                    end += 1
            if restart:
                continue

            if fragment[end] == ' ':
                n_word += 1
                end += 1

        if n_word == 4:
            multigrams.append(fragment[start:end-1])
            start = end
            end = start

    filtered_multigrams = []
    for multigram in multigrams:
        if len(multigram.split()) > 3 and len(multigram.split()) < 6:
            filtered_multigrams.append(multigram)

    return filtered_multigrams

def hit_get_literature_evidence(multigrams, n_fragment):
    """
    Hit get literature evidence for a combination of the multigrams
    Save responses per fragment in responses directory

    Parameters:
    multigrams: list of multigrams extracted from the fragment
    multigrams don't contain any special characters

    Returns:
    """
    success = False
    n_try = 0

    # try TOTAL_TRIES_WITH_N_MULTIGRAMS times with N_MULTIGRAMS grams
    n_words_in_gram = N_MULTIGRAMS
    tried_five_gram = False
    tried_three_gram = False
    n_results = 0

    min_result_number = 10000

    while success == False and n_try < TOTAL_TRIES_WITH_N_MULTIGRAMS:
        n_words_in_gram = min(n_words_in_gram, len(multigrams))
        final_multigrams = ';'.join(random.sample(multigrams, n_words_in_gram))
        #print(final_multigrams)
        input_params = {'only_meta': '1', 'doc_token': final_multigrams}
        res = requests.get(API, params=input_params, headers="", cookies=COOKIE).json()["result"]
        
        response_filename_fragment = "responses/fragment" + str(n_fragment) + ".json"
        n_results = res["num_results"]

        # Gather doc ids
        doc_ids = []
        for document in res["literature"]:
            doc_ids.append(document["id"])
        doc_ids = ','.join(map(str, doc_ids))

        print(n_results)
        if n_results > 0 and n_results < 10:
            success = True

        # Save the result which contains the minimum number of documents, with only_meta as 0
        if min_result_number > n_results:
            with open(response_filename_fragment, 'w', encoding='utf8') as temp:

                # Get fragments only if a lot of results are present
                if n_results > 10:
                        input_params = {'only_meta': '0', 'doc_ids': doc_ids, 'token': final_multigrams}
                else:
                        input_params = {'only_meta': '0', 'doc_token': final_multigrams, 'doc_ids': doc_ids}

                response = requests.get(API, params=input_params, headers="", cookies=COOKIE).json()
                json.dump(response, temp, ensure_ascii=False)
                min_result_number = n_results
        
        n_try += 1

        # if too many results in query, try 5 grams
        if success == False and n_results > 10 and n_try == TOTAL_TRIES_WITH_N_MULTIGRAMS and tried_five_gram == False:
            n_try = 0
            n_words_in_gram = N_MULTIGRAMS + 1
            tried_five_gram = True
            continue

        # if zero results in query, try 3 grams
        if success == False and n_results == 0 and n_try == TOTAL_TRIES_WITH_N_MULTIGRAMS and tried_three_gram == False:
            n_try = 0
            n_words_in_gram = N_MULTIGRAMS - 1
            tried_three_gram = True
            continue
    
    if success == False:
        if n_results > 10:
            print("More than 10 results found for fragment")
        elif n_results < 0:
            print("No results found for fragment")

def extract_sentences(n_fragment):
    """
    Extract sentences given a fragment number after loading file
    """
    response_filename_fragment = "responses/fragment" + str(n_fragment) + ".json"

    # Get the fragment to match
    fragment = ""
    with open("fragments.txt", 'r') as fragment_file:
        for i, line in enumerate(fragment_file):
            if i == n_fragment:
                fragment = line.strip('\n\r')

    
    # Match with document
    with open(response_filename_fragment, 'r') as response_file:
        response = json.load(response_file)

        for document in response["result"]["literature"]:
            loc = document["sentences"][0].find(fragment)
            if loc != -1:
                full_text = document["sentences"][0]

                #reverse and forward search full stop (frag start = loc, frag end = loc + fragment length)
                #sentences = nltk.sent_tokenize(full_text)

                custom_sent_tokenizer = punkt(full_text)
                sent_end_pos = []
                for _, sent_stop in custom_sent_tokenizer.span_tokenize(full_text):
                    sent_end_pos.append(sent_stop)

                sentence_end_pos = document["sentences"][0].find('.', loc + len(fragment))



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
    with open("sample_response.json", 'r') as f:
        data = json.load(f)
        fragments = []

        for doc in data["result"]["literature"]:
            with open("fragments.txt", 'r') as fragments_file:
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
            n_fragment = 0
            for fragment in fragments_file:
                print("Fragment: #", n_fragment)
                multigrams = get_multigrams_from_fragment(fragment)
                hit_get_literature_evidence(multigrams, n_fragment)
                extract_sentences(n_fragment)
                n_fragment += 1
                continue
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
    