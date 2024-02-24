from typing import Dict, List, Any
import re
import os
import zipfile
from pathlib import Path

from docx2python import docx2python
import pandas
# LOCAL file
from westlaw_links import WestLaw

def check_not_empty_or_credits(item) -> bool:
    return item[0] and '\t ' in item[0] # try to remove the thanks given footnote

def get_footnotes(file_path: str) -> Dict[int, List[str]]:
    # get footnotes from word document and insert into dict
    docx_temp = docx2python(file_path)
    print(docx_temp.footnotes)
    filtered_footnotes = filter(check_not_empty_or_credits, docx_temp.footnotes[0][0])
    footnotes: Dict[int, List[str]] = {c+1:[item[0].split('\t ', 1)[1]] for c, item in enumerate(filtered_footnotes)}

    return footnotes

# https://github.com/python-openxml/python-docx/issues/780
def get_total_pages(file_path: str) -> int:
    docx_object = zipfile.ZipFile(file_path)
    docx_property_file_data = docx_object.read('docProps/app.xml').decode()
    page_count = re.search(r"<Pages>(\d+)</Pages>", docx_property_file_data).group(1)
    return int(page_count)

def doc_info(file_path: str) -> str:
    return f"Number of Footnotes: {len(get_footnotes(file_path))}\nNumber of Pages: {get_total_pages(file_path)}"

def separate_sources(source: str) -> List[str]:
    # split multiple citations based on the ";" in the structure
    if ';' in source:
        return source.split('; ')
    return [source]

def id_last_source(source: str, count: int) -> int:
    # loop through backwards looking for id. or Id. in a source
    # have to look if the previous usage has an id to carry it forward
    if len(source) > 20: # TODO Id should only be in the first bit of a source label # how to discount a paragraph that talks about itself?
        source = source[:20]
    if 'id.' in source or 'Id.' in source:
        print('id', count)
        return str(count - 1)
    # TODO

def supra_source(source: str) -> int:
    # look through looking for supra if found then look for number after note --> which is the footnote refernced
    # use the number found to mark where this note is found
    if 'supra notes' in source:
        # TODO
        pass
    elif 'supra note' in source:
        print('supra note')
        supra_pos = source[source.find('supra note') + len('supra note'):]
        return re.findall('\d+', supra_pos)[0] # return first digit section
    
    # TODO

def get_source_type(source: str) -> str:
    ''' read in the source to see what type of source it is '''
    # TODO 
    source = source.lower()
    source_type = ''

    ''''
    Administrative Material
    Agency study
    Article
    article by institutional author
    Article in a Book Compilation
    Blog Article
    Blog Post
    Book
    Book by institutional author
    Brief? Periodical?
    Case
    City Ordinance
    Code
    Comment
    Congressional Hearing
    County Code
    Court Rule
    Data Table
    Directory
    Document
    DOJ Letter
    DOJ Settlement Aggreement
    Email
    Essay
    Executive Branch Document
    Executive Branch Letter
    Executive Branch Website
    Executive Material
    Forthcoming Periodical
    Government Report
    Govt. Release
    Hearing
    House Resolution
    institutional author
    Institutional Release?
    Internal citation
    internet
    Internet Periodical Material
    Journal
    Journal Article
    Law Journal
    law review
    Law review article
    Law Review Note
    Legislative Act
    Legislative Material
    Memorandum
    News Article
    news release
    newspaper
    Note Itself
    Online article
    Online source
    online web page
    Pamphlet
    Periodical
    Press Release
    Questionnaire
    Regulation
    Release
    Report
    Resolution
    Standards (?)
    State Agency Report
    State Auditor Report
    State constitution
    State Resolution
    statute
    Training Document
    Transcript
    Trial Pleading
    Video
    web - instituional author
    web article
    web page
    Website
    Website Article
    Website Fact Sheet
    Website Overview of Data Compilation
    Website/Release
    Working Paper
    '''

    if ' v. ' in source or ' v ' in source:
        source_type = 'Case'
    elif ' act ' in source or 'mich. comp. laws' in source or 'comp. stat. ann.' in source or 'u.s.c.' in source:
        source_type = 'Statute'
    elif 'https' in source:
        source_type = 'Article'
    elif ' art. ' in source:
        source_type = 'constitution'
    elif 'L. Rev.' in source:
        source_type = 'Law Review Article'
    return source_type # if source not found return empty string

def aggregate_subsequent(series):
    return reduce(lambda x, y: x + y, series)

