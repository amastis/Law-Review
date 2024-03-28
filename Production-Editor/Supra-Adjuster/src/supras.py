import re
import copy
from pathlib import Path
import csv
import os
from typing import Dict, Union, List, Tuple

from docx2python import docx2python


def find_footnote_number(author: str, starting_footnote: int, footnotes: Dict[int, List[str]], search_space: int) -> int:
    # gets author + footnote pointing to currently
    last_spotted = starting_footnote # in case there is a supra mention to the author in the same footnote as its first use...
    counter = starting_footnote if starting_footnote < len(footnotes.keys()) else len(footnotes.keys()) - 1
    end_search_space: int = starting_footnote - search_space - 1
    if end_search_space < 1:
        end_search_space = 0

    #print(re.findall(f'{author},\ssupra', footnotes[counter][0]))
    # re usage is to make sure that author's name is not part of a word
    while counter != end_search_space and (author not in re.findall(f'[A-Za-z]?{author}[A-Za-z]?', footnotes[counter][0]) or re.findall(f'{author},\ssupra', footnotes[counter][0])): # TODO case comparison?
        #print(author, counter, footnotes[counter][0])
        if author in footnotes[counter][0]:
            last_spotted = counter
        counter -= 1

    if counter == 0: # TODO FIX
        return last_spotted
    return counter # should never not return correct value... # TODO what if unable to find???

def check_not_empty_or_credits(item) -> bool:
    return item[0] and '\t ' in item[0] # try to remove the thanks given footnote 


def get_footnotes(file_path: str) -> Dict[int, List[str]]:
    docx_temp = docx2python(file_path)
    filtered_footnotes = filter(check_not_empty_or_credits, docx_temp.footnotes[0][0])
    footnotes: Dict[int, List[str]] = {c+1:[item[0].split('\t ', 1)[1]] for c, item in enumerate(filtered_footnotes)}
    return footnotes    


def compare_footnotes(file_path: str, original_num_footnotes: int, progressbar) -> Union[Dict[str, int], List[int], List[int]]:
    # get footnotes from word document and insert into dict
    footnotes: Dict[int, List[str]] = get_footnotes(file_path)
    ''' TO check if there are spaces in between footnote number and footnote
    for i,item in enumerate(docx_temp.footnotes[0][0]):
        if not check_not_empty_or_credits(item):
            print(i, item)
    '''
    INTRODUCTORY_SIGNALS: Tuple[str] = ('E.g.,', 'Accord', 'See', 'see', 'See also', 'see also', 'Cf.', 'Compare', 'with', 'Contra', 'But see', 'But cf.', 'See generally', 'see generally')

    original_footnotes = copy.deepcopy(footnotes)
    half_window: int = len(footnotes.keys()) - original_num_footnotes
    
    # break footnote into individual footnotes
    for k,item in footnotes.items():
        footnotes[k] = item[0].split(';')

    supras: Dict[str, int] = {} # keys in name format "KEY AUTHOR": POSSIBLE FOOTNOTE #, 
    supras_notes: List[int] = []
    infras: List[int] = []
    for k,item in footnotes.items():
        for source in item:

            if 'supra notes' in source:
                # currently just mark that there is a range of supra notes to look through with current footnote #...
                supras_notes.append(k)
            elif 'supra note' in source:
                author: str = re.findall('[A-Za-z\s]+[\'’]?[A-Za-z\s]+\.?', source[:source.index('supra')])[-1].strip()
                if start_str := [item for item in INTRODUCTORY_SIGNALS if author.startswith(item)]:
                    lengths: List[int] = [len(item) for item in start_str]
                    author = author[max(lengths):].strip()
                starting_footnote: int = int(re.findall('note (\d+)', source)[0])
                search_start: int = starting_footnote + half_window 
                window_size: int  = 2 * half_window + 1
                print(starting_footnote, search_start)
                if search_start > k:
                    window_size -= (search_start - k)
                    search_start = k - 1
                print(k, search_start, window_size, author)
                #found_footnote = find_footnote_number(author, k, original_footnotes)
                found_footnote = find_footnote_number(author, search_start, original_footnotes, window_size)
                print(found_footnote)
                if found_footnote != starting_footnote:
                    supras[f'{k} {author}'] = found_footnote
            elif 'infra' in source and 'infra Part' not in source:
                # currently just mark that there is an infra to look at...
                infras.append(k)
        progressbar.put(1)

    return supras, supras_notes, infras

def to_file(footnotes: Dict[str, int], supras: List[str], infras: List[str]) -> None:
    download_path: str = Path.home() / 'Downloads'

    if footnotes:
        print('Current Supra Footnote, Author, New Footnote')
        with open(os.path.join(download_path, 'footnote_predictions.csv'), 'w') as file:
            csv_file = csv.writer(file)
            csv_file.writerow(['Current Supra Footnote', 'Author', 'New Footnote'])
            csv_file.writerows([[*(k.split(' ', 1)), item] for k, item in footnotes.items()])
        print(footnotes)

    if not supras and not infras:
        return
    with open(os.path.join(download_path, 'infras_and_supra_notes.txt'), 'w') as file:
        if supras:
            file.write(f'Supra Notes to investigate: {supras}\n')
            print(f'Supra Notes to investigate: {supras}')

        if infras:
            file.write(f'Infras to investigate: {infras}')
            print(f'Infras to investigate: {infras}')


def main(original_path: str, edited_path: str, progressbar) -> None:
    docx_temp = docx2python(original_path)
    filtered_footnotes = filter(check_not_empty_or_credits, docx_temp.footnotes[0][0])
    originial_size: int = len(list(filtered_footnotes))

    footnotes_to_print, supras_to_investigate, infras_to_investigate = compare_footnotes(edited_path, originial_size, progressbar)

    to_file(footnotes_to_print, supras_to_investigate, infras_to_investigate)

if __name__ == '__main__':
    import queue
    progressbar = queue.Queue()
    original_path: str = './ORIGINAL.docx' # TODO CHANGE FOR LOCAL RUN
    edited_path: str = './EDITED.doxc' # TODO CHANGE FOR LOCAL RUN

    main(original_path, edited_path, progressbar)

''' TODO
- checking if there are additional references with that author's name to ensure that some supras don't have to be thought about -- while others have to check what the previous version was... 
'''