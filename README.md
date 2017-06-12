This project contains a Ruby script that extracts the details all Carpentry workshops that went ahead in the UK from the Software Carpentry's AMY system.

This includes Software Carpentry, Data Carpentry and Train The Trainer (instructor training) workshops (and hopefully Library Carpentry workshops as well when they start recording them in AMY).

The script uses AMY's public API to extract certain information, but also accesses some private pages (to extract data not exposed via the API). Hence, in order for the script to work, one needs to have an account in AMY and to discover one's session cookie used after authentication to gain access and then use that cookie in the script to call certain private pages.

Cookie looks something like this: 
"Cookie" => "__utma=2571...; __utmc=257105289; sessionid=cyu3...; _ga=GA1.2...; csrftoken=MrTv..."
and you can figure one out if you look at what headers your browser sends after you authenticate with AMY. This is a hackish way of
doing things but there is no other way to authenticate programmaticaly at the moment, nor is this info exposed  via the API.

