#/usr/bin/env python
"""Usage:
    panopto.py ls [--verbose] <folder-or-session-id>
    panopto.py get-access [--verbose] <folder-or-session-id>
    panopto.py update-access [--verbose] <folder-or-session-id> <inherited> <level>
    panopto.py get-session [--verbose] <session-id>
"""

import json, os, re, sys, urllib3

from docopt import docopt

from utils.panopto_oauth2 import PanoptoOAuth2
from utils.panopto_folders import PanoptoFolders
from utils.panopto_sessions import PanoptoSessions
from utils.panopto_uploader import PanoptoUploader

from local import (
    PANOPTO_ALLOW_INSECURE_HTTP_REQUESTS, 
    PANOPTO_CLIENT_ID, 
    PANOPTO_CLIENT_SECRET,
    PANOPTO_SERVER
)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    if PANOPTO_ALLOW_INSECURE_HTTP_REQUESTS:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    oauth2 = PanoptoOAuth2(
        PANOPTO_SERVER,
        PANOPTO_CLIENT_ID,
        PANOPTO_CLIENT_SECRET,
        not PANOPTO_ALLOW_INSECURE_HTTP_REQUESTS,
        arguments['--verbose']
    )

    if arguments['ls']:
        folder_mgr = PanoptoFolders(
            PANOPTO_SERVER,
            not PANOPTO_ALLOW_INSECURE_HTTP_REQUESTS,
            oauth2
        )
    
        for f in folder_mgr.get_children(arguments['<folder-or-session-id>']):
            print('f\t{}\t{}'.format(f['Id'], f['Name']))
        for s in folder_mgr.get_sessions(arguments['<folder-or-session-id>']):
            print('s\t{}\t{}'.format(s['Id'], s['Name']))

    if arguments['get-access']:
        session_mgr = PanoptoSessions(
            PANOPTO_SERVER,
            not PANOPTO_ALLOW_INSECURE_HTTP_REQUESTS,
            oauth2
        )
        a = session_mgr.get_access(arguments['<folder-or-session-id>'])
        print('{}\t{}'.format(a['IsInherited'], a['Level']))

    if arguments['update-access']:
        session_mgr = PanoptoSessions(
            PANOPTO_SERVER,
            not PANOPTO_ALLOW_INSECURE_HTTP_REQUESTS,
            oauth2
        )
        assert arguments['<inherited>'] in ('True', 'False')
        if arguments['<inherited>'] == 'True':
            arguments['<inherited>'] = True
        if arguments['<inherited>'] == 'False':
            arguments['<inherited>'] = False
        assert arguments['<level>'] in (
            'Organization', 
            'OrganizationUnlisted', 
            'Public',
            'PublicUnlisted', 
            'Restricted'
        )
        session_mgr.update_access(
            arguments['<folder-or-session-id>'],
            arguments['<inherited>'],
            arguments['<level>']
        )

    if arguments['get-session']: 
        session_mgr = PanoptoSessions(
            PANOPTO_SERVER,
            not PANOPTO_ALLOW_INSECURE_HTTP_REQUESTS,
            oauth2
        )
        print(
            json.dumps(
                session_mgr.get_session(arguments['<session-id>'])
            )
        )
