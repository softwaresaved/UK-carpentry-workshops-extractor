#!/usr/bin/env ruby

# Extracts information about Carpentry instructors (per country) from AMY and saves them to a CSV file.

require 'json'
require 'csv'
require 'fileutils'
require 'date'
require_relative "lib/amy.rb"
require_relative "lib/clp-parser.rb"

VERSION = "1.0.1"

module Instructors

  def self.get_instructors(country_code, session_id, csrf_token)

    puts "\n" + "#" * 80 +"\n\n"
    puts "Getting instructors' info from AMY, filtered per country via its airports. Country we are looking for: #{country_code}. \n"
    puts "\n" + "#" * 80 +"\n\n"

    instructors = []

    if session_id.nil? or csrf_token.nil?
      puts "session_id or csrf_token are blank - cannot authenticate with AMY system to access #{AMY_API_ALL_PERSONS_URL}."
    else
      begin
        # Retrieve a list of all people that have a profile in AMY
        puts "Quering AMY's API at #{AMY_API_ALL_PERSONS_URL} to get available info on all registered people."
        headers = HEADERS.merge({"Accept" => "application/json", "Cookie" => "sessionid=#{session_id}; token=#{csrf_token}"})
        json = JSON.load(open(AMY_API_ALL_PERSONS_URL, headers))
        all_people = json["results"]
        # Results are paged so we need to do a few more queries to get all the results back
        next_page = json["next"]
        while !next_page.nil?
          puts "Querying " + next_page
          json = JSON.load(open(next_page, headers))
          all_people += json["results"]
          next_page = json["next"]
        end

        # Unless we are looking for instructors in all countries -
        # - get all airports for the selected country_code recorded in AMY, and
        # - get all top level domains for that country.
        begin

          airports = get_airports(country_code, session_id, csrf_token)
          airport_iata_codes = airports.map{|airport| airport['iata']}
          puts "Airport codes for #{country_code}: " + airport_iata_codes.to_s

          # Get top level domains for the country
          tlds_for_countries = get_top_level_domains_for_countries
          country_tlds = tlds_for_countries.map{ |country| country["tld"] if country["country_code"] == country_code}.compact.flatten
          all_other_tlds = tlds_for_countries.map{ |country| country["tld"] if country["country_code"] != country_code}.compact.flatten
          puts "Top level domains for #{country_code}: " + country_tlds.to_s
          puts "All other top level domains: " + all_other_tlds.to_s
          puts "\n" + "#" * 80 +"\n\n"

        end unless country_code.downcase == "all"

        # Filter out instructors (people with a non-empty badge field) by country (via a list of airports for a country).
        all_people.each_with_index do |person, index|

          if country_code.downcase == "all" # Include instructors from all countries

            instructors << person if !(INSTRUCTOR_BADGES & person['badges']).empty?

          else # Look for instructors from a specific country

            if !(INSTRUCTOR_BADGES & person['badges']).empty?  # Has the person got any of the instructor badges?

              # Get the person airport's IATA code - the 3 characters before the last '/' in the airport field URI
              airport_iata_code = person['airport'].nil? ? nil : person['airport'][person['airport'].length - 4 , 3]

              # If airport code is nil then we cannot conclude where the person is from,
              # so we look up their email address to see if we can determine the country from top level domain name
              if airport_iata_code.nil?
                if (person["email"].nil? or person["email"] == "") # We cannot conclude anything, the person does not have an email address recorded so we include this person
                  instructors << person
                else
                  email_tld = ".#{person["email"].split('.').last}" # Everything after the last ".", including the "."

                  # If instructors email address domain belongs to the country we are searching for then include them.
                  # If they belong to any other country other than the one we are looking for - then exclude them.
                  # If we cannot conclude anything from the email domain (e.g. .com) - we have to include this person as we
                  # simply cannot know if the person belongs to a country or not.
                  if (country_tlds.include?(email_tld)) # We know for sure the person is from the country we are looking for
                    # Include this person
                    person["country_code"] = country_code # At least record the country
                    instructors << person
                  elsif (all_other_tlds.include?(email_tld)) # We know for sure the person is from a different country
                    # Exclude this person
                  else # We cannot conclude anything
                    # Still include this person
                    instructors << person
                  end
                end
              elsif airport_iata_codes.include?(airport_iata_code)
                # Get the airport details based on the IATA code from person's profile
                airport = airport_iata_code.nil? ? nil : airports.select{|airport| airport["iata"] == airport_iata_code}[0]
                person["airport_iata_code"] = airport_iata_code
                person["airport_name"] = airport_iata_code.nil? ? nil : airport["fullname"]
                person["country_code"] = airport_iata_code.nil? ? nil : airport["country"]
                instructors << person
              end
            end
          end
        end

        puts "The following instructors have no information on nearest airport and country and should be fixed in AMY:\n"
        instructors_with_no_country = instructors.select{|person| person["airport_iata_code"] == nil and person["country_code"] == nil}
        puts "None\n" if instructors_with_no_country.empty?
        instructors_with_no_country.each do |person|
          puts "#{person['personal']} #{person['family']} #{person['email']}"
        end

        puts "\nThe following instructors have the country inferred from the top level domain in email address and should be fixed in AMY:\n"
        instructors_with_country_from_email_tld = instructors.select{|person| person["airport_iata_code"] == nil and person["country_code"] != nil}
        puts "None\n" if instructors_with_country_from_email_tld.empty?
        instructors_with_country_from_email_tld.each do |person|
          puts "#{person['personal']} #{person['family']} #{person['email']}"
        end

        puts "\n" + "#" * 80 +"\n\n"

        #sleep(3700);

        # Get extra info about taught workshops and instructor badges awarded for each of the filtered out instructors
        instructors.each do |instructor|

          headers = HEADERS.merge({"Accept" => "application/json", "Cookie" => "sessionid=#{session_id}; token=#{csrf_token}"})

          # Workshops taught by the instructor
          tasks_url = instructor["tasks"]
          puts "Quering AMY's persons API at #{tasks_url} to get extra information on taught workshops for instructor #{instructor["personal"]} #{instructor["family"]}."
          tasks = JSON.load(open(tasks_url, headers))
          # Find all the tasks where the role was "instructor" then find that event's slug
          workshops_taught = tasks.map do |task|
            if task["role"] == "instructor"
              event_url = task["event"] # Events URL in AMY's API (contains slug), e.g. "https://amy.software-carpentry.org/api/v1/events/2013-09-21-uwaterloo/"
              event_url.scan(/([^\/]*)\//).last.first  # Find/emit event's slug - find all matching strings up to '/'
            end
          end.compact  # compact to eliminate nil values
          instructor["workshops_taught"] = workshops_taught
          instructor["number_of_workshops_taught"] = workshops_taught.length

          # Instructor badges awarded
          awards_url = instructor["awards"]
          puts "Quering AMY's persons API at #{awards_url} to get extra information on instructor badges awarded for instructor #{instructor["personal"]} #{instructor["family"]}."
          awards = JSON.load(open(awards_url, headers))
          # Find all the awards for this instructor
          awards.map do |award|
            if INSTRUCTOR_BADGES.include? award["badge"]
              instructor["#{award['badge']}-badge-awarded"] = award["awarded"] # date awarded
            end
          end

        end
      rescue Exception => ex
        puts "Failed to get instructors using AMY's API at #{AMY_API_ALL_PERSONS_URL}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
        puts "Backtrace:\n\t#{ex.backtrace.join("\n\t")}"
      end
    end

    return instructors
  end

  def self.write_instructors_to_csv(instructors, csv_file)

    FileUtils.touch(csv_file) unless File.exist?(csv_file)
    # CSV headers
    csv_headers = ["name", "surname", "email", "amy_username", "country_code", "nearest_airport_name", "nearest_airport_code", "affiliation", "domains",
                   "instructor-badges", "swc-instructor-badge-awarded", "dc-instructor-badge-awarded", "trainer-badge-awarded", "earliest-badge-awarded",
                   "lessons", "number_of_workshops_taught", "workshops_taught"]

    begin
      CSV.open(csv_file, 'w',
               :write_headers => true,
               :headers => csv_headers #< column headers
      ) do |csv|
        instructors.each do |instructor|

          date_array = [instructor["swc-instructor-badge-awarded"], instructor["dc-instructor-badge-awarded"], instructor["trainer-badge-awarded"]].compact.map{ |award_date| Date.parse(award_date) }
          earliest_badge_awarded = date_array.min

          csv << ([instructor["personal"],
                   instructor["family"],
                   instructor["email"],
                   instructor["username"],
                   instructor["country_code"],
                   instructor['airport_name'],
                   instructor["airport_iata_code"],
                   instructor["affiliation"],
                   instructor["domains"],
                   instructor["badges"],
                   instructor["swc-instructor-badge-awarded"],
                   instructor["dc-instructor-badge-awarded"],
                   instructor["trainer-badge-awarded"],
                   earliest_badge_awarded,
                   instructor["lessons"],
                   instructor["number_of_workshops_taught"],
                   instructor["workshops_taught"]])
        end
      end
      puts "\n" + "#" * 80 +"\n\n"
      puts "Finished writing instructor data for a total of #{instructors.length.to_s} instructors to file #{csv_file}."
      puts "\n" + "#" * 80 +"\n\n"
    rescue Exception => ex
      puts "\n" + "#" * 80 +"\n\n"
      puts "Failed to get export instructor data into #{csv_file}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
      puts "Backtrace:\n\t#{ex.backtrace.join("\n\t")}"
    end
  end

end

# Main script body
if __FILE__ == $0 then

  # parse command line parameters
  options = parse(ARGV)

  # Accessing certain private pages requires authentication and obtaining session_id and csrf_token for subsequent calls.
  session_id, csrf_token = authenticate_with_amy(options.username, options.password)

  # Get all instructors for a country (or all countries) recorded in AMY.
  # To do so, we have get all airports for a country and then look up if the nearest airport field in a person's AMY profile falls in that list - that is how we can determine
  # if someone is from a certain country (AMY just does not record the country of origin on its own but it can be determined via the nearest airport).
  instructors = Instructors.get_instructors(options.country_code, session_id, csrf_token)

  Instructors.write_instructors_to_csv(instructors, options.instructors_file) unless instructors.empty?

end
