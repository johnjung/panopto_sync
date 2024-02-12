#!python3
import argparse
from panopto_oauth2 import PanoptoOAuth2
from panopto_folders import PanoptoFolders
from panopto_uploader import PanoptoUploader
import urllib3
import sys
import os
import json
import re

from local import PANOPTO_SERVER, PANOPTO_CLIENT_ID, PANOPTO_CLIENT_SECRET


SOUND_FILES_ON_DISK = '/data/digital_collections_ocfl/orig/dma/sound_files'


def parse_argument():
    '''
    Argument definition and handling.
    '''
    parser = argparse.ArgumentParser(description='Upload a single video file to Panopto server')
    parser.add_argument('--server', dest='server', required=True, help='Server name as FQDN')
    parser.add_argument('--folder-id', dest='folder_id', required=True, help='ID of uppermost Panopto folder')
    parser.add_argument('--client-id', dest='client_id', required=True, help='Client ID of OAuth2 client')
    parser.add_argument('--client-secret', dest='client_secret', required=True, help='Client Secret of OAuth2 client')
    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_argument()

    # Can get info about files in a folder like this:
    # print(folder_mgr.get_sessions('028d107b-1e89-4511-9b01-aecb011d9e92'))
    # sys.exit()

    skip_verify = True

    # Suppress annoying warning message.
    if skip_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    oauth2 = PanoptoOAuth2(
        args.server, 
        args.client_id, 
        args.client_secret, 
        not skip_verify
    )

    # Get data about DMA folders from Panopto.
    folder_mgr = PanoptoFolders(
        args.server,
        not skip_verify,
        oauth2
    )

    panopto_folders_list = folder_mgr.get_children(args.folder_id)

    # Report folder names that appear more than once. 
    panopto_folders_dict = {}
    for f in panopto_folders_list:
        if f['Name'] not in panopto_folders_dict:
            panopto_folders_dict[f['Name']] = 0
        panopto_folders_dict[f['Name']] += 1
    print_header = True
    for folder_name, count in panopto_folders_dict.items():
        if count > 1:
            if print_header:
                print('SOME FOLDER NAMES APPEAR MORE THAN ONCE')
                print_header = False
            print(folder_name)
    if print_header == False:
        print('')

    # Report folder names that appear on disk but not in Panopto, and
    # vice versa.
    panopto_folders = set([f['Name'] for f in panopto_folders_list])

    disk_folders = set()
    for e in os.listdir(SOUND_FILES_ON_DISK):
        if e in ('C',):
            continue
        if os.path.isdir(os.path.join(SOUND_FILES_ON_DISK, e)):
            disk_folders.add(e)

    print_header = True
    for i in sorted(list(panopto_folders - disk_folders)):
        if print_header:
            print('{} FOLDERS IN PANOPTO BUT NOT ON DISK'.format(len(panopto_folders - disk_folders)))
            print_header = False
        print(i)
    if print_header == False: 
        print('')

    print_header = True
    for i in sorted(list(disk_folders - panopto_folders)):
        if print_header:
            print('{} FOLDERS ON DISK BUT NOT IN PANOPTO'.format(len(disk_folders - panopto_folders)))
            print_header = False
        print(i)
    if print_header == False:
        print('')

    sys.exit()

    # Build a lookup for Panopto folder ids.
    panopto_folder_ids = {}
    for f in panopto_folders_list:
        panopto_folder_ids[f['Name']] = f['Id']

    uploader = PanoptoUploader(
        args.server,
        not skip_verify,
        oauth2
    )

    for name, identifier in panopto_folder_ids.items():
        print(name)
        sessions = folder_mgr.get_sessions(identifier)
        if sessions == []:
            for root, dirs, files in os.walk(os.path.join(SOUND_FILES_ON_DISK, name)):
                for f in files:
                    p = os.path.join(root, f)
                    m = re.search('\/sound_files\/([^/]+)\/ready_wav\/([^/]+)$', p)
                    try:
                        folder = m.group(1)
                    except AttributeError:
                        continue

                    if folder in ('hin-urd-diags1&2',):
                        continue

                    uploader.upload_video(p, panopto_folder_ids[folder])
                    print(p)
                    print(folder)
                    print('')
