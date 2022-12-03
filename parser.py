from typing import Optional
from datetime import date
from core.browser import Browser
from core.config_parser import MainConfig, OpenApiConfig
from selenium.webdriver.common.by import By
from core.database import Database
import concurrent.futures
import requests
import json

DATABASE = Database()
MAIN_CONFIG = MainConfig()


class SeleniumParser(Browser):

    def __init__(self,
                 sport_list: list[str],
                 sport_date_list: list[str],
                 fullscreen: Optional[bool] = None,
                 window_height: Optional[int] = None,
                 window_width: Optional[int] = None,
                 use_proxy: Optional[bool] = None):
        super().__init__(fullscreen=fullscreen, window_height=window_height,
                         window_width=window_width, use_proxy=use_proxy)
        self.sport_list = sport_list
        self.sport_date_list = sport_date_list

        if len(self.sport_list) > 0 and self.sport_list[0] == 'all':
            self.sport_list = MAIN_CONFIG['sports']

        for sport in sport_list:
            for temp_date in sport_date_list:
                day_result = self.try_parse_sport(sport, temp_date)
                day_result = data_processing(day_result)

                print(day_result)
                insert_data_into_database(day_result)

        self.close_browser()

    def parse_events_temp_table(self, live: bool = False):
        result = []
        if not self.check_web_element_availability(By.CLASS_NAME,
                                                   'ReactVirtualized__Grid__innerScrollContainer'):
            return result
        counter = 0
        last_row = None
        result_repeats = []
        while True:
            counter += 1
            table = self.driver.find_element(By.CLASS_NAME, 'ReactVirtualized__Grid__innerScrollContainer')
            rows = table.find_elements(By.TAG_NAME, 'a')
            if rows[-1] == last_row:
                break
            elif counter > 100:
                raise Exception('infinite in def parse_events_temp_table')
            for row in rows:
                text = row.get_attribute('innerText')
                text_list = text.split('\n')
                if text in result_repeats or len(text_list) < 4:
                    continue
                result_repeats.append(text)
                result.append({'time': text_list[0], 'status': text_list[1],
                               'team1': text_list[2].replace("'", ""),
                               'team2': text_list[3].replace("'", ""),
                               'is live': live})
            last_row = rows[-1]
            self.driver.execute_script('return arguments[0].scrollIntoView(true);', last_row)
            for i in range(10):
                self.driver.execute_script(f'window.scrollBy(0, {int((self.CONFIG["window height"] - 100) / 12)})')
            self.random_sleep(1, 3)

        return result

    def parse_events_table(self):
        self.driver.find_element(By.CSS_SELECTOR, 'label[for="WideToggle-right"]').click()
        self.random_sleep(5, 10)
        live_result = self.parse_events_temp_table(live=True)
        self.driver.find_element(By.CSS_SELECTOR, 'label[for="WideToggle-left"]').click()
        self.random_sleep(5, 10)
        day_result = self.parse_events_temp_table()

        for row in live_result:
            for another_row in day_result:
                if (row['time'] == another_row['time'] and row['status'] == another_row['status'] and
                        row['team1'] == another_row['team1'] and row['team2'] == another_row['team2']):
                    another_row['is live'] = True
                    break
        return day_result

    def pass_cookie(self):
        if self.check_web_element_availability(By.CLASS_NAME, 'fc-dialog-content'):
            self.driver.find_element(By.CLASS_NAME, 'fc-button-label').click()
            self.random_sleep()

    def parse_sport(self, sport_name: str, sport_date: str):
        for i in range(MAIN_CONFIG['tries']):
            self.open_page(f'{self.MAIN_PAGE}/{sport_name}/{sport_date}')
            if not self.wait(MAIN_CONFIG['waits']['wait for sport page'],
                             By.CLASS_NAME, 'ReactVirtualized__Grid__innerScrollContainer'):
                self.pass_cookie()
                continue
            self.pass_cookie()
            return self.parse_events_table()
        raise Exception('No sport data found\n'
                        f'sport: {sport_name}\n'
                        f'date: {sport_date}')

    def try_parse_sport(self, sport_name: str, sport_date: str):
        try:
            return self.parse_sport(sport_name, sport_date)
        except Exception as e:
            if not self.check_text_availability('Try selecting a different date on the calendar.'):
                raise e
            return []


