# Interaction with Carpentries system AMY

require 'yaml'
require 'open-uri'
require 'json'

# Public JSON API URL to all 'published' instructor events that went or will go ahead (i.e. have country_code, address, start date, latitude and longitude, etc.)
AMY_API_PUBLISHED_WORKSHOPS_URL = "https://amy.software-carpentry.org/api/v1/events/published/"

# Private JSON API URL for all people that have a profile (but not necessarily an account) in AMY
AMY_API_ALL_PERSONS_URL = "https://amy.software-carpentry.org/api/v1/persons/"

# Private JSON API for getting all airports and their countries registered in AMY
AMY_API_ALL_AIRPORTS_URL = "https://amy.software-carpentry.org/api/v1/airports/"

AMY_UI_WORKSHOP_BASE_URL = "https://amy.software-carpentry.org/workshops/event"  # AMY_UI_WORKSHOP_BASE_URL/id gets the workshop id's page in HTML
AMY_UI_PERSON_BASE_URL = "https://amy.software-carpentry.org/workshops/person"  # AMY_UI_PERSON_BASE_URL/id gets the person id's page in HTML

# YAML config file with username/password to login to AMY (to be used if credentials are not passed as command line arguments)
AMY_LOGIN_CONF_FILE =  'amy_login.yml'

# All airports form AMY are serialised as JSON to this file
#AIRPORTS_FILE = 'airports.json'

# AMY login URL - for authenticated access, go to this URL first to authenticate and obtain sessionid and csrf_token for subsequent requests
AMY_LOGIN_URL = "https://amy.software-carpentry.org/account/login/"
HEADERS = {
    "User-Agent" => "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Accept" => "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language" => "en-GB,en;q=0.5"
}

# Types of instructor badges in AMY
INSTRUCTOR_BADGES = ["swc-instructor", "dc-instructor", "trainer"]

COUNTRIES_FILE = File.dirname(__FILE__) + "/countries.json"

# Additional US top-level domains
ADDITIONAL_US_DOMAINS = [".edu", ".gov"]

# Authenticate with AMY using username and password.
# Returns (session_id, csrf_token) that can be reused for the duration of session.
def authenticate_with_amy(username = nil, password = nil)

  # Authentication with AMY involves mimicking the UI form authentication (i.e. mimic what is happening in the UI), since basic authN is not supported.
  # We first need to retrieve csrf_token passed to the client by the server (so we do an initial GET AMY_LOGIN_URL), then POST the csrf_token back alongside username and password (and also pass the csrf_token in headers).
  # In return, we get the session_id and the same csrf_token. We use these two for all subsequent calls to private pages and pass them in headers.
  if username.nil? and password.nil?
    if File.exist?(AMY_LOGIN_CONF_FILE)
      amy_login = YAML.load_file(AMY_LOGIN_CONF_FILE)
      username = amy_login['amy_login']['username']
      password  = amy_login['amy_login']['password']
    else
      puts "Failed to load AMY login details from #{AMY_LOGIN_CONF_FILE}: file does not exist."
      return nil, nil
    end
  end

  if username.nil? or password.nil?
    puts "Username or password are blank - cannot authenticate with AMY."
    return nil, nil
  else
    begin
      csrf_token = open(AMY_LOGIN_URL).meta['set-cookie'].scan(/csrftoken=([^;]+)/)[0][0]
      puts "Obtained csrf_token from AMY."

      amy_login_url = URI.parse(AMY_LOGIN_URL)
      headers = HEADERS.merge({
                                  "Referer" => AMY_LOGIN_URL,
                                  "Cookie" => "csrftoken=#{csrf_token}"
                              })

      http = Net::HTTP.new(amy_login_url.host, amy_login_url.port)
      http.use_ssl = true

      request = Net::HTTP::Post.new(amy_login_url.request_uri, headers)
      request.set_form_data("username" => username, "password" => password, "csrfmiddlewaretoken" => csrf_token)

      response = http.request(request)

      session_id = response['set-cookie'].scan(/sessionid=([^;]+)/)[0][0]
      puts "Obtained session_id from AMY."

      return session_id, csrf_token

    rescue Exception => ex
      puts "Failed to authenticate with AMY. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
      puts "Backtrace:\n\t#{ex.backtrace.join("\n\t")}"
      return nil, nil
    end
  end
end

# Get airports for country registered in AMY using AMY's API
def get_airports(country_code, session_id, csrf_token)
  puts "\n" + "#" * 80 +"\n\n"
  puts "Getting airport info so we can filter instructors per country."

  all_airports = []
  airports_by_country = []

  if session_id.nil? or csrf_token.nil?
    puts "session_id or csrf_token are blank - cannot authenticate with AMY system to access #{AMY_API_ALL_AIRPORTS_URL}."
  else
    begin
      # # Check if we already have the airports saved to a local file
      # if File.exists?(AIRPORTS_FILE)
      #   # Read airports from the file
      #   puts "Loading airport info saved to file #{AIRPORTS_FILE} at an earlier run."
      #   all_airports = JSON.parse(File.read(AIRPORTS_FILE))
      # else
      # Retrieve info about all airports available via AMY's API
      puts "Quering AMY's API at #{AMY_API_ALL_AIRPORTS_URL} to get info on airports in country: #{country_code}."
      headers = HEADERS.merge({"Accept" => "application/json", "Cookie" => "sessionid=#{session_id}; token=#{csrf_token}"})

      json = JSON.load(open(AMY_API_ALL_AIRPORTS_URL, headers))
      all_airports = json["results"]
      # Results are paged so we need to do a few more queries to get all the results back
      next_page = json["next"]
      while !next_page.nil?
        puts "Querying " + next_page
        json = JSON.load(open(next_page, headers))
        all_airports += json["results"]
        next_page = json["next"]
      end

      airports_by_country = all_airports
      airports_by_country = all_airports.select{|airport| airport["country"] == country_code} unless (country_code.nil? or country_code == 'all')

        # # Save all airports to a file for future use
        # File.open(AIRPORTS_FILE,"w") do |f|
        #   f.write( JSON.pretty_generate(all_airports))
        # end
        # end
    rescue Exception => ex
      puts "Failed to get airports info using AMY's API at #{AMY_API_ALL_AIRPORTS_URL}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
      puts "Backtrace:\n\t#{ex.backtrace.join("\n\t")}"
    end
  end
  return airports_by_country
end

# Read top level domains for countries into an array of hashes which keys are 2-letter country codes and values are arrays of TLDs,
# e.g. [{"GB" => [".uk"]}, {"US" => [".gov", ".edu", ".us"]}, ...].
def get_top_level_domains
  tlds = []
  begin
    countries_file = File.read(COUNTRIES_FILE)
    countries = JSON.parse(countries_file)
    tlds = countries.map{ |country| country['cca2'] == "US" ? {country['cca2'] => country['tld'].concat(ADDITIONAL_US_DOMAINS)} : {country['cca2'] => country['tld']} }
  rescue Exception => ex
    puts "Failed to read countries and their top level domains from #{File.absolute_path(COUNTRIES_FILE)}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
    puts "Backtrace:\n\t#{ex.backtrace.join("\n\t")}"
  end
  return tlds
end