package au.csiro.aehrc.clinicaltrialssearch;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;


import com.google.code.context.ContextStripper;


import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.XML;


import junit.framework.TestCase;

public class ClinicalDocumentAnalyserTest extends TestCase {

	private static JSONObject testJson;

	public void setUp() throws JSONException, IOException {
		ClassLoader classLoader = getClass().getClassLoader();
		File testClinicalTrial = new File(classLoader.getResource("NCT02058186.xml").getFile());
		testJson = XML.toJSONObject(new String(Files.readAllBytes(testClinicalTrial.toPath())));
	}
	
	public void test_cleanDocument() {
		JSONObject json = ClinicalDocumentAnalyser.cleanDocument(testJson);
		assertEquals(1.0, json.getJSONObject("clinical_study").getJSONObject("eligibility").getDouble("minimum_age"));
		assertEquals(18.0, json.getJSONObject("clinical_study").getJSONObject("eligibility").getDouble("maximum_age"));
	}
	
	public void test_Day() {
		assertEquals(0.0027397260273972603, ClinicalDocumentAnalyser.convertAgeToYears("1 Day", -1.0));
		assertEquals(0.005479452054794521, ClinicalDocumentAnalyser.convertAgeToYears("2 Days", -1.0));
	}
	
	public void test_Months() {	
		assertEquals(0.5, ClinicalDocumentAnalyser.convertAgeToYears("6 Months", -1.0));
		assertEquals(0.5, ClinicalDocumentAnalyser.convertAgeToYears("6 month", -1.0));
		assertEquals(0.5, ClinicalDocumentAnalyser.convertAgeToYears("6month", -1.0));
		
		assertEquals(0.25, ClinicalDocumentAnalyser.convertAgeToYears("3 Months", -1.0));
		assertEquals(0.25, ClinicalDocumentAnalyser.convertAgeToYears("3 month", -1.0));
		assertEquals(0.25, ClinicalDocumentAnalyser.convertAgeToYears("3month", -1.0));
		
		assertEquals(4.916666666666667, ClinicalDocumentAnalyser.convertAgeToYears("59 Months", -1.0));
		
		assertEquals(-1.0, ClinicalDocumentAnalyser.convertAgeToYears("N/A", -1.0));
	}
	
	public void test_Years() {	
		assertEquals(18.0, ClinicalDocumentAnalyser.convertAgeToYears("18 Years", -1.0));
		assertEquals(1.0, ClinicalDocumentAnalyser.convertAgeToYears("1 year", -1.0));
		assertEquals(10.0, ClinicalDocumentAnalyser.convertAgeToYears("10 years", -1.0));
		
		assertEquals(0.0, ClinicalDocumentAnalyser.convertAgeToYears("N/A", 0.0));
	}

	public void test_splitEligibilityCriteria() {
		String crit = "Inclusion Criteria:"
		+ "-  Thoracic surgical patients requiring lung isolation"
		+ "-  Pulmonary resection: lobectomy, segmentectomy"
		+ "-  Esophageal surgery and no pulmonary resection"
		+ "-  Mediastinal surgery and no pulmonary resection"
		+ "Exclusion Criteria:"
		+ "-  Metabolic disorder"
		+ "-  Metabolic syndrome"
		+ "-  Diabetes"
		+ "-  Pregnancy";

	

		assertTrue("Dummy", true);
	}

	public void test_parseEligibility() {
		String crit = "Exclusion Criteria:\r\n\r\n          -  Any medical or psychiatric condition that compromises the subject's ability to\r\n             participate in the study.\r\n\r\n          -  Any other significant disease including liver or renal disease\r\n\r\n          -  Pregnant or lactating women\r\n\r\n          -  Contraindications for MR imaging";

		JSONArray eligibilityList = ClinicalDocumentAnalyser.parseEligibility(crit);
		

		for(Object item : eligibilityList) {
			System.out.println("*" + item);
		}

		System.out.println("  -  Oral Contraceptive, either combined or progestogen alone".replaceAll("\\s+-\\s+", ""));

		assertEquals("Correct number of lines not found.", 5, eligibilityList.length());
	}

	public void test_Context() {
		final String NEGATED = "There is no fever present for this patient.";
		final String AFFIRMED = "Fever present for this patient.";

		ContextStripper context = new ContextStripper();

		assertEquals(AFFIRMED, context.markupNegation(AFFIRMED));
		assertEquals("There is no <negated>fever present for this patient.</negated>", context.markupNegation(NEGATED));
		assertEquals("There is no neg_fever neg_present neg_for neg_this patient.", context.prependNegation(NEGATED));
		
	}

	public static void main(String[] args) throws JSONException, IOException {
		
		new ClinicalDocumentAnalyserTest().test_Context();
		
	}
}
