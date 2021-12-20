package au.csiro.aehrc.clinicaltrialssearch;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.HttpURLConnection;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.cli.BasicParser;
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.apache.http.HttpResponse;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.entity.FileEntity;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.log4j.Logger;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.XML;

import javax.json.Json;

/**
 * Indexes clinical trial documents into Elastic.
 * <p>
 * Clinical trial documents are distributed in a specific XML format (@see
 * https://clinicaltrials.gov/ct2/resources/download).
 * <p>
 * Indexer will do the following:
 * <p>
 * 1. Convert the XML into JSON format. Batches of 1,000 clinical trials will be
 * written to the `json_out` directory.
 * <p>
 * 2. Submit the JSON batches to Elastic.
 */
public class Indexer {

    public static Integer currentId = 1;

    public static void incrementId() {
        currentId++;
    }

    Logger log = Logger.getLogger(Indexer.class.getName());
    private static final String JSON_OUT_DIR = "json_out";

    public Indexer() {

    }

    public void convertCorpusToJSON(File corpusDir) throws JSONException, IOException {
        log.info("Converting " + corpusDir);
        if (!corpusDir.exists()) {
            log.error("corpus does not exist", new FileNotFoundException(corpusDir.getAbsolutePath()));
        }

        new File(JSON_OUT_DIR).mkdir();

        File[] files = corpusDir.listFiles();
        PrintWriter writer = new PrintWriter(JSON_OUT_DIR + "/clinical_trials-0.json", "UTF-8");
        for (int i = 0; i < files.length; i++) {
            if (!files[i].getName().startsWith("NCT") || !files[i].getName().endsWith(".xml.qout")) {
//				continue;
            }

            if (i % 1000 == 0) {
                writer.close();
                writer = new PrintWriter(JSON_OUT_DIR + "/clinical_trials-" + i + ".json", "UTF-8");
            }

            log.info("Processing " + (i + 1) + "/" + files.length + ": " + files[i]);

            JSONObject json = convertXMLtoJSON(files[i]);
            json = cleanJsonContent(json);
            String ISOData = new String(json.toString().getBytes("iso-8859-1"));
            writer.println("{ \"index\" : {\"_id\" : " + currentId + ", \"_type\" : \"trial\" } }");
            writer.println(cleanStringContent(ISOData.toString()));

            incrementId();

        }
        writer.close();
        log.info("Convertion complete.");
    }

    private void indexClinicalTrialsWithElastic(String endPoint) throws ClientProtocolException, IOException {
        File[] jsonFiles = new File(JSON_OUT_DIR).listFiles();
        for (int i = 0; i < jsonFiles.length; i++) {
            log.info("Indexing " + (i + 1) + "/" + jsonFiles.length + " " + jsonFiles[i]);
            postJsonFileToElastic(jsonFiles[i], endPoint);

        }
        log.info("Completed sending " + jsonFiles.length + " files to elastic.");
    }

    private void postJsonFileToElastic(File jsonFile, String endPoint) throws ClientProtocolException, IOException {
        // Preprocessing of inconsistent fields
        List<String> newLines = new ArrayList<String>();
        for (String line : Files.readAllLines(Paths.get(jsonFile.toURI()), StandardCharsets.UTF_8)) {
            String update = line.replaceAll("\"enrollment\":([0-9]+),",
                    "\"enrollment\":{\"type\":\"NA\",\"content\":$1},");
            update = update.replaceAll("\"completion_date\":(\".*\"),",
                    "\"completion_date\":{\"type\":\"NA\",\"content\":$1},");

            newLines.add(update);
        }
        Files.write(Paths.get(jsonFile.toURI()), newLines, StandardCharsets.UTF_8);

        // post to elasticsearch
        HttpPost post = new HttpPost(Configuration.getElasticIndexURL() + "/trial/_bulk");
        post.setEntity(new FileEntity(jsonFile));
        post.addHeader("content-type", "application/x-ndjson");
        post.addHeader("Accept", "text/plain");

        HttpResponse response = HttpClientBuilder.create().build().execute(post);
        if (response.getStatusLine().getStatusCode() != HttpURLConnection.HTTP_OK) {
            log.warn("Error received when indexing " + jsonFile + " "
                    + new BufferedReader(new InputStreamReader(response.getEntity().getContent())).readLine());
        } else {
            log.debug("Index complete for " + jsonFile);
        }

    }

