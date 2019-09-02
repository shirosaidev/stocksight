#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import.kibana.py - import kabana visual for each defined symbol
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import requests
import sys
import os.path
from config import symbols

if __name__ == '__main__':

    try:
        template_file = open('kibana_export/export.7.3.ndjson', "rt", encoding='utf-8')
        import_template = template_file.read()
        template_file.close()

        for symbol in symbols:
            try:
                ndjson_file_path = 'kibana_export/'+symbol+'_exports.ndjson'
                ndjson_file = open(ndjson_file_path, "wt", encoding='utf-8')
                final_text = import_template.replace('tmpl',symbol)
                ndjson_file.write(final_text)
                ndjson_file.close()

                kibana_import_url = 'http://kibana:5601/api/saved_objects/_import'
                payload = { 'overwrite': 'false'}
                headers ={'kbn-xsrf': 'True'}
                post = requests.request('POST',kibana_import_url, headers=headers, files={'file': open(ndjson_file_path, "rt", encoding='utf-8')})
                print("Import %s Kibana Dashboard" % symbol)
                print(ndjson_file_path)
                print(post.text)

            except Exception as e:
                print(e);
                pass

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)