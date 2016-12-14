#!/usr/bin/env ruby

# Extracts JSON from https://amy.software-carpentry.org/api/v1/events/published/ containing all SWC, DC and TTT workshops
# that went ahead and then extracts those that were held in the UK and saves them to a CSV file.

require 'open-uri'
require 'json'
require 'csv'
require 'fileutils'

amy_api_published_events_url = "https://amy.software-carpentry.org/api/v1/events/published/"

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

# CSV headers
csv_headers = ["slug", "humandate", "start", "end", "tags", "address", "url"]

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
              workshop["address"],
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

