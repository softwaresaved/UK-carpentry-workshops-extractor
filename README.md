This project contains a Ruby script that extracts the details of all UK Carpentry workshops recorded in Software Carpentry's AMY system.

This includes Software Carpentry, Data Carpentry and Train The Trainer (instructor training) workshops (and hopefully Library Carpentry workshops as well when they start being recorded in AMY).

The script uses AMY's public API to extract certain information, but also accesses some private pages (to extract data not exposed via the API). Hence, in order for the script to work, one needs to have an account in AMY. 

If use GitHub account to login to AMY, you need to your session cookie used after authentication and then use that cookie in the script to call certain private pages. Session cookie looks something like this: 
`"Cookie" => "__utma=2571...; __utmc=257105289; sessionid=cyu3...; _ga=GA1.2...; csrftoken=MrTv..."`
and you can figure one out if you look at what headers your browser sends after you authenticate with AMY. This is a hackish way of
doing things.

