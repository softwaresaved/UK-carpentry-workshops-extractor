#!/usr/bin/env ruby

# Extracts JSON from https://amy.software-carpentry.org/api/v1/events/published/ containing all SWC, DC and TTT workshops
# that went ahead and then extracts those that were held in the UK and saves them to a CSV file.

#require 'open-uri'
#require 'openssl'
require 'yaml'
require 'json'
require 'csv'
require 'fileutils'
require 'nokogiri'
require 'date'

require 'httparty'

# Public JSON API URL to all workshop events that went ahead (i.e. have country, address, start date, latitude and longitude, etc.)
amy_api_published_workshops_url = "https://amy.software-carpentry.org/api/v1/events/published/"
amy_ui_workshop_base_url = "https://amy.software-carpentry.org/workshops/event"

def authenticate_with_amy
  # AMY login URL - for authenticated access, go to this URL first to authenticate and obtain sessionid and csrftoken for subsequent requests
  amy_login_url = "https://amy.software-carpentry.org/account/login/"

  # Authentication with AMY involves mimicing the UI form authentication (i.e. mimic what is happening in the UI), since basic authN is not supported.
  # We first need to retrieve csrftoken passed to the client by the server (so we do an initial get amy_login_url), then post the csrftoken back alongside username and password (and also pass the csrftoken in headers).
  # In return we expect a session_id and the same csrftoken. We use these two for all subsequent calls to private pages and pass them in headers.

  amy_login_conf_file =  'amy_login.yml'

  if File.exist?(amy_login_conf_file)
    amy_login = YAML.load_file(amy_login_conf_file)
    begin
      csrftoken = HTTParty.get(amy_login_url).headers['set-cookie'].scan(/csrftoken=([^;]+)/)[0][0]
      session_id = HTTParty.post(amy_login_url,
                                 follow_redirect: false,
                                 body: { username: amy_login.username, password: amy_login.password, csrfmiddlewaretoken: csrftoken },
                                 headers: { Referer: url, Cookie: "csrftoken=#{csrftoken}" }).headers['set-cookie'].scan(/sessionid=([^;]+)/)[0][0]
      return csrftoken, session_id
    rescue Exception => ex
      puts "Failed to authenticate with AMY. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
      return nil, nil
    end
  else
    puts "Failed to load AMY login details from #{amy_login_conf_file}: file does not exist."
    return nil, nil
  end
end

def get_uk_workshops
  all_published_workshops = []  # all workshops in AMY that are considered 'published', i.e. have a venue, location , longitude, latitude and start and end date
  uk_workshops = []
  begin
    # Retrieve publicly available workshop details using AMY's public API
    puts "Quering #{amy_api_published_workshops_url}"
    all_published_workshops = JSON.load(open(amy_api_published_workshops_url, "Accept" => "application/json"))
  rescue Exception => ex
    puts "Failed to get anything out of #{amy_api_published_workshops_url}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
  else
    # Get the workshops in the UK
    uk_workshops = all_published_workshops.select{|workshop| workshop["country"] == "GB"}
    puts "Result stats: number of UK workshops = #{uk_workshops.length.to_s}; total number of all workshops = #{all_published_workshops.length.to_s}."
  end
  return uk_workshops
end

def get_private_workshop_info(workshops, session_id, csrftoken)
  workshops.each_with_index do |workshop, index|
    begin
      print "######################################################\n"
      print "Processing workshop no. " + (index+1).to_s + " (#{workshop["slug"]}) from #{amy_ui_workshop_base_url + "/" + workshop["slug"]}" + "\n"

      # Replace the Cookie header info with the correct one, if you have access to AMY, as access to these pages needs to be authenticated
      #workshop_html_page = Nokogiri::HTML(open(amy_ui_workshop_base_url + "/" + workshop["slug"], :Cookie => "sessionid=#{session_id}; token=#{csrftoken}"), nil, "utf-8")
      response = HTTParty.get(amy_ui_workshop_base_url + "/" + workshop["slug"],
                              headers: { Cookie: "sessionid=#{session_id}; token=#{csrftoken}", csrftoken: csrftoken })
      workshop_html_page = Nokogiri::HTML(response.body)


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
      workshop['instructors'] = instructors.map(&:text) # Get text value of all instructor nodes as an array
      workshop['instructors'] += Array.new(10 - workshop['instructors'].length, '')  # append empty strings (if we get less then 10 instructors from AMY) as we have 10 placeholders for instructors and want csv file to be properly aligned
      workshop['instructors'] = workshop['instructors'][0,10] if workshop['instructors'].length > 10 # keep only the first 10 elements (that should be enough to cover all instructors, but just in case), so we can align the csv rows properly later on
      puts "Found #{workshop["instructors"].reject(&:empty?).length} instructors for #{workshop["slug"]}."
    rescue Exception => ex
      # Skip to the next workshop
      puts "Failed to get number of attendees for workshop #{workshop["slug"]} from #{amy_ui_workshop_base_url + "/" + workshop["slug"]}. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
      next
    end
  end
end

def write_workshops_to_csv(csv_file)
  # CSV headers
  csv_headers = ["slug", "humandate", "start", "end", "tags", "venue", "address", "latitude", "longitude", "eventbrite_id", "contact", "url", "number_of_attendees", "instructor_1", "instructor_2", "instructor_3", "instructor_4", "instructor_5", "instructor_6", "instructor_7", "instructor_8", "instructor_9", "instructor_10"]

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
end


if __FILE__ == $0 then
  # Get all UK workshops available via AMY's public API
  uk_workshops = get_uk_workshops()

  # Figure out some extra details about the workshops - e.g. the number of workshop attendees and instructors from AMY records - by accessing the UI/HTML page of each workshop - since this info is not available via the public API.
  # To do that, we need to extract the HTML table listing people and their roles (e.g. where role == 'learner' or where role == 'instructor').
  # Accessing these pages requires authentication and obtaining session_id and csrftoken for subsequent calls.
  session_id, csrftoken = authenticate_with_amy()
  get_private_workshop_info(uk_workshops, session_id, csrftoken) unless (session_id.nil? or csrftoken.nil?)

  date = Time.now.strftime("%Y-%m-%d")
  csv_file = "UK-carpentry-workshops_#{date}.csv"
  FileUtils.touch(csv_file) unless File.exist?(csv_file)

  write_workshops_to_csv(csv_file)
end