def get_subsequent_footnotes(footnotes: Dict[int, List[str]]) -> Dict[int, Dict[str, Any]]:
    footnote_split_num = 0
    for k,v in footnotes.items():
        footnotes[k] = {'sources': separate_sources(v[0])}
        footnote_split_num += len(footnotes[k])
    # reverse insert similar ids and supras
    # TODO get accurate 
    test_subsequent_Footnotes: List[List[str]] = [[] for _ in range(footnote_split_num + 1)] # index 0 is a place holder nothing should go there -- no references to final position either (nothing subsequent)
    subsequent_Footnotes: List[str] = []
    for k,value_dict in reversed(footnotes.items()):
        for v in reversed(value_dict['sources']): # reverse so the items match up with their end numbering sys
            id_value: str = id_last_source(v, k)
            supra_value: str = supra_source(v)

            if id_value and test_subsequent_Footnotes[k]:
                # copy and delete [] to new value
                old_values = test_subsequent_Footnotes[int(id_value) + 1] # id_value is already -1 so add 1 to get original value
                test_subsequent_Footnotes[int(id_value)] = old_values
                test_subsequent_Footnotes[int(id_value)].append(k) # TODO does it need to be -1?
                test_subsequent_Footnotes[int(id_value) + 1] = []
            elif id_value:
                test_subsequent_Footnotes[int(id_value)].append(k)
                subsequent_Footnotes.append(id_value)
            elif supra_value and test_subsequent_Footnotes[k]:
                old_values = test_subsequent_Footnotes[int(k)] # supra_value is already -1 so add 1 to get original value
                if test_subsequent_Footnotes[int(supra_value)]:
                    test_subsequent_Footnotes[int(supra_value)].extend(old_values)
                else:
                    test_subsequent_Footnotes[int(supra_value)] = old_values
                test_subsequent_Footnotes[int(supra_value)].append(k) # TODO does it need to be -1?
                test_subsequent_Footnotes[int(k)] = []
            elif supra_value:
                subsequent_Footnotes.append(supra_value)
                test_subsequent_Footnotes[int(supra_value)].append(k)
            else:
                subsequent_Footnotes.append('') # blank placeholder

    # add in the subsequnt footnotes into dict object
    for c, item in enumerate(test_subsequent_Footnotes[1:]):
        footnotes[c+1]['subsequent_footnotes'] = item

    return footnotes

