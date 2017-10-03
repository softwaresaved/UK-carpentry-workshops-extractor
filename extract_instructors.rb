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

  def self.get_instructors(airports, session_id, csrf_token)

    puts "\n" + "#" * 80 +"\n\n"
    puts "Getting instructors' info, filtered per country via its airports."

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

        airport_iata_codes = airports.map{|airport| airport['iata']} unless airports.nil?
        puts "Looking for instructors with airport codes in " + airport_iata_codes.to_s unless airport_iata_codes.nil?
        # Filter out instructors (people with a non-empty badge field) by country (via a list of airports for a country). If airports is nil - return instructors for all airports/countries.
        all_people.each_with_index do |person, index|

          # To determine people from the UK, check the nearest_airport info, and, failing that, if email address ends in '.ac.uk' - that is our best bet.
          if airports.nil? # Include instructors from all airports/all countries
            instructors << person if !(INSTRUCTOR_BADGES & person['badges']).empty?
          else
            if !(INSTRUCTOR_BADGES & person['badges']).empty?  # The person has any of the instructor badges
              # Get the person airport's IATA code - the 3 characters before the last '/' in the airport field URI
              airport_iata_code = person['airport'].nil? ? nil : person['airport'][person['airport'].length - 4 , 3]
              if airport_iata_code.nil?
                instructors << person  # If airport code is nil then we cannot conclude where the person is from, so we have to include them
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

   # Get all airports for the selected country_code recorded in AMY
  airports = get_airports(options.country_code, session_id, csrf_token)

  # Get all UK instructors recorded in AMY (we have to filter by the airport as it is the nearest airport that appears in people's profiles in AMY)
  instructors = Instructors.get_instructors(airports, session_id, csrf_token)

  Instructors.write_instructors_to_csv(instructors, options.instructors_file) unless instructors.empty?

end
