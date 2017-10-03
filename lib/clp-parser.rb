require 'optparse'
require 'ostruct'
require 'date'

# Data directory where we save the results
DATA_DIR = "#{File.expand_path(File.dirname(__FILE__))}/data"
FileUtils.mkdir_p(DATA_DIR) unless Dir.exists?(DATA_DIR)

# Parse command line parameters
# As per http://ruby-doc.org/stdlib-2.1.3/libdoc/optparse/rdoc/OptionParser.html
def parse(args)
  # The options specified on the command line will be collected in *options*.
  # We set the default values here.
  options = OpenStruct.new
  options.country_code = "GB"
  date = Time.now.strftime("%Y-%m-%d")
  options.workshops_file = File.join(DATA_DIR, "carpentry-workshops_GB_#{date}.csv")
  options.instructors_file = File.join(DATA_DIR, "carpentry-instructors_GB_#{date}.csv")

  opt_parser = OptionParser.new do |opts|
    opts.banner = "Usage: ruby extract-workshops-instructors.rb [-u USERNAME] [-p PASSWORD] [-c COUNTRY_CODE] [-w WORKSHOPS_FILE] [-i INSTRUCTORS_FILE]"

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
      options.country_code = country_code
      options.workshops_file = File.join(DATA_DIR, "carpentry-workshops_#{country_code}_#{date}.csv")
      options.instructors_file = File.join(DATA_DIR, "carpentry-instructors_#{country_code}_#{date}.csv")
    end

    opts.on("-w", "--workshops_file WORKSHOPS_FILE",
            "File name within 'data' directory where to save the workshops extracted from AMY to. Defaults to carpentry-workshops_COUNTRY_CODE_DATE.csv.") do |workshops_file|
      options.workshops_file = File.join(DATA_DIR, "#{workshops_file}")
    end

    opts.on("-i", "--instructors_file INSTRUCTORS_FILE",
            "File name within 'data' directory where to save the instructors extracted from AMY to. Defaults to carpentry-instructors_COUNTRY_CODE_DATE.csv.") do |instructors_file|
      options.instructors_file = File.join(DATA_DIR, "#{instructors_file}")
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