def get_footnote_types(footnotes: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    # Example RETURN: {1: {'sources': ['48 S.Ct. 564'], 'type': ['Case']})
    # go through and assign types
    # how to split the footnotes into own 
    for _,v in footnotes.items():
        v['type'] = [get_source_type(source) for source in v['sources']]
        # regex tries to get the [volumne reporter page_number] of case
        #v['link'] = [westlaw.get_source_link(re.findall('\d+\s[A-Za-z\.\d\s]+\s\d+', search_term)[0]) for search_term, source_type in zip(v['sources'], v['type']) if source_type == "Case"] # TODO link

    return footnotes

def to_pandas(footnotes: Dict[int, Dict[str, Any]]) -> pandas.DataFrame:
    ''' Write the final product to an excel file '''
    footnote_num = [str(c + 1) for c,k in enumerate(footnotes) for _ in footnotes[k]['sources']]
    footnote_source = [source for k,v in footnotes.items() for source in v['sources']]
    footnote_type = [type for _,v in footnotes.items() for type in v['type']]
    #footnote_link = [link for _,v in footnotes.items() for link in v['link']]
    footnote_subsequent = [', '.join(str(x) for x in reversed(v['subsequent_footnotes'])) if v.get('subsequent_footnotes') else '' for k,v in footnotes.items() for _ in v['sources']]
    df1 = pandas.DataFrame.from_dict({"Footnote #": footnote_num, "Type": footnote_type, "Source Name": footnote_source, "Subsequent Footnotes": footnote_subsequent, "Link/Location": []}, orient='index').T

    return df1

def remove_duplicate_internal_citations(df1: pandas.DataFrame) -> pandas.DataFrame:
   # TODO indexing by the supra value won't work if the footnote number has changed

    # separate out the different sources from the footnote number into own column
    #df1 = df1.set_index('Footnote #').apply(pandas.Series.explode, axis=0).reset_index()
    # rearrange columns in order

    # remove the id and supras
    #df1 = df1.drop_duplicates(keep='first', subset=['Source Name'])
    indexs_drop = []
    print("DUPLICATES")
    dupes = df1['Source Name'].duplicated(keep=False)
    #dupes = df1[].duplicated(subset=['Source Name'])
    #dupes.to_csv("./dupes.csv")
    #df1.to_csv("./dupes_compare.csv")

    # get indexs for duplicates to create a subsequent footnotes list w/ first index removed
    dupe_index_dict = {}
    first_dupe_indexs = []
    for (index, item), _ in zip(df1.iterrows(), dupes):
        item_name = item['Source Name']
        if 'supra ' in item_name or id_last_source(item['Source Name'], 2):
            continue

        footnote_number = item['Footnote #']
        if item_name in dupe_index_dict:
            dupe_index_dict[item_name].append(footnote_number)
            if item['Subsequent Footnotes']:
                dupe_index_dict[item_name].append(item['Subsequent Footnotes'])
        else:
            if not item['Subsequent Footnotes']:
                dupe_index_dict[item_name] = []
            else:
                dupe_index_dict[item_name] = [item['Subsequent Footnotes']]
            first_dupe_indexs.append(index)

    # finding the rows that will need to be dropped
    for (index, item), duplicate_value in zip(df1.iterrows(), df1['Source Name'].duplicated(keep=False)): # https://stackoverflow.com/questions/68772493/tagging-all-duplicates-pandas-dataframe-even-the-first-instace-without-nan
        # column names 'Source Name', 'Footnote #', 'Subsequent Footnotes'
        if first_dupe_indexs and index == first_dupe_indexs[0]:
            # update the dupes with later mentions and don't delete that index
            item['Subsequent Footnotes'] = ', '.join(dupe_index_dict[item['Source Name']])
            first_dupe_indexs.pop(0)
        elif duplicate_value and not item['Subsequent Footnotes']:
            #print(index, item)
            indexs_drop.append(index)
            #print(item)
        elif duplicate_value:
            # TODO add duplicate value to earlier column
            #print(item)
            pass
        elif 'supra ' in item['Source Name'] or (id_last_source(item['Source Name'], 2) and not item['Subsequent Footnotes']): # remove those rows w/ supra in them
            indexs_drop.append(index)

    #print(indexs_drop)
    df1 = df1.drop(index=indexs_drop)
    return df1

def get_links(df1: pandas.DataFrame, westlaw, total_footnotes: int, progressbar) -> pandas.DataFrame:
    progress = 0
    for (_, item) in df1.iterrows(): # get links to cases
        progressbar.put(1)
        progress += 1
        if item['Type'] == "Case":
            try:
                search_term = re.findall('\d+\s[A-Za-z\.\d\s]+\s\d+', item['Source Name'])[0]
            except IndexError: 
                print(item['Source Name'])
                search_term = None
            if search_term:
                try:
                    item['Link/Location'] = westlaw.get_source_link(search_term)
                except Exception as e:
                    progressbar.put(e)

    # bc iterrows() are already compressed from the original footnote number 
    remainder: int = total_footnotes - progress - 1 if progress else 0 
    if remainder > 0:
        progressbar.put(remainder)
    return df1

def article_links(df1: pandas.DataFrame) -> pandas.DataFrame:
    for (_, item) in df1.iterrows(): # get article links from footnote itself
        if item['Type'] == "Article":
            try:
                is_link = [link for link in re.findall(r"https?://[^\s]+", item['Source Name']) if 'perma' not in link][0]
            except IndexError: 
                print(item['Source Name'])
                is_link = None
            if is_link:
                item['Link/Location'] = is_link
    return df1

def download_excel(df1: pandas.DataFrame, file_name: str) -> None:
    df1 = df1[['Source Name', 'Type', 'Footnote #', 'Subsequent Footnotes', 'Link/Location']]
    df1.to_excel(str(Path.home() / "Downloads" / file_name), index=False)

# going through a single word doc to create the proper excel file
def create_excel(file_path: str, file_name: str, is_getting_links: bool, westlaw, progressbar) -> None:
    footnotes: Dict[int, List[str]] = get_footnotes(file_path)
    total_footnotes: int = len(footnotes)
    footnotes = get_subsequent_footnotes(footnotes)
    footnotes = get_footnote_types(footnotes)
    dataframe = to_pandas(footnotes)
    dataframe = remove_duplicate_internal_citations(dataframe)
    if is_getting_links:
        dataframe = get_links(dataframe, westlaw, total_footnotes, progressbar)
    dataframe = article_links(dataframe) # TODO use links to find duplicates
    download_excel(dataframe, file_name)
    if not is_getting_links:
        progressbar.put(total_footnotes - 1)

def main(file_path: str, westlaw_user: str, westlaw_pass: str, progressbar) -> None:
    is_getting_links: bool = bool(westlaw_user and westlaw_pass)
    
    westlaw = None
    if is_getting_links:
        westlaw = WestLaw(westlaw_user, westlaw_pass)

    if os.path.isfile(file_path):
        _, file = os.path.split(file_path)
        excel_name = f'{file.split(".")[0]}.xlsx'
        create_excel(file_path, excel_name, is_getting_links, westlaw, progressbar)
    else: # is a folder
        for file in os.listdir(file_path):
            if file == '.DS_Store':
                continue
            excel_name = f'{file.split(".")[0]}.xlsx'
            path_to_file = Path.joinpath(Path(file_path), file)
            create_excel(path_to_file, excel_name, is_getting_links, westlaw, progressbar)
            break # TODO link


def test(file_path: str, westlaw_user: str, westlaw_pass: str, progressbar) -> None:
    westlaw = WestLaw(settings.westlaw_username, settings.westlaw_password)

    footnotes = {1: {'sources': ['48 S.Ct. 564'], 'type': ['Case']}, 
        2: {'sources': ['389 U.S. 347'], 'type': ['Case']},
    }
    dataframe = to_pandas(footnotes)
    get_links(dataframe, westlaw, progressbar)


if __name__ == '__main__':
    # only for when the file is run locally -- TESTING PURPOSES
    import queue
    import settings # .py file with plaintext variables (westlaw_username, westlaw_password)
    file_path = './TESTING.docx' # WARNING: there is no TESTING.docx - TODO change for local purposes
    progressbar = queue.Queue()
    main(file_path, settings.westlaw_username, settings.westlaw_password, progressbar)
    #test(file_path, settings.westlaw_username, settings.westlaw_password, progressbar)
