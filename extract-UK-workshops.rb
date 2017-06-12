#!/usr/bin/env ruby

# Extracts JSON from https://amy.software-carpentry.org/api/v1/events/published/ containing all SWC, DC and TTT workshops
# that went ahead and then extracts those that were held in the UK and saves them to a CSV file.

require 'open-uri'
require 'json'
require 'csv'
require 'fileutils'
require 'nokogiri'
require 'date'

# Public JSON API URL to all workshop events that went ahead (i.e. have country, address, start date, latitude and longitude, etc.)
amy_api_published_workshops_url = "https://amy.software-carpentry.org/api/v1/events/published/"
amy_ui_workshop_base_url = "https://amy.software-carpentry.org/workshops/event"

search_results = []
uk_workshops = []
begin
  # Retrieve results from amy_api_published_workshops_url
  puts "Quering #{amy_api_published_workshops_url}"
  search_results = JSON.load(open(amy_api_published_workshops_url, "Accept" => "application/json"))
rescue Exception => ex
  puts "Failed to get anything out of #{amy_api_published_workshops_url}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
else
  # Get the workshops in the UK
  uk_workshops = search_results.select{|workshop| workshop["country"] == "GB"}
  puts "Result stats: number of UK workshops = #{uk_workshops.length.to_s}; total number of all workshops = #{search_results.length.to_s}."
end

# Figure out the number of workshop attendees from AMY records by accessing the UI/HTML version of each workshop - since this info is not available via the API.
#
# We figure out the number of attendees from the table listing people and roles (where role == 'learner').
#
# Accessing these pages requires authentication, hence we use the 'Cookie' header to pass the session info which expires after a while.
#
# Cookie header looks something like this: "Cookie" => "__utma=2571...; __utmc=257105289; sessionid=cyu3...; _ga=GA1.2...; csrftoken=MrTv..."
# and you can figure one out if you look at what headers your browser sends after you authenticate with AMY. This is a hackish way of
# doing things but there is no other way to authenticate programmaticaly at the moment, nor is this info exposed  via the API.

uk_workshops.each_with_index do |workshop, index|
  begin
    print "######################################################\n"
    print "Processing workshop no. " + (index+1).to_s + " (#{workshop["slug"]}) from #{amy_ui_workshop_base_url + "/" + workshop["slug"]}" + "\n"

    # Replace the Cookie header info with the correct one, if you have access to AMY, as access to these pages needs to be authenticated
    workshop_html_page = Nokogiri::HTML(open(amy_ui_workshop_base_url + "/" + workshop["slug"], "Cookie" => "add-your-own-session-cookie"), nil, "utf-8")

    if !workshop_html_page.xpath('//title[contains(text(), "Log in")]').empty?
      puts "Failed to get the HTML page for workshop #{workshop["slug"]} from #{amy_ui_workshop_base_url + "/" + workshop["slug"]} to parse it. You need to be authenticated to access this page."
      next
    end

    # Look at the attendance row in the HTML table
    # <tr class=""><td>attendance:</td><td colspan="2">   25   <a href="#" class="btn btn-primary btn-xs pull-right disabled">Ask for attendance</a></td></tr>
    # Note at_xpath method is used as we know there will be one element only
    attendance_number_node = workshop_html_page.at_xpath('//table/tr/td[contains(text(), "attendance:")]/../td[2]') # gets 2nd <td> child of a <tr> node that contains a <td> with the text 'attendance:'

    #workshop['number_of_attendees'] = workshop_html_page.xpath('//table/tr/td[contains(text(), "learner")]').length
    workshop['number_of_attendees'] = attendance_number_node.blank? ? 0 : attendance_number_node.content.slice(0, attendance_number_node.content.index("Ask for attendance")).strip.to_i
    puts "Found #{workshop["number_of_attendees"]} attendees for #{workshop["slug"]}."

    instructors = workshop_html_page.xpath('//table/tr/td[contains(text(), "instructor")]/../td[3]')
    workshop['instructors'] = instructors.map(&:text)#.join('|') # Get text value of all instructors and then join with the '|', which seems like a good separator
    workshop['instructors'] += Array.new(10 - workshop['instructors'].length, '')  # append empty strings (if we get less then 10 instructors from AMY) as we have 10 columns for instructors and want csv file to be properly aligned
    workshop['instructors'] = workshop['instructors'][0,10] if workshop['instructors'].length > 10 # keep only the first 10 elements (that should be enough to cover all instructors, but just in case), so we can align the csv rows properly later on
    puts "Found #{workshop["instructors"].reject(&:empty?).length} instructors for #{workshop["slug"]}."
  rescue Exception => ex
    # Skip to the next workshop
    puts "Failed to get number of attendees for workshop #{workshop["slug"]} from #{amy_ui_workshop_base_url + "/" + workshop["slug"]}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
    next
  end
end

# CSV headers
csv_headers = ["slug", "humandate", "start", "end", "tags", "venue", "address", "latitude", "longitude", "eventbrite_id", "contact", "url", "number_of_attendees", "instructor_1", "instructor_2", "instructor_3", "instructor_4", "instructor_5", "instructor_6", "instructor_7", "instructor_8", "instructor_9", "instructor_10"]

date = Time.now.strftime("%Y-%m-%d")
csv_file = "UK-carpentry-workshops_#{date}.csv"
FileUtils.touch(csv_file) unless File.exist?(csv_file)

begin
  CSV.open(csv_file, 'w',
           :write_headers => true,
           :headers => csv_headers #< column headers
  ) do |csv|
    uk_workshops.each do |workshop|
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
               workshop["instructors"]]).flatten  # flatten because workshop["instructors"] is an array and we want to concatenate each of its elements
    end
  end
  puts "\n" + "#" * 80 +"\n\n"
  puts "Finished writing workshop data into #{csv_file}."
  puts "Wrote a total of " + uk_workshops.length.to_s + " UK workshops."
  puts "\n" + "#" * 80 +"\n\n"
rescue Exception => ex
  puts "\n" + "#" * 80 +"\n\n"
  puts "Failed to get export workshop data into #{csv_file}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
end

