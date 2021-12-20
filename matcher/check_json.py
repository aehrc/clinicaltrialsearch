import json
import glob
import sys
from tqdm import tqdm

    
def check_json(json_file):
 
    with open(json_file) as fh:
        ok, fail = 0, 0
        for count, line in enumerate(fh):
            if not line.startswith('{ "index" : {"_id" : 1'):
                try:
                    json.loads(line)
                    ok += 1
                except:
                    print(json_file, count+1)
                    fail += 1
    #print('ok={}; fail={}'.format(ok, fail))
    return ok, fail

    
def main():
    total_ok, total_fail = 0, 0
    for json_file in tqdm(glob.glob('../indexer/json_out/*.json')):
        ok, fail = check_json(json_file)
        total_fail += fail
        total_ok += ok
    print('ok={}; fail={}. Pass rate={:.4f}'.format(total_ok, total_fail, 1-(total_fail/(total_fail+total_ok))), file=sys.stderr)
        
main()