def insert_data_into_database(data: list):
    for row in data:
        if DATABASE.get_rows_by_teams_data(row):
            continue
        DATABASE.insert_row(row)


def data_processing(data: list):
    for row in data:
        if '/' not in row['time']:
            today = date.today()
            row['time'] = row['time'] + f' {today.day if len(str(today.day)) > 1 else "0" + str(today.day)}/' \
                                        f'{today.month if len(str(today.month)) > 1 else "0" + str(today.month)}/' \
                                        f'{today.year}'
    return data


class ApiParser:
    API_URL = 'https://api.sofascore.com'
    CONFIG = OpenApiConfig()
    PROXY_URL = f'http://{CONFIG["proxy username"]}:{CONFIG["proxy password"]}@' \
                f'{CONFIG["proxy ip"]}:{CONFIG["proxy port"]}'

    def __init__(self,
                 sport_list: list[str],
                 sport_date_list: list[str],
                 use_proxy: Optional[bool] = None,
                 parallel: Optional[bool] = None
                 ):
        self.sport_list = sport_list
        self.sport_date_list = sport_date_list
        self.use_proxy = use_proxy
        self.parallel = parallel

        if len(self.sport_list) > 0 and self.sport_list[0] == 'all':
            self.sport_list = MAIN_CONFIG['sports']

        self.parse()
        self.parse(live=True)

    def parse_sport(self, *args, **kwargs):
        args = args[0]
        if 'sport_name' in args and 'sport_date' in args and 'live' in args:
            sport_name = args['sport_name']
            sport_date = args['sport_date']
            live = args['live']
        else:
            return []
        try:
            response = requests.get(
                url=f'{self.API_URL}/api/v1/sport/{sport_name}/scheduled-events/{sport_date}' if not live else
                f'{self.API_URL}/api/v1/sport/{sport_name}/events/live',
                proxies={'http': self.PROXY_URL, 'https': self.PROXY_URL} if self.use_proxy else None)
        except Exception as e:
            raise e
        result_json = json.loads(response.text)
        if 'error' in result_json:
            return []
        result = []
        for event in result_json['events']:
            result.append({'time': sport_date, 'status': event['status']['description'],
                           'team1': event['homeTeam']['name'].replace("'", ""),
                           'team2': event['awayTeam']['name'].replace("'", ""),
                           'is live': live})
        return result

    def parse(self, live=False):
        result = []
        if self.parallel:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                if len(self.sport_date_list) > len(self.sport_list):
                    for sport_name in self.sport_list:
                        sport_result = executor.map(self.parse_sport,
                                                    [{'sport_name': sport_name,
                                                      'sport_date': sport_date,
                                                      'live': live}
                                                     for sport_date in self.sport_date_list])
                        result += sport_result
                else:
                    for sport_date in self.sport_date_list:
                        sport_result = executor.map(self.parse_sport,
                                                    [{'sport_name': sport_name,
                                                      'sport_date': sport_date,
                                                      'live': live}
                                                     for sport_name in self.sport_list])
                        result += sport_result
        else:
            for sport_name in self.sport_list:
                for sport_date in self.sport_date_list:
                    sport_result = self.parse_sport({'sport_name': sport_name,
                                                     'sport_date': sport_date,
                                                     'live': live})
                    result += sport_result
        if result:
            if isinstance(result[0], list):
                new_result = []
                for temp_result in result:
                    new_result += temp_result
                result = new_result
            print(result)
            result = data_processing(result)
            insert_data_into_database(result)


if __name__ == '__main__':
    # temp_parser = SeleniumParser(sport_list=['esports'], sport_date_list=['2022-12-02',
    #                                                                       '2022-12-03'])
    another_temp_parser = ApiParser(sport_list=['all'], sport_date_list=['2022-12-02'],
                                    parallel=True)
