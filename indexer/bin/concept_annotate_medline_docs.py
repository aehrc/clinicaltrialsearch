#!/usr/bin/env python

import sys, glob, multiprocessing, logging, re, os, argparse, csv

import multiprocessing
from threading import Thread

from operator import itemgetter
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

class Annotator:
    
    def __init__(self, index_loc, output_directory):
        self.output_directory = output_directory
        import quickumls
        logging.info("Loading QuickUMLS from " + index_loc)
        self.matcher = quickumls.QuickUMLS(index_loc)
        self.semtasks, self.semtypes = self.build_semantic_types()
        
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
        
        
    def process_doc_list(self, doc):
        if os.path.isfile('{}/{}.qout'.format(self.output_directory, os.path.basename(doc))):
            print("%s.qout already exists - ignoring" % doc)
            return ""

        indoc = open(doc)
        text_content = indoc.read()
        
        
        
        for section in ["brief_summary", "detailed_description", "eligibility", "primary_outcome", "secondary_outcome", "keywords"]: 
            
            offset, text = self.extract_section(text_content, section)
            
            annotations = {'Diagnosis': [], 'Test': [], 'Treatment': [], 'Other': []}
            
            if text == None:
                continue
            cleaned_text = text

            # strip child tags
            for tag in re.findall('(</?[a-zA-Z]+[^>]*?>)', cleaned_text):
                cleaned_text = cleaned_text.replace(tag, " "*len(tag))

            cuis = []
            try:
                for phrase in self.matcher.match(cleaned_text, best_match=True, ignore_syntax=False):
                    logging.debug("\tP: %s" % phrase)
                    best_match = sorted(phrase, key=itemgetter('similarity'), reverse=True)[0]
                    best_match["start"] = int(best_match["start"]+offset)
                    best_match["end"] = int(best_match["end"]+offset)
                    
                    if best_match['cui'] not in cuis: # avoid dup. cuis
                        tag = self.semtasks.get(best_match['cui'], 'Other')
                        semtype = self.semtypes.get(best_match['semtypes'].pop(), 'N/A')
                        label = re.sub('[^A-Za-z0-9 ]' ,'', best_match['term'])
                        
                        annotation = "<{}><cui>{}</cui><name>{}</name><semtype>{}</semtype></{}>".format(tag, best_match['cui'], label, semtype, tag)
                        text_content = text_content[:offset] + annotation + text_content[offset:]    
                        
                        cuis.append(best_match['cui'])
            except KeyError:
                #print('Got key error on ' + cleaned_text)
               pass 
        indoc.close()

        outdoc = open('{}/{}.qout'.format(self.output_directory, os.path.basename(doc)), 'w')
        outdoc.write("\n"+text_content+"\n")
        outdoc.close()
    

    def process_doc_inline(self, doc):
        
        if os.path.isfile("%s.qout" % doc):
            #print("%s.qout already exists - ignoring" % doc)
            return ""

        indoc = open(doc)

        results = []
        text_content = indoc.read()
        
        for section in ["brief_summary", "detailed_description", "eligibility", "primary_outcome", "secondary_outcome"]: 

            offset, text = self.extract_section(text_content, section)
            
            if text == None:
                continue
            cleaned_text = text
            for tag in re.findall('(</?[a-zA-Z]+[^>]*?>)', cleaned_text):
                cleaned_text = cleaned_text.replace(tag, " "*len(tag))

            try:
                for phrase in self.matcher.match(cleaned_text, best_match=True, ignore_syntax=False):
                    logging.debug("\tP: %s" % phrase)
                    best_match = sorted(phrase, key=itemgetter('similarity'), reverse=True)[0]
                    best_match["start"] = int(best_match["start"]+offset)
                    best_match["end"] = int(best_match["end"]+offset)
                    results.append(best_match)
            except KeyError:
                pass

        indoc.close()

        outdoc = open('%s.qout' % doc, 'w')

        offset = 0
        if len(results) > 0:
                
            for concept in sorted(results, key=itemgetter('start')):
                start = int(concept['start']) + offset
                end = (concept['end']) + offset
                similarity = int(float(concept['similarity'])*1000)
                
                tag = self.semtypes.get(concept['cui'], 'Other')
                
                text_content = text_content[:start] \
                    + '<' + tag + '>' \
                    + text_content[start:end] \
                    + '</' + tag + '>' \
                    + text_content[end:]
                
                
                offset += 2*len(tag)+len("<></>")
                
            outdoc.write(text_content)
        else:
            print("No concepts found in relevant section of", doc)

        outdoc.close()


    def para_process_docs(self, id, docs):
        print("Starting thread {} with {} files".format(id, len(docs)))
        for count, doc in enumerate(docs):
            print("Process {}: {} ({}/{})".format(id, doc, count, len(docs)))
            self.process_doc_list(doc)

    def process_dir(self, location, num_procs=multiprocessing.cpu_count()):
        
        docs = glob.glob('%s/*/N*.xml' % location)
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
    parser.add_argument('-o', '--output_directory', help="Directory to write output to.", required=False)
    
    args = parser.parse_args()
    
    if not args.output_directory:
        args.output_directory = args.directory
        
    
    if args.directory:
        Annotator(args.quickumls_directory, args.output_directory).process_dir(args.directory, args.num_procs)
    elif args.file:
        Annotator(args.quickumls_directory, args.output_directory).process_doc_list(args.file)
    else:
        parser.print_help()
    
	#process_dir(sys.argv[1])