    protected JSONObject convertXMLtoJSON(File file) throws JSONException, IOException {
        JSONObject json = XML.toJSONObject(new String(Files.readAllBytes(file.toPath())));

        return ClinicalDocumentAnalyser.cleanDocument(json);
    }

    public static String cleanStringContent(String content) {
        content = stripCompletionDate(content);
        return content;
    }

    public static JSONObject cleanJsonContent(JSONObject content) {
        if (content.getJSONObject("clinical_study").has("start_date") && content.getJSONObject("clinical_study").get("start_date") instanceof JSONObject) {
			content.getJSONObject("clinical_study").put("start_date", content.getJSONObject("clinical_study").getJSONObject("start_date").getString("content"));
        }
        return content;
    }

    public static String stripCompletionDate(String content) {
        int completionDateIndex = content.indexOf("\"completion_date\"");
        int verificationDateIndex = content.indexOf("\"verification_date\"");
        if (completionDateIndex != -1 && verificationDateIndex != -1) {
            content = content.substring(0, completionDateIndex) + content.substring(verificationDateIndex);
        }
        return content;
    }

    protected HttpResponse setUpElasticMappings() throws ClientProtocolException, IOException {
        return setUpElasticMappings(true);
    }

    protected HttpResponse setUpElasticMappings(boolean askOnExistingMappings)
            throws ClientProtocolException, IOException {

        log.info("Setting up elastic mappings.");
        ClassLoader classLoader = getClass().getClassLoader();
        File mappingFile = new File(classLoader.getResource("elastic_mappings.json").getFile());

        HttpPut put = new HttpPut(Configuration.getElasticIndexURL());
        put.setEntity(new FileEntity(mappingFile));
        put.addHeader("content-type", "application/json");
        put.addHeader("Accept", "*/*");

        HttpResponse response = HttpClientBuilder.create().build().execute(put);

        if (response.getStatusLine().getStatusCode() != HttpURLConnection.HTTP_OK) {
            log.warn("Error on mappings setup: "
                    + new BufferedReader(new InputStreamReader(response.getEntity().getContent())).readLine());

            if (askOnExistingMappings) {
                try {
                    BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
                    String input = "";
                    while (!"y".equals(input) && !"n".equals(input)) {
                        System.out.print("Error on mappings setup. Do you want to continue? [y/n]: ");
                        input = br.readLine().toLowerCase();
                    }
                    if ("n".equals(input)) {
                        System.out.println("Shutting down.");
                        System.exit(0);
                    } else {
                        log.info("Keeping existing mappings and continuing.");
                    }

                } catch (IOException io) {
                    io.printStackTrace();
                }
            }
        } else { // HTTP OK
            log.info("New mappings created.");
        }

        return response;
    }

    public void indexCorpus(File corpusDir) throws JSONException, IOException {

        if (new File(JSON_OUT_DIR).exists()) {
            log.info("Existing conversion detected - uses these.");
        } else {
            convertCorpusToJSON(corpusDir);
        }

        setUpElasticMappings();
        indexClinicalTrialsWithElastic("clinicaltrials");

        log.info("Indexing is complete. Shutting down.");
    }

    public static String usage() {
        return "Usage: indexer <corpus-dir>";
    }

    public static void main(String[] args) throws JSONException, IOException, ParseException, URISyntaxException {

        Options options = new Options();
        options.addOption("e", "elastic", true, "Elastic endpoint.");

        CommandLineParser parser = new BasicParser();
        CommandLine cmd = parser.parse(options, args);


        if (cmd.hasOption("e")) {
            Configuration.setElasticIndexURL(cmd.getOptionValue("e"));
        }

        if (cmd.getArgList().size() > 0) {
            File docsDir = new File(cmd.getArgList().get(0).toString());
            System.out.println("Indexing " + docsDir + " to " + Configuration.getElasticIndexURL());
            new Indexer().indexCorpus(docsDir);
        } else {
            HelpFormatter formatter = new HelpFormatter();
            formatter.printHelp("indexer <corpus>", options);
        }


    }

}
