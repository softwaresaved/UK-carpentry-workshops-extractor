require 'google_drive'
require "fileutils"

def google_drive_upload(file_path, google_folder_id)
  begin
    secrets_file = File.join(File.dirname(__FILE__), '/../client_secrets.json')
    session = GoogleDrive::Session.from_config(secrets_file)
    file_name = File.basename(file_path)
    parent_folder = session.file_by_id(google_folder_id)
    parent_folder.upload_from_file(file_path,
                                   file_name,
                                   {convert: false, :content_type => "text/csv"})
    puts "File #{file_path} uploaded to Google Drive."
  rescue Exception => ex
    puts "\n" + "#" * 80 +"\n\n"
    puts "Failed to upload #{file_path} to Google Drive. An error of type #{ex.class} occurred, the reason being: #{ex.message}."
    puts "Backtrace:\n\t#{ex.backtrace.join("\n\t")}"
  end
end