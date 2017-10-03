#!/usr/bin/env ruby

# Extracts information about Carpentry workshops (per country) from AMY and saves them to a CSV file.

require 'json'
require 'csv'
require 'fileutils'
require 'nokogiri'
require 'date'
require_relative "lib/amy.rb"
require_relative "lib/clp-parser.rb"

VERSION = "1.0.1"

module Workshops

  # Get info on 'published' workshops recorded in AMY, by country_code (or for all countries if country_code == nil or country_code == 'all').
  # 'Published' workshops are those that went ahead or are likely to go ahead (i.e. have country_code, address, start date, end date, latitude and longitude, etc.)
  def self.get_workshops(country_code, session_id, csrf_token)

    all_published_workshops = []  # all workshops in AMY that are considered 'published', i.e. have a venue, location , longitude, latitude, start and end date, etc.
    workshops_by_country = []
    begin
      # Retrieve publicly available workshop details using AMY's public API
      puts "Quering AMY's API at #{AMY_API_PUBLISHED_WORKSHOPS_URL} to get publicly available info for published workshops for country: #{country_code}."
      headers = HEADERS.merge({"Accept" => "application/json"})
      all_published_workshops = JSON.load(open(AMY_API_PUBLISHED_WORKSHOPS_URL, headers))

      # Get the workshops for the selected country_code, or all workshops if country_code == nil or country_code == 'all'
      workshops_by_country = all_published_workshops
      workshops_by_country = all_published_workshops.select{|workshop| workshop["country"] == country_code} unless (country_code.nil? or country_code.downcase == 'all')
      puts "Results: number of workshops for country #{country_code} = #{workshops_by_country.length.to_s}; total number of all workshops = #{all_published_workshops.length.to_s}."

      # Figure out some extra details about the workshops - e.g. the number of instructor attendees and instructors from AMY records - by accessing the UI/HTML page of each instructor - since this info is not available via the public API.
      # To do that, we need to extract the HTML table listing people and their roles (e.g. where role == 'learner' or where role == 'instructor').
      # Accessing these pages requires authentication passing session_id and csrf_token obtained previously.
      get_private_workshop_info(workshops_by_country, session_id, csrf_token) unless (session_id.nil? or csrf_token.nil?)

    rescue Exception => ex
      puts "Failed to get publicly available workshops info using AMY's API at #{AMY_API_PUBLISHED_WORKSHOPS_URL}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
      puts "Backtrace:\n\t#{ex.backtrace.join("\n\t")}"
    end

    return workshops_by_country
  end

  def self.get_private_workshop_info(workshops, session_id, csrf_token)
    workshops.each_with_index do |workshop, index|
      begin
        puts "\n" + "#" * 80 +"\n\n"
        print "Processing workshop no. " + (index+1).to_s + " (#{workshop["slug"]}) from #{AMY_UI_WORKSHOP_BASE_URL + "/" + workshop["slug"]}" + "\n"

        # Add the Cookie header, as access to these pages needs to be authenticated
        headers = HEADERS.merge({"Cookie" => "sessionid=#{session_id}; token=#{csrf_token}"})
        workshop_html_page = Nokogiri::HTML(open(AMY_UI_WORKSHOP_BASE_URL + "/" + workshop["slug"], headers))

        if !workshop_html_page.xpath('//title[contains(text(), "Log in")]').empty?
          puts "Failed to get the HTML page for instructor #{workshop["slug"]} from #{AMY_UI_WORKSHOP_BASE_URL + "/" + workshop["slug"]} to parse it. You need to be authenticated to access this page."
          next
        end

        # Look at the attendance row in the HTML table
        # <tr class=""><td>attendance:</td><td colspan="2">   25   <a href="#" class="btn btn-primary btn-xs pull-right disabled">Ask for attendance</a></td></tr>
        # Note at_xpath method is used as we know there will be one element only
        attendance_number_node = workshop_html_page.at_xpath('//table/tr/td[contains(text(), "attendance:")]/../td[2]') # gets 2nd <td> child of a <tr> node that contains a <td> with the text 'attendance:'

        #workshop['number_of_attendees'] = workshop_html_page.xpath('//table/tr/td[contains(text(), "learner")]').length
        workshop['number_of_attendees'] = attendance_number_node.nil? ? 0 : attendance_number_node.content.slice(0, attendance_number_node.content.index("Ask for attendance")).strip.to_i
        puts "Found #{workshop["number_of_attendees"]} attendees for #{workshop["slug"]}."

        # Get instructors that taught at workshops
        instructors = workshop_html_page.xpath('//table/tr/td[contains(text(), "instructor")]/../td[3]')
        workshop['instructors'] = instructors.map(&:text) # Get text value of all instructor nodes as an array
        workshop['instructors'] += Array.new(10 - workshop['instructors'].length, '')  # append empty strings (if we get less then 10 instructors from AMY) as we have 10 placeholders for instructors and want csv file to be properly aligned
        workshop['instructors'] = workshop['instructors'][0,10] if workshop['instructors'].length > 10 # keep only the first 10 elements (that should be enough to cover all instructors, but just in case), so we can align the csv rows properly later on
        puts "Found #{workshop["instructors"].reject(&:empty?).length} instructors for #{workshop["slug"]}."
      rescue Exception => ex
        # Skip to the next workshop
        puts "Failed to get number of attendees for workshop #{workshop["slug"]} from #{AMY_UI_WORKSHOP_BASE_URL + "/" + workshop["slug"]}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
        puts "Backtrace:\n\t#{ex.backtrace.join("\n\t")}"
        next
      end
    end
  end

  def self.write_workshops_to_csv(workshops, csv_file)

    FileUtils.touch(csv_file) unless File.exist?(csv_file)
    # CSV headers
    csv_headers = ["slug", "humandate", "start", "end", "tags", "venue", "address", "latitude", "longitude", "eventbrite_id", "contact", "url", "number_of_attendees", "instructor_1", "instructor_2", "instructor_3", "instructor_4", "instructor_5", "instructor_6", "instructor_7", "instructor_8", "instructor_9", "instructor_10"]

    begin
      CSV.open(csv_file, 'w',
               :write_headers => true,
               :headers => csv_headers #< column headers
      ) do |csv|
        workshops.each do |workshop|
          csv << ([workshop["slug"],
                   workshop["humandate"],
                   (workshop["start"].nil? || workshop["start"] == '') ? DateTime.now.to_date.strftime("%Y-%m-%d") : workshop["start"],
                   (workshop["end"].nil? || workshop["end"] == '') ? ((workshop["start"].nil? || workshop["start"] == '') ? DateTime.now.to_date.next_day.strftime("%Y-%m-%d") : DateTime.strptime(workshop["start"], "%Y-%m-%d").to_date.next_day.strftime("%Y-%m-%d")) : workshop["end"],
                   workshop["tags"].map{|x| x["name"]}.join(", "),
                   workshop["venue"],
                   workshop["address"],
                   workshop["latitude"],
                   workshop["longitude"],
                   workshop["eventbrite_id"],
                   workshop["contact"],
                   workshop["url"],
                   workshop["number_of_attendees"],
                   workshop["instructors"]]).flatten  # flatten because instructor["instructors"] is an array and we want to concatenate each of its elements
        end
      end
      puts "\n" + "#" * 80 +"\n\n"
      puts "Finished writing workshop data for a total of #{workshops.length.to_s} workshops to file #{csv_file}."
      puts "\n" + "#" * 80 +"\n\n"
    rescue Exception => ex
      puts "\n" + "#" * 80 +"\n\n"
      puts "Failed to get export workshop data into #{csv_file}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
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

  # Get all workshops for the selected country_code recorded in AMY
  workshops = Workshops.get_workshops(options.country_code, session_id, csrf_token)

  Workshops.write_workshops_to_csv(workshops, options.workshops_file) unless workshops.empty?

end
