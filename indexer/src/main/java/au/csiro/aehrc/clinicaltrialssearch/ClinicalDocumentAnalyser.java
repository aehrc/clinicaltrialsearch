package au.csiro.aehrc.clinicaltrialssearch;



import com.google.code.context.ContextStripper;

import org.json.JSONArray;
import org.json.JSONObject;

public class ClinicalDocumentAnalyser {

	private static ContextStripper context = new ContextStripper();

	protected static Double convertAgeToYears(String age, Double ageInYears) {

		if (age.toLowerCase().contains("year")) {
			age = age.toLowerCase().replace("year", "").replace("s", "").trim();
			ageInYears = Double.parseDouble(age);
		}
		if (age.toLowerCase().contains("month")) {
			age = age.toLowerCase().replace("month", "").replace("s", "").trim();
			ageInYears = Double.parseDouble(age) / 12;
		}
		if (age.toLowerCase().contains("week")) {
			age = age.toLowerCase().replace("week", "").replace("s", "").trim();
			ageInYears = Double.parseDouble(age) / 52;
		}
		if (age.toLowerCase().contains("day")) {
			age = age.toLowerCase().replace("day", "").replace("s", "").trim();
			ageInYears = Double.parseDouble(age) / 365;
		}
		
		return ageInYears;
	}

	/**
	 * Converts all ages into age in years.
	 */
	public static JSONObject normaliseAge(JSONObject doc) {

		Double minAge = convertAgeToYears(
			doc.getJSONObject("clinical_study").getJSONObject("eligibility").getString("minimum_age"), -1.0);
		Double maxAge = convertAgeToYears(
			doc.getJSONObject("clinical_study").getJSONObject("eligibility").getString("maximum_age"), 150.0);

		doc.getJSONObject("clinical_study").getJSONObject("eligibility").put("minimum_age", minAge);
		doc.getJSONObject("clinical_study").getJSONObject("eligibility").put("maximum_age", maxAge);
		
		return doc;
	}

	/**
	 * Split the eligibility criteria into inclusion & exclusion.
	 * 
	 * @param doc - A json object of the whole document
	 * @return Updated doc split into inclusion & exclusion.
	 */
	protected static JSONObject splitEligibilityCriteria(JSONObject criteria) {
		String inclusion = criteria.getString("textblock");
		criteria.remove("textblock");
		String exclusion = "";

		int begin_exclusion = inclusion.toLowerCase().indexOf("exclusion");
		if(begin_exclusion > -1) {
			exclusion = inclusion.substring(begin_exclusion);
			inclusion.substring(0, begin_exclusion);
			criteria.put("exclusion", parseEligibility(exclusion));
		}
		
		criteria.put("inclusion", parseEligibility(inclusion));
		
		return criteria;
	}

	protected static JSONArray parseEligibility(String eligibilityStr) {
		JSONArray eligibilityArray = new JSONArray();

		/**
		 * Break up based on blank lines
		 */
		String crit = "";
		for(String line : eligibilityStr.split("\n")) {
			if(line.trim().length() == 0) {
				eligibilityArray.put(crit);
				crit = "";
			}
			String str = line.replaceAll("\\s+-\\s+", "").trim();
			crit = crit + " " + str;
		}
		eligibilityArray.put(crit);

		return eligibilityArray;
	}

	public static String prependNegation(String content) {
		return context.prependNegation(content);
	}

	public static JSONObject cleanDocument(JSONObject doc) {
		if (doc.getJSONObject("clinical_study").has("eligibility")) {

			// Age normalisation
			doc = normaliseAge(doc);


			// split criteria
			if (doc.getJSONObject("clinical_study").getJSONObject("eligibility").has("criteria")) {
				JSONObject criteria = doc.getJSONObject("clinical_study").getJSONObject("eligibility").getJSONObject("criteria");
				criteria = splitEligibilityCriteria(criteria);
			}
		}


		return doc;
	}

}
