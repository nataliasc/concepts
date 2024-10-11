import marimo

__generated_with = "0.6.22"
app = marimo.App(width="medium")


@app.cell
def __(load_dotenv, os, pd, requests):
    load_dotenv("../.env")

    # get relevant journals data from OpenAlex
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
            headers={"mailto": os.getenv("OPENALEX_EMAIL")},  # use OpenAlex polite pool
        ).json()
        n_results = int(response['meta']['count'])

        sources += response["results"]

        if n_results > 200:
            for i in range(2, n_results // 200 + 1):
                subsequent_response = requests.get(
            f"https://api.openalex.org/sources?search={journal_names}&page={i}&per-page=200",
            headers={"mailto": os.getenv("OPENALEX_EMAIL")},
            ).json()
            sources += subsequent_response["results"]


        return n_results, sources

    journals = ["Cognitive Science", "Cognitive Sciences",
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

    # get data filtering by issn
    def get_openalex_sample(keywords, issns):
        # To test: https://api.openalex.org/works?filter=locations.source.issn:0010-0277&search=categorization&per-page=200

        works = list()
        keywords = ' OR '.join(f'"{k}"' for k in keywords)
        response = requests.get(
            f"https://api.openalex.org/works?filter=locations.source.issn:{'|'.join(issns)},title_and_abstract.search:{keywords}&per-page=200&cursor=*",
            # per-page parameter must be between 1 and 200
            headers={"mailto": os.getenv("OPENALEX_EMAIL")},  # use OpenAlex polite pool
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
            headers={"mailto": os.getenv("OPENALEX_EMAIL")},
            ).json()
                try:
                    next_cursor = subsequent_response["meta"]["next_cursor"]
                except KeyError:
                    print(subsequent_response["message"])
                works += subsequent_response["results"]       

        return n_results, works
      
    search_terms = ["concept formation"]
    _n, openalex_data = get_openalex_sample(search_terms, issns[:100])

    _, _openalex_data = get_openalex_sample(search_terms, issns[100:])
    openalex_data += _openalex_data
    oa_df = pd.DataFrame(openalex_data)
    oa_df.head()
    dois = oa_df.doi.tolist()
    print(f"Results:......{len(oa_df)}")
    return (
        df,
        dois,
        get_journals,
        get_openalex_sample,
        issns,
        journal_data,
        journals,
        n,
        oa_df,
        openalex_data,
        search_terms,
    )


@app.cell
def __(oa_df):
    oa_df.to_csv("concept-formation.csv", encoding='utf-8')
    return


@app.cell
def __():
    import os
    import requests
    from dotenv import load_dotenv
    import pandas as pd
    return load_dotenv, os, pd, requests


if __name__ == "__main__":
    app.run()
