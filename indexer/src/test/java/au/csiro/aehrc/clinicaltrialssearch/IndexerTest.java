package au.csiro.aehrc.clinicaltrialssearch;

import java.io.File;
import java.io.IOException;
import java.net.HttpURLConnection;

import org.apache.http.HttpResponse;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.HttpClientBuilder;
import org.json.JSONException;
import org.json.JSONObject;

import junit.framework.TestCase;

public class IndexerTest extends TestCase {
	
	ClassLoader classLoader = getClass().getClassLoader();
	File testClinicalTrial = new File(classLoader.getResource("NCT02058186.xml").getFile());
	
	public void testJSONOutput() throws JSONException, IOException {
		JSONObject json = new Indexer().convertXMLtoJSON(testClinicalTrial);
		assertEquals("NCT02058186", json.getJSONObject("clinical_study").getJSONObject("id_info").getString("nct_id"));
	}
	
	public void disabled_testSetUpElasticMappings() throws ClientProtocolException, IOException {
		HttpResponse response = new Indexer().setUpElasticMappings(false);
		assertEquals(HttpURLConnection.HTTP_OK, response.getStatusLine().getStatusCode());
		
		HttpGet get = new HttpGet(Configuration.getElasticIndexURL());
		HttpResponse mappingResponse = HttpClientBuilder.create().build().execute(get);
		
		assertEquals(HttpURLConnection.HTTP_OK, mappingResponse.getStatusLine().getStatusCode());
	}

}
