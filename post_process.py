import re
import os
import json
import shutil
import numpy as np

def get_adjacency_matrix(url_relations):
    n = len(url_relations) # # nodes
    
    m = np.zeros((n,n))
    for i in url_relations:
        for j in url_relations[i]:
            m[i][j] = 1/len(url_relations[i])
    
    return m.T

def find_repeated_fingerprints(url_fingerprints):
    sorted_fps = sorted(url_fingerprints.values())
    repeated_fps = set()
    for fp1, fp2 in zip(sorted_fps, sorted_fps[1:]):
        if fp1 == fp2:
            repeated_fps.add(fp1)
    
    return {fp: set([url for url, _fp in url_fingerprints.items() if _fp == fp])
                for fp in repeated_fps}

def post_process(folder, verbose=False):
    meta_data = dict()
    url_relations = dict()
    url_anchortext = dict()
    
    converted_metadata_folder = os.path.join(folder, 'converted_metadata')
    if os.path.exists(converted_metadata_folder) and os.path.isdir(converted_metadata_folder):
        shutil.rmtree(converted_metadata_folder)
    os.mkdir(converted_metadata_folder)
    print('Converted metadata will be saved in', converted_metadata_folder)
    
    files = os.listdir(folder)
    n_files = len(files)
    print('Discovered', n_files, 'files. Start to read them')
    
    for i, file in enumerate(files):
        doc_path = os.path.join(folder, file)
        metadata_path = os.path.join(folder, 'metadata', file+'.json')

        if not os.path.isdir(doc_path)\
            and not os.path.islink(doc_path)\
            and os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                md = json.loads(f.read())
                child_urls = md.pop('child_urls')
                meta_data[file] = md
                url = md['url']

                for child_url, anchor_text in child_urls:
                    url_relations.setdefault(url, set()).add(child_url)
                    
                    if re.search(r'\w{5,}', anchor_text):
                        url_anchortext.setdefault(child_url, set()).add(anchor_text)
        
        if i%10 == 0:
            print(i+1, '/', n_files, ' '*20, end='\r')
    else:
        print('Completed', ' '*20)

    # url and index conversions
    print('Removing child URLs which were not crawled')
    index_to_url = dict(enumerate(url_relations.keys()))
    url_to_index = {url: i for i, url in index_to_url.items()}

    # remove child_urls that are not part of urls, and change url to index
    url_relations = {url_to_index[url]: 
                        [url_to_index[url] for url in child_urls if url in url_to_index]
                            for url, child_urls in url_relations.items()}
    url_anchortext = {url: sorted(at) for url, at in url_anchortext.items() if url in url_to_index}

    # am
    print('Getting adjacency matrix')
    am = get_adjacency_matrix(url_relations)
    am_to = (am>0).sum(axis=1)
    am_from = (am>0).sum(axis=0)

#     # page rank
#     pr = page_rank(am, verbose=verbose)

    new_meta_data = {url: {
#         'page_rank_score': float(pr[index]),
        'anchor_text': url_anchortext[url],
        'number_of_links_from_which': int(am_from[index]),
        'number_of_links_to_which': int(am_to[index]),
        }
        for url, index in url_to_index.items()
    }
    
    print('Saving converted meta data')
    n_meta_data = len(meta_data)
    
    for i, (file, md) in enumerate(meta_data.items()):
        path = os.path.join(converted_metadata_folder, file+'.json')
        
        with open(path, 'w') as f:
            f.write(json.dumps(dict(md, **new_meta_data[md['url']])))
        
        if i%10==0:
            print(i+1, '/', n_files, ' '*20, end='\r')
    else:
        print('Completed', ' '*20)
    
    
