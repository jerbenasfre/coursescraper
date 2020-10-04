from bs4 import BeautifulSoup
from selenium import webdriver
import requests
from urllib.parse import unquote
import json
import re
import time

# Specify path constants for selenium and JSON
WEBDRIVER = ""
SAVE_PATH = ""

class Course:

    def __init__(self, name, instructors = None, university = None, provider = None, start = None, duration = None, language = None, description = None):
        self._name = name
        self._instructors = instructors
        self._university = university
        self._provider = provider
        self._start = start
        self._duration = duration
        self._language = language
        self._description = description

    def getName(self):
        return self._name

    def getInstructors(self):
        return self._instructors

    def getUniversity(self):
        return self._university

    def getProvider(self):
        return self._provider

    def getStart(self):
        return self._start

    def getDuration(self):
        return self._duration

    def getLanguage(self):
        return self._language

    def getDescription(self):
        return self._description

    # Returns a str representation of course for debugging purposes.
    def __str__(self):
        return f"Name: {self._name}, Instructor(s): {self._instructors}, University: {self._university}, Provider: {self._provider}, Start: {self._start}, Duration: {self._duration}, Language: {self._language}\nDescription: {self._description}"

    # Returns the dict representation of the course to be converted into JSON
    def getJSON(self):
        return {
                "name": self._name,
                "instructor(s)": self._instructors,
                "university": self._university,
                "provider": self._provider,
                "start": self._start,
                "duration": self._duration,
                "language": self._language,
                "description": self._description
            }
    
