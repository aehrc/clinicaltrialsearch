#!/usr/bin/env python

import sys, glob, multiprocessing, logging, re, os, argparse, csv, sqlite3

import multiprocessing
from threading import Thread

from operator import itemgetter
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

class Annotator:
    
    def __init__(self, index_loc, output_db):
        self.output_db = output_db
        import quickumls
        
        logging.info("Performing setup tasks.")
        self.semtasks, self.semtypes = self.build_semantic_types()
        self.output_db = output_db
        self.setup_db(output_db)

        logging.info("Loading QuickUMLS from " + index_loc)
        self.matcher = quickumls.QuickUMLS(index_loc)
        

    def setup_db(self, output_db):
    
        if not os.path.exists(output_db):
            sql_conn = sqlite3.connect(output_db)
            sql_cursor = sql_conn.cursor()
            sql_cursor.execute('''CREATE TABLE concepts
                        (doc text, start integer, end integer, ngram text, cui ngram, similarity real, semtype text, task text, label text)''')
            logging.info('Created new db {}'.format(output_db))
        else:
            logging.info('Using existing db {}'.format(output_db))
    
        sql_conn.commit()
        sql_conn.close()
        
    def build_semantic_types(self):
        semtasks = {}
        with open('{}/cui_semantic_types.txt'.format(os.path.dirname(os.path.realpath(__file__)))) as fh:
            for line in fh:
                source,cui,name,semtype,task = line.strip().split('|')
                semtasks[cui] = task.replace(" ","")

        semtypes = {}
        with open('{}/sem_types.csv'.format(os.path.dirname(os.path.realpath(__file__)))) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                semtypes[row[0]] = row[1]
        
        return semtasks, semtypes
    
    def extract_section(self, text_content, tag):
        start = text_content.find("<%s>" % tag)
        logging.debug("Looking for <%s>: %d" % (tag,start) )
        if start > -1:
            start = start+len("<%s>" % tag) # ignore the <tag>
            end = text_content.find("</%s>" % tag)
            return start, text_content[start:end]
        else:
            return -1, None
        
    def write_to_db(self, sql_conn, **concept):
        sql_cursor = sql_conn.cursor()
        sql_cursor.execute("INSERT INTO concepts VALUES ('{doc}',{start},{end},'{ngram}','{cui}', {similarity}, '{semtype}', '{task}', '{label}')".format(**concept))

    def process_doc(self, doc, sql_conn):

        indoc = open(doc)
        text_content = indoc.read()
        
        
        for section in ["brief_summary", "detailed_description", "eligibility", "primary_outcome", "secondary_outcome", "keywords"]: 
            
            offset, text = self.extract_section(text_content, section)
            
            if text == None:
                continue
            cleaned_text = text

            # strip child tags
            for tag in re.findall('(</?[a-zA-Z]+[^>]*?>)', cleaned_text):
                cleaned_text = cleaned_text.replace(tag, " "*len(tag))

            try:
                for phrase in self.matcher.match(cleaned_text, best_match=True, ignore_syntax=False):
                    logging.debug("\tP: %s" % phrase)
                    best_match_concept = sorted(phrase, key=itemgetter('similarity'), reverse=True)[0]
                    
                    best_match_concept["doc"] = doc
                    best_match_concept["start"] = int(best_match_concept["start"]+offset)
                    best_match_concept["end"] = int(best_match_concept["end"]+offset)
                    best_match_concept["task"] = self.semtasks.get(best_match_concept['cui'], 'Other')
                    best_match_concept["semtype"] = self.semtypes.get(best_match_concept['semtypes'].pop(), 'N/A')
                    best_match_concept["label"] = re.sub('[^A-Za-z0-9 ]' ,'', best_match_concept['term'])
                    
                    self.write_to_db(sql_conn, **best_match_concept)
                    
            except KeyError:
                #print('Got key error on ' + cleaned_text)
               pass 
        indoc.close()
    

    def para_process_docs(self, id, docs):
        print("Starting thread {} with {} files".format(id, len(docs)))
        sql_conn = sqlite3.connect(self.output_db)
        for count, doc in enumerate(docs):
            print("Process {}: {} ({}/{})".format(id, doc, count, len(docs)))
            self.process_doc(doc, sql_conn)
        sql_conn.commit()
        sql_conn.close()

    def process_dir(self, location, num_procs=multiprocessing.cpu_count()):
        
        docs = glob.glob('%s/*.xml' % location)
        inc = int(len(docs) / num_procs)
        sub_files = [docs[i:i+inc] for i in range(0, len(docs), inc) if os.path.isfile(docs[i]) and not docs[i].startswith("thread_")]
        
        for (count, f) in enumerate(sub_files):
            try:
                Thread(target=self.para_process_docs, args=(count, f)).start()
            except Exception as errtxt:
                print(errtxt)
                

         
        print("Finsihed process %d docs." % len(docs))


if __name__ == '__main__':    

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description="Take Medline XML docs and annotates UMLS concepts.")
    parser.add_argument('-q', '--quickumls_directory', help="Location of quickumls index.", default='/Users/koo01a/tools/quickumls-data')
    parser.add_argument('-d', '--directory', help="Directory of Medline docs to process.")
    parser.add_argument('-n', '--num_procs', help="Number of paralell process to use when processing a directory.", type=int, default=multiprocessing.cpu_count())
    parser.add_argument('-f', '--file', help="Single Medline doc to process.")
    parser.add_argument('-o', '--output_db', help="DB to write output to.", required=True)
    
    args = parser.parse_args()
    
    if not args.output_db:
        args.output_db = args.directory
        
    
    if args.directory:
        Annotator(args.quickumls_directory, args.output_db).process_dir(args.directory, args.num_procs)
    elif args.file:
        Annotator(args.quickumls_directory, args.output_db).process_doc(args.file)
    else:
        parser.print_help()
    
	#process_dir(sys.argv[1])

