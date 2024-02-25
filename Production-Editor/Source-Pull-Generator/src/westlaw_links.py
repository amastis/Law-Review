import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException


class WestLaw:
    """WestLaw link searching"""
    def __init__(self, username: str, password: str) -> None:
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(), options=options)
        self._login(username, password)
        
    def _login(self, username: str, password: str) -> None:
        '''login and get to the search bar'''
        self.driver.get('https://1.next.westlaw.com/Search/Home.html?transitionType=Default&contextData=(sc.Default)&bhcp=1')
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, 'SignIn'))) 
        self.driver.find_element(By.ID, 'Username').send_keys(username)
        self.driver.find_element(By.ID, 'Password').send_keys(password)
        time.sleep(2)
        self.driver.find_element(By.ID, 'SignIn').click()
        element = WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.ID, 'co_clientIDContinueButton'))) 
        time.sleep(2)
        self.driver.find_element(By.ID, 'co_clientIDContinueButton').click() # click start a new session
        WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.ID, 'searchInputId')))

    def get_source_link(self, search_term: str) -> str:
        '''input search into search bar and return the first result - if a list or the document if a specific url is redirected'''
        self.driver.find_element(By.ID, 'searchInputId').clear()
        self.driver.find_element(By.ID, 'searchInputId').send_keys(search_term)
        try:
            self.driver.find_element(By.ID, 'searchButton').click()
        except ElementClickInterceptedException as e: # trying to handle if modal popups occur
            self.driver.execute_script("arguments[0].click();", self.driver.find_element(By.ID, 'searchButton'))

        # https://stackoverflow.com/questions/36316465/what-is-the-best-way-to-check-url-change-with-selenium-in-python
        try: # wait for search to go through
            WebDriverWait(self.driver, 60).until(EC.url_changes(self.driver.current_url))
        except TimeoutException as ex:
            pass

        # handling waiting for different page types and getting results
        if '/Search/' in self.driver.current_url:
            # when using a generic term --> get a loading screen to check for
            try: # see if loading bar is on screen and wait
                WebDriverWait(self.driver, 60).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'co_loading'))) 
            except TimeoutException as ex:
                print(ex)
            
            try: # check search results on screen - to select first result
                element = WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.ID, 'cobalt_search_case_results')))
            except (NoSuchElementException, TimeoutException) as e: # no results?
                pass
            try: # for when there are no results
                multiple_cases = WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.CLASS_NAME, 'co_searchResult_list')))
                element = multiple_cases.find_element(By.TAG_NAME, 'h3')
            except (TimeoutException, NoSuchElementException) as e:
                pass # assumed that element was already assigned. so don't need reassignment


            if element: # TODO add comparison for source
                # get first resource on search result page (taking you directly to the source)
                return element.find_element(By.TAG_NAME, 'a').get_attribute("href")
        elif '/Document/' in self.driver.current_url:
            # when a case --> no loading screen --> look for search bar to load
            try: # dismiss tutorial popup
                element = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'bb-button')))
                self.driver.find_element(By.CLASS_NAME, 'bb-button').click()
            except (TimeoutException, NoSuchElementException) as ex:
                pass

            try: # wait for page to fully load (for next search)
                WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.ID, 'searchInputId')))
            except TimeoutException as e:
                pass

            return self.driver.current_url

        return ''


if __name__ == '__main__':
    # local file
    import settings # FOR LOCAL TESTING
    
    westlaw = WestLaw(settings.westlaw_username, settings.westlaw_password)
    # TEST --  general search term to case 
    print(westlaw.get_source_link('test'))
    print(westlaw.get_source_link('473 U.S. 667'))
    # TEST --  case with shepards warnings (creating modals) to case
    print(westlaw.get_source_link('48 S.Ct. 564'))
    print(westlaw.get_source_link('389 U.S. 347'))
    # TEST - where there are multiple versions of a case
    print(westlaw.get_source_link('448 U.S. 297'))
