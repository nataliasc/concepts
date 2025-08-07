import marimo

__generated_with = "0.9.11"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def __():
    import os
    import requests
    from dotenv import load_dotenv
    import numpy as np
    import pandas as pd
    pd.options.mode.chained_assignment = None
    return load_dotenv, np, os, pd, requests


@app.cell(hide_code=True)
def __():
    # handling a single work: make more readable dict


    # handling inverse abstract
    def convert_abstract(inv_abs):

        if inv_abs:
            assert isinstance(inv_abs, dict)

            idxs = []
            for idx in inv_abs.values():
                idxs += idx
            n_words = max(idxs)

            wordlist = [''] * (n_words + 1)
            for word in inv_abs.keys():
                idx = inv_abs[word]
                for i in idx:
                    wordlist[i] = word

            abstract = ' '.join(wordlist)

        else:
            abstract = None

        return abstract



    # get journal name as a string
    def get_journal(work):
        return work['primary_location']['source']['display_name']

    # get authors of a work as a single string
    def get_authors(work):
        auths = []
        for auth in work['authorships']:
            auths += [auth['author']['display_name']]
        return '; '.join(auths)

    # get author institutions of a work as a single string
    def get_institutions(work):
        insts = []
        for auth in work['authorships']:
            for inst in auth['institutions']:
                insts += [inst['display_name'] + ', '
                         + inst['country_code']]
        return '; '.join(insts)

    # get keywords of a work as a single string
    def get_keywords(work):
        kws = []
        for kw in work['keywords']:
            kws += [kw['display_name']]
        return '; '.join(kws)

    # get topics of a work as a single string
    def get_topics(work):
        tps = []
        for tp in work['topics']:
            tps += [tp['display_name'] + ' - '
                    + tp['subfield']['display_name'] + ' - '
                    + tp['field']['display_name'] + ' - '
                    + tp['domain']['display_name']]
        return '; '.join(tps)

    # get concepts of a work as a single string
    def get_concepts(work):
        cons = []
        for con in work['topics']:
            cons += [con['display_name']]
        return '; '.join(cons)

    # get abstract of a work as a string
    def get_abstract(work):
        return convert_abstract(work['abstract_inverted_index'])



    # convert a single work item (dict) to a dict with readable and relevant information
    def make_readable(work):
        readable = dict()
        readable['doi'] = work['doi']
        readable['title'] = work['title']
        readable['year'] = work['publication_year']
        readable['authors'] = get_authors(work)
        readable['journal'] = get_journal(work)
        readable['abstract'] = get_abstract(work)
        readable['alex_keywords'] = get_keywords(work)
        readable['institutions'] = get_institutions(work)
        readable['alex_url'] = work['id']
        readable['alex_topics'] = get_topics(work)
        readable['alex_concepts'] = get_concepts(work)
        readable['cited_by_count'] = work['cited_by_count']
        return readable
    return (
        convert_abstract,
        get_abstract,
        get_authors,
        get_concepts,
        get_institutions,
        get_journal,
        get_keywords,
        get_topics,
        make_readable,
    )


@app.cell(hide_code=True)
def __(requests):
    # def get_journals(names)

    # load_dotenv("../.env")
    def get_journals(names):
        # To test: https://api.openalex.org/sources?search=cognition
        # When searching sources: the fields searched are
        # `display_name`, `alternate_titles`, and `abbreviated_title`.
        # https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/search-entities

        sources = list()
        journal_names = ' OR '.join(f'"{j}"' for j in names)
        response = requests.get(
            f"https://api.openalex.org/sources?search={journal_names}&per-page=200",
            # per-page parameter must be between 1 and 200
            # headers={"mailto": os.getenv("OPENALEX_EMAIL")},  # use OpenAlex polite pool
        ).json()
        n_results = int(response['meta']['count'])

        sources += response["results"]

        if n_results > 200:
            for i in range(2, n_results // 200 + 1):
                subsequent_response = requests.get(
            f"https://api.openalex.org/sources?search={journal_names}&page={i}&per-page=200",
            # headers={"mailto": os.getenv("OPENALEX_EMAIL")},
            ).json()
            sources += subsequent_response["results"]


        return n_results, sources
    return (get_journals,)


@app.cell(hide_code=True)
def __(make_readable, requests):
    def get_openalex_sample(keywords, issns):
        # To test: https://api.openalex.org/works?filter=locations.source.issn:0010-0277&search=categorization&per-page=200

        works = list()
        keywords = ' OR '.join(f'"{k}"' for k in keywords)
        response = requests.get(
            f"https://api.openalex.org/works?filter=locations.source.issn:{'|'.join(issns)},title_and_abstract.search:{keywords}&per-page=200&cursor=*",
            # per-page parameter must be between 1 and 200
            # headers={"mailto": os.getenv("OPENALEX_EMAIL")},  # use OpenAlex polite pool
        ).json()
        try:
            n_results = int(response['meta']['count'])
        except KeyError:
            print(response)
        try:
            next_cursor = response['meta']['next_cursor']
        except KeyError:
            print(response)

        works += response["results"]


        if n_results > 200:
            while next_cursor:
                subsequent_response = requests.get(
            f"https://api.openalex.org/works?filter=locations.source.issn:{'|'.join(issns)},title_and_abstract.search:{keywords}&per-page=200&cursor={next_cursor}",
            # headers={"mailto": os.getenv("OPENALEX_EMAIL")},
            ).json()
                try:
                    next_cursor = subsequent_response["meta"]["next_cursor"]
                except KeyError:
                    print(subsequent_response["message"])
                works += subsequent_response["results"]

        # make readable
        readable_list = []
        for work in works:
            readable_list += [make_readable(work)]

        return n_results, works, readable_list
    return (get_openalex_sample,)


@app.cell
def __(get_journals, pd):
    journals = ["Cognitive Science",
                "Cognitive Sciences",
                "Cognition",
                "Journal of Experimental Psychology",
                "Journal of Mathematical Psychology",
                "American Psychologist",
                "Psychological review",
                "Cognitive Psychology"]

    n, journal_data = get_journals(journals)

    df = pd.DataFrame(journal_data)
    issns = [issn for issn in df.issn_l if issn != None]
    print(len(issns))
    return df, issns, journal_data, journals, n


@app.cell
def __(get_openalex_sample, issns, pd):
    search_terms = ["category learning"]  # structure learning, category formation, category induction


    _n, openalex_data, readable_data = get_openalex_sample(search_terms, issns[:100])

    _, _openalex_data, _readable_data = get_openalex_sample(search_terms, issns[100:])
    openalex_data += _openalex_data
    readable_data += _readable_data

    oa_df = pd.DataFrame(readable_data)
    oa_df.insert(1, 'flag_duplicant', oa_df.duplicated(subset='title', keep='first'))
    # dois = oa_df.doi.tolist()
    print(f"Results:......{len(oa_df)}")
    oa_df.head(10)
    return oa_df, openalex_data, readable_data, search_terms


@app.cell
def __(oa_df, search_terms):
    fn = '_'.join(search_terms) + '.csv'
    oa_df.to_csv(fn, encoding='utf-8')
    return (fn,)


if __name__ == "__main__":
    app.run()