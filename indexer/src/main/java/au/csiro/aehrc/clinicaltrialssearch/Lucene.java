package au.csiro.aehrc.clinicaltrialssearch;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.Reader;
import java.nio.file.Paths;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.Fields;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.MultiFields;
import org.apache.lucene.index.Term;
import org.apache.lucene.index.Terms;
import org.apache.lucene.index.TermsEnum;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

public class Lucene {

	public static int processFileOrDirectory(File fileOrDir, int counter, IndexWriter iwriter) throws IOException {

		if (fileOrDir.isDirectory()) {
			for (File file : fileOrDir.listFiles()) {
				counter = processFileOrDirectory(file, counter, iwriter);
			}
		} else {

			System.out.println("Indexing document " + counter);
			counter++;

			Document document = new Document();

			Reader reader = new FileReader(fileOrDir);
			document.add(new Field("contents", reader, TextField.TYPE_NOT_STORED));

			iwriter.addDocument(document);
			reader.close();
		}

		return counter;
	}

	public static void main(String[] args) throws IOException {

		System.out.println("Indexing collection at " + args[0]);

		Analyzer analyzer = new StandardAnalyzer();

		Directory directory = FSDirectory.open(Paths.get("/tmp/testindex"));

		IndexWriterConfig config = new IndexWriterConfig(analyzer);
		IndexWriter iwriter = new IndexWriter(directory, config);

		File dir = new File(args[0]);
		int counter = processFileOrDirectory(dir, 1, iwriter);

		// iwriter.optimize();
		iwriter.close();

		System.out.println("Indexing completed. " + counter + " documents found.");

		System.out.println("Building term stats...");

		// Now search the index:
		IndexReader ireader = DirectoryReader.open(directory);

		Fields fields = MultiFields.getFields(ireader);
		FileWriter output = new FileWriter("lucene.stats");

		for (String field : fields) {

			Terms terms = fields.terms(field);
			TermsEnum termEnum = terms.iterator();

			System.out.println("Writing stats for field " + field + " containg " + terms.size() + " terms.");

			while (termEnum.next() != null) {
				String term = termEnum.term().utf8ToString();
				long ttf = ireader.totalTermFreq(new Term("contents", term));

				output.write(term + " - " + ttf + "\n");
			}

			long T = ireader.getSumTotalTermFreq("contents");
			output.write("*total-terms* - " + T);
		}

		output.close();
		ireader.close();
		directory.close();

		System.out.println("Stats written to 'lucene.stats'.");
	}

}
