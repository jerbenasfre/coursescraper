# About

Simple webscraper I made in order to scrape coursebuffet in order to brush up on my webscraping skills. This repository contains the code to run the webscraper, a zip of the courses it gathers from coursebuffet, and a mockup of what the mysql tables would look like.

It gathers the course name, instructor, description, university, provider, start date, duration, and main language and writes the info as a json file.

I used Selenium to interact with the load more button, beautifulsoup and regex to parse for the data I need.

# Future Plans:

* Make the json writing asynchronous to speed it up.

* Make webscraper more generic in order to use for other websites.

* Reimplement webscraper using javascript libraries/frameworks.