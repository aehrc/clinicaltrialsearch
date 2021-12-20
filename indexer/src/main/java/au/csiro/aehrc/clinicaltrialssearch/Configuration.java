package au.csiro.aehrc.clinicaltrialssearch;

import java.util.Properties;

import org.apache.log4j.Logger;

public class Configuration {

	private static Logger log = Logger.getLogger(Configuration.class.getName());

	// default prop file
	private static final String PROPERTIES_FILE = "indexer.properties";

	// where properties are stored
	private static Properties properties;

	static {
		loadProperties();
	}

	/**
	 * Read the PROPERTIES_FILE off the classpath.
	 */
	private static void loadProperties() {

		// load properties from classpath
		properties = new Properties();
		try {
			properties.load(Configuration.class.getClassLoader().getResourceAsStream(PROPERTIES_FILE));
			log.info("Loaded configuration values from " + PROPERTIES_FILE);
		} catch (Exception e) {
			log.fatal("Configuration file not found, please ensure " + "there is a '" + PROPERTIES_FILE
					+ "' on the classpath" + e);
		}

		// override any properties that were specified on the command line
		properties.putAll(System.getProperties());
	}

	public static String getElasticIndexURL() {
		return properties.getProperty("elastic.index.url", "http://localhost:9200/clinicaltrials");
	}

	public static void setElasticIndexURL(String value) {
		properties.setProperty("elastic.index.url", value);
	}

}
