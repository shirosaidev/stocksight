import requests
import sys
import os.path
from config import symbols

if __name__ == '__main__':

    try:
        template_file = open('../kibana_export/export.7.3.ndjson', "rt", encoding='utf-8')
        import_template = template_file.read()
        template_file.close()

        for symbol in symbols:
            try:
                ndjson_file_path = '../kibana_export/'+symbol+'_exports.ndjson'
                if os.path.exists(ndjson_file_path) is False:
                    ndjson_file = open(ndjson_file_path, "xt", encoding='utf-8')
                    final_text = import_template.replace('tmpl',symbol)
                    ndjson_file.write(final_text)
                    ndjson_file.close()

                kibana_import_url = 'http://kibana:5601/api/saved_objects/_import'
                payload = { 'overwrite': 'false'}
                headers ={'kbn-xsrf': 'True'}
                post = requests.post(kibana_import_url, headers=headers, files={'file': ndjson_file_path})
                print("Import %s result" % symbol)
                print(post.text)

            except Exception as e:
                print(e.with_traceback(e.__traceback__));
                pass

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)