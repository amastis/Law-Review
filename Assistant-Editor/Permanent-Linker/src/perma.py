# https://perma.cc/docs/developer#developer-archives
import time
import requests
import re
import csv
import os
from pathlib import Path
from typing import Dict, Union, List

from docx2python import docx2python
from tqdm import tqdm

def folder_id(response, folder_name: str) -> int: 
    for item in response:
        if item['name'] == folder_name:
            return item['id']
    return None

def get_user_folder(headers: Dict[str, str]) -> Union[int, None]:
    response = requests.get('https://api.perma.cc/v1/user/', headers=headers)

    wayne_folder = folder_id(response.json()['top_level_folders'], 'Wayne Law Review')

    response = requests.get(f'https://api.perma.cc/v1/folders/{wayne_folder}/folders', headers=headers)
    return folder_id(response.json()['objects'], 'Test')
    #return None # no Personal Links folder found
'''
def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]
'''
# create and return the archived links
def archive_links(headers: Dict[str, str], linked_folder: int, urls: List[str]) -> None:

    #for batched_links in batch(urls, 10):

    json_data = {
        'urls': urls,
        'target_folder': linked_folder,
    }

    # https://stackoverflow.com/questions/16511337/correct-way-to-try-except-using-python-requests-module
    try:
        response = requests.post('https://api.perma.cc/v1/archives/batches', headers=headers, json=json_data)
        print(response)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("OOps: Something Else",err)    
    '''
    archive_results = {}
    for item in response.json()['capture_jobs']:
        archive_results[item['submitted_url']] = f'https://perma.cc/{item["guid"]}'

    return archive_results
    '''

def get_perma_links(headers: Dict[str, str], linked_folder: int, number_archived: int) -> Dict[str, str]:

    params = {
        'limit': number_archived,
    }

    try: 
        response = requests.get(f'https://api.perma.cc/v1/folders/{linked_folder}/archives', params=params, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("OOps: Something Else",err)
    
    archive_results: Dict[str, str] = {}
    print(len(response.json()['objects']), number_archived)
    for item in response.json()['objects']:
        archive_results[item['url']] = f'https://perma.cc/{item["guid"]}'

    return archive_results

def check_not_empty_or_credits(item) -> bool:
    return item[0] and '\t ' in item[0] # try to remove the thanks given footnote

def get_footnotes(file_path: str) -> Dict[int, List[str]]:
    # get footnotes from word document and insert into dict
    docx_temp = docx2python(file_path)
    filtered_footnotes = filter(check_not_empty_or_credits, docx_temp.footnotes[0][0])
    footnotes: Dict[int, List[str]] = {c+1:[item[0].split('\t ', 1)[1]] for c, item in enumerate(filtered_footnotes)}
    
    links = []
    for k,item in footnotes.items():
        for source in item:
            # https://stackoverflow.com/questions/6038061/regular-expression-to-find-urls-within-a-string
            #is_link: str = re.findall(r"/(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])/igm", source)
            is_link = re.findall(r"https?://[^\s]+", source)
            #print(is_link, source)
            if is_link:
                total_links: int = len(is_link)
                perma_links = ['perma.cc' in link for link in is_link]
                perma_links_count: int = sum(perma_links)
                if total_links % 2 == 1 or perma_links_count < (total_links / 2): #not any('perma.cc' in link for link in is_link): # TODO only those that are subsequent (immediately) and not just any because misses other links available
                    # https://stackoverflow.com/questions/22650506/how-to-remove-non-alphanumeric-characters-at-the-beginning-or-end-of-a-string
                    # remove last character that's not number or letter
                    links.extend([re.sub(r"^\W+|\W+$", "", url) for url,is_perma in zip(is_link, perma_links) if not is_perma])

    return links

def save_results(link_pairs: Dict[str, str], original_file: str) -> None:
    # convert dict pairs to csv format
    link_results = [[k,v] for k,v in link_pairs.items()]
    with open(str(Path.home() / "Downloads" / f"perma {original_file}"), 'w') as file:
        writer = csv.writer(file)
        writer.writerows(link_results)

def main(api_key: str, file_path: str, progressbar) -> None:
    to_archive: List[str] = get_footnotes(file_path)

    request_headers = {
        'Authorization': f'ApiKey {api_key}',
    }
    folder_value: int = get_user_folder(request_headers)
    if not folder_value:
        print('no Personal Links folder')
        return

    archive_links(request_headers, folder_value, to_archive)

    for i in range(len(to_archive)): # TODO do we need to wait this long?
        time.sleep(1)
        progressbar.put(1)

    if len(to_archive):
        try:
            perma_results = get_perma_links(request_headers, folder_value, len(to_archive))
        except Exception as e:
            print(e)
            progressbar.put(e)

        # to only show user those links they have requested        
        print(perma_results)
        remove_keys: List[str] = [item for item in perma_results if item not in to_archive]
        for item in remove_keys:
            perma_results.pop(item, None)

        _, file_name = os.path.split(file_path)
        save_results(perma_results, file_name.replace('.docx', '.csv'))


if __name__ == '__main__':
    # only for when file is run locally -- TESTING PURPOSE
    import queue
    import settings # .py file with plaintext variables (API_KEY)

    file_path = './TESTING.docx' # WARNING: there is no TESTING.docx - TODO change for local purposes
    progressbar = queue.Queue()

    main(settings.API_KEY, file_path, progressbar)
