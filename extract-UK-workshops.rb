#!/usr/bin/env ruby

# Extracts JSON from https://amy.software-carpentry.org/api/v1/events/published/ containing all SWC, DC and TTT workshops
# that went ahead and then extracts those that were held in the UK and saves them to a CSV file.

require 'open-uri'
require 'json'
require 'csv'
require 'fileutils'
require 'nokogiri'

amy_api_published_events_url = "https://amy.software-carpentry.org/api/v1/events/published/"
amy_workshop_events_url = "https://amy.software-carpentry.org/workshops/event"

search_results = []
uk_workshops = []
begin
  # Retrieve results from amy_api_published_events_url
  puts "Quering #{amy_api_published_events_url}"
  search_results = JSON.load(open(amy_api_published_events_url, "Accept" => "application/json"))
rescue Exception => ex
  puts "Failed to get anything out of #{amy_api_published_events_url}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
else
  # Get the workshops in the UK
  uk_workshops = search_results.select{|workshop| workshop["country"] == "GB"}
  puts "Result stats: number of UK workshops = #{uk_workshops.length.to_s}; total number of all workshops = #{search_results.length.to_s}."
end

# Figure out the number of students from AMY records (from table listing people and roles, where role == 'learner') for each of the workshop.
# Accessing pages requires user to be authenticated, hence we use the 'Cookie' header with session info which expires after a while.
# Cookie header looks something like this: "Cookie" => "__utma=2571...; __utmc=257105289; sessionid=cyu3...; _ga=GA1.2...; csrftoken=MrTv..."
# and you can figure one out if you look at what headers your browser sends after you are authenticated with AMY. This is a hackish way of
# doing things but there is no other way to authenticate programatically at the moment. Nor is this info avaiable via the public API.
uk_workshops.each do |workshop|
  begin
    # Replace the Cookie header info with the correct one, if you have access to AMY
    #workshop_html_page = Nokogiri::HTML(open(amy_workshop_events_url + "/" + workshop["slug"], "Cookie" => "__utma=2571...; __utmc=257105289; sessionid=cyu3...; _ga=GA1.2...; csrftoken=MrTv..."))

    if !workshop_html_page.xpath('//title[contains(text(), "Log in")]').empty?
      puts "Failed to get number of attendees for workshop #{workshop["slug"]} from #{amy_workshop_events_url + "/" + workshop["slug"]}. You need to be authenticated to access this page."
      next
    end
    puts "Calculating the number of attendees for workshop #{workshop["slug"]} by parsing #{amy_workshop_events_url + "/" + workshop["slug"]}."
    workshop['number_of_attendees'] = workshop_html_page.xpath('//table/tr/td[contains(text(), "learner")]').length
    puts "Found #{workshop["number_of_attendees"]} attendees for #{workshop["slug"]}."
  rescue Exception => ex
    # Skip to the next workshop
    puts "Failed to get number of attendees for workshop #{workshop["slug"]} from #{amy_workshop_events_url + "/" + workshop["slug"]}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
    next
  end
end

# CSV headers
csv_headers = ["slug", "humandate", "start", "end", "tags", "venue", "address", "latitude", "longitude",
               "number_of_attendees",
               "eventbrite_id", "contact", "url"]

date = Time.now.strftime("%Y-%m-%d")
csv_file = "SWC-DC-TTT-workshops-UK_#{date}.csv"
FileUtils.touch(csv_file) unless File.exist?(csv_file)

begin
  CSV.open(csv_file, 'w',
           :write_headers => true,
           :headers => csv_headers #< column headers
  ) do |csv|
    uk_workshops.each do |workshop|
      csv << [workshop["slug"],
              workshop["humandate"],
              workshop["start"],
              workshop["end"],
              workshop["tags"].map{|x| x["name"]}.join(", "),
              workshop["venue"],
              workshop["address"],
              workshop["latitude"],
              workshop["longitude"],
              workshop["number_of_attendees"],
              workshop["eventbrite_id"],
              workshop["contact"],
              workshop["url"]]
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

