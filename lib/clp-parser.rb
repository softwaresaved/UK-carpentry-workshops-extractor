# Parse command line parameters
# As per http://ruby-doc.org/stdlib-2.1.3/libdoc/optparse/rdoc/OptionParser.html

require 'optparse'
require 'ostruct'
require 'date'

# Data directory where we save the results
DATA_DIR = File.expand_path("../data", File.expand_path(File.dirname(__FILE__)))
FileUtils.mkdir_p(DATA_DIR) unless Dir.exists?(DATA_DIR)
WORKSHOPS_DIR = "#{DATA_DIR}/workshops"
INSTRUCTORS_DIR = "#{DATA_DIR}/instructors"

def parse(args)
  # The options specified on the command line will be collected in *options*.
  # We set the default values here.
  options = OpenStruct.new
  options.country_code = "GB"
  date = Time.now.strftime("%Y-%m-%d")
  if ($0.downcase.include?('workshops'))
    FileUtils.mkdir_p(WORKSHOPS_DIR) unless Dir.exists?(WORKSHOPS_DIR)
    options.workshops_file = File.join(WORKSHOPS_DIR, "carpentry-workshops_GB_#{date}.csv")
  elsif ($0.downcase.include?('instructors'))
    FileUtils.mkdir_p(INSTRUCTORS_DIR) unless Dir.exists?(INSTRUCTORS_DIR)
    options.instructors_file = File.join(INSTRUCTORS_DIR, "carpentry-instructors_GB_#{date}.csv")
  else
    puts "You are possibly not invoking the correct Ruby script - extract_workshops.rb or extract_instructors.rb."
    exit 1
  end

  opt_parser = OptionParser.new do |opts|
    if ($0.downcase.include?('workshops'))
      opts.banner = "Usage: ruby #{$0} [-u USERNAME] [-p PASSWORD] [-c COUNTRY_CODE] [-w WORKSHOPS_FILE]"
    elsif ($0.downcase.include?('instructors'))
      opts.banner = "Usage: ruby #{$0} [-u USERNAME] [-p PASSWORD] [-c COUNTRY_CODE] [-i INSTRUCTORS_FILE]"
    end

    opts.separator ""

    opts.on("-u", "--username USERNAME",
            "Username to use to authenticate to AMY") do |username|
      options.username = username
    end

    opts.on("-p", "--password PASSWORD",
            "Password to use to authenticate to AMY") do |password|
      options.password = password
    end

    opts.on("-c", "--country_code COUNTRY_CODE",
            "ISO-3166-1 two-letter country_code code or 'all' for all countries. Defaults to 'GB'.") do |country_code|
      options.country_code = country_code.upcase # Country codes need to be uppercase so handle lowercase cases
      if ($0.downcase.include?('workshops'))
        options.workshops_file = File.join(WORKSHOPS_DIR, "carpentry-workshops_#{options.country_code}_#{date}.csv")
      elsif ($0.downcase.include?('instructors'))
        options.instructors_file = File.join(INSTRUCTORS_DIR, "carpentry-instructors_#{options.country_code}_#{date}.csv")
      end
    end

    if ($0.downcase.include?('workshops'))
      opts.on("-w", "--workshops_file WORKSHOPS_FILE",
              "File within 'data/workshops' directory where to save the workshops extracted from AMY to. Defaults to carpentry-workshops_COUNTRY_CODE_DATE.csv.") do |workshops_file|
        options.workshops_file = File.join(WORKSHOPS_DIR, "#{workshops_file}")
      end
    end

    if ($0.downcase.include?('instructors'))
      opts.on("-i", "--instructors_file INSTRUCTORS_FILE",
              "File within 'data/instructors' directory where to save the instructors extracted from AMY to. Defaults to carpentry-instructors_COUNTRY_CODE_DATE.csv.") do |instructors_file|
        options.instructors_file = File.join(INSTRUCTORS_DIR, "#{instructors_file}")
      end
    end

    # A switch to print the version.
    opts.on_tail("-v", "--version", "Show version") do
      puts VERSION
      exit
    end

    # Print an options summary.
    opts.on_tail("-h", "--help", "Show this help message") do
      puts opts
      exit
    end

  end

  opt_parser.parse!(args)
  options
end  # parse()