class CourseScraper:

    def __init__(self):
        # list to hold all the Course objects.
        self._courses = []
        
        # set to hold all subjects that need to be scrapped from.
        self._subjects = set()
        
        # selenium webdriver to click load more button.
        self._driver = webdriver.Chrome(WEBDRIVER)

        self._debug = False

    # Util method to quit the webdriver when finished scrapping.
    def quitDriver(self):
        self._driver.quit()

    # Handles construction of course data into Course object.
    #
    # Parameters:
    # course_url - url of the course page to be scraped.
    def _createCourse(self, course_url):
        
        if self._debug:
            print("Scraping " + course_url)

        # Wait 1 second before scraping course page.
        time.sleep(1)
        response = requests.get(course_url)

        soup = BeautifulSoup(response.text, "html.parser")

        # Get course title.
        try:
            title = soup.findAll("h4", {"class": "coursepage-coursetitle"})[0].text
            classification = (soup.findAll("div", {"class": "coursepage-cbtitle"})[0]).a.text.split(" - ")[0]
        except:
            print("Error occured in _createCourse when scrapping title. Courses must have a title.")
            return

        # Get course description.
        description = "NA"
        try:
            description = (soup.findAll("div", {"class": "coursedetails-description"})[0]).p.text
        except:
            if self._debug:
                print("No description was found.")

        # Extracts info from "More Info" tab in course buffet.
        info_a, info_b = soup.find_all("ul",{"class": "CourseInfoTab-list1"})

        # Default values to NA.
        instructors = "NA"
        university = "NA"
        provider = "NA"
        start = "NA"
        duration = "NA"
        language = "NA"

        # Get instructor(s).
        instructors = info_a.li.text[len("instructor(s)")+1:] if info_a.li.text != None else "NA"
        
        # Get university and provider.
        divs = info_a.findAll("div", attrs={"class":"courseinfoimg"})

        # Checks to see if university or provider can be found, defaults to NA if not.
        if len(divs) > 0:

            if len(divs) > 1:
                university = unquote(divs[0].img['src'].split("/")[-1][:-4])
                provider = unquote(divs[1].img['src'].split("/")[-1][:-4])
                
            # If providers is in the first div object, there is no university.
            elif "providers" in divs[0].img['src']:
                provider = unquote(divs[0].img['src'].split("/")[-1][:-4])
            # There is no providers
            else:
                university = unquote(divs[0].img['src'].split("/")[-1][:-4])
        else:
            university = "NA"
            provider = "NA"

        # If info_b contains info, scrape it.
        if len(info_b) != 0:
            # Get start date, duration, & language.
            for li in info_b.findAll("li"):
                if li.span.text == "Start Date":
                    start = li.text[len("start date")+1:]
                elif li.span.text == "Duration":
                    duration = li.text[len("duration")+1:]
                elif li.span.text == "Main Language":
                    language = li.text[len("main language")+1:]

        # Create course object.
        course = Course(title,instructors,university,provider,start,duration,language,description)

        if self._debug:
            print("Adding course:\n\n" + str(course))
            
        self._courses.append(course)

    # Gathers all the subjects listed in the site's browse all page.
    #
    # Parameters:
    # seed_url - starting page to scrape the subjects from.
    # pattern - pattern to look for in order to find link to subject page.
    def _gatherSubjects(self, seed_url, pattern):
        if self._debug:
            print("Gathering subjects in page: " + seed_url)

        try:
            response = requests.get(seed_url)

            # Wait for 3 sec for the page to load.
            time.sleep(3)

            # Raise HTTPError if http response is not ok.
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Gather links to subject pages.
            for sub in soup.findAll('a', attrs={'href': re.compile(pattern)}):
                self._subjects.add(sub.get('href'))
            
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

    # First extracts the courses from a subject and then calls createCourse
    # to turn it into a Course object.
    #
    # Parameters:
    # base_url - base url to append queries to
    # subject_url - link to a subject page.
    # pattern - pattern to look for in order to find course link
    def _getCourses(self, base_url, subject, pattern):
        self._driver.get(base_url+subject)

        # Wait for 1.5 sec for the page to load.
        time.sleep(1.5)

        # Change if site has a different id for load more button.
        try:
            button = self._driver.find_element_by_id("load-more-button")

            # Handles the load more button for coursebuffet.
            while button.is_displayed():
                button.click()
                # Wait for 1/2 a sec for the page to load.
                time.sleep(0.5)
        except:
            if self._debug:
                print("No load more button found. Will just scrape from current page.")
        
        soup = BeautifulSoup(self._driver.page_source, "html.parser")

        course_links = set()

        for link in soup.findAll('a', attrs={'href': re.compile(pattern)}):
            course_links.add(base_url+link.get('href'))

        # Iterate through each course found in subject page.
        for course in course_links:
            self._createCourse(course)

    
    # Calls helper methods to scrape coursebuffet.
    # First gathers all subjects found in coursebuffet,
    # then gathers the courses from one subject,
    # and finally writes to file the courses from that subject.
    # Process repeats until all subject courses have been scraped and saved.
    def scrape(self):
        self._gatherSubjects("https://www.coursebuffet.com/areas","/sub/")
 
        if self._debug:
            print(f"Total subjects: {len(self._subjects)}")
            for sub in self._subjects:
                print(sub)

        if len(self._subjects) == 0:
            print("No subjects was found. Check pattern or url given.")
            return
        
        # Iterate through subjects and get the course from each subject
        for sub in self._subjects:
            if self._debug:
                print("Getting courses from: https://www.coursebuffet.com"+sub)
            self._getCourses("https://www.coursebuffet.com",sub,"/course/")

            if len(self._courses) == 0:
                print("No courses were found. Check the subject_url and make sure it is valid for the site")
            else:
                # Save the courses gathered from one subject and reset the courses list.
                # This is to ensure some data gets saved in case of a crash.
                for course in self._courses:
                    self._saveToFile(course, SAVE_PATH);

                self._courses.clear()

        
    # Saves the course as JSON to specified path. Names the file using title + provider to account for courses with same title.
    def _saveToFile(self, course, save_path):
        # Filter course name so it is valid for a window's environment.
        file = "".join( x for x in course.getName()+"by"+course.getProvider()+".json" if (x.isalnum() or x in "._- "))
        
        with open(save_path+file, "w+") as file_name:
            json.dump(course.getJSON(), file_name)




if __name__ == "__main__":
    scraper = CourseScraper()
    scraper.scrape()
    scraper.quitDriver()
