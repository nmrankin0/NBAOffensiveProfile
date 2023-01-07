'''
File Purpose:
    - Gather Current Year NBA Synergy Play-type data and combine current years stats with past years stats

Program Flow:
    - Randomly select which play-type to start with
    - Gather data for each play-type
    - Combine all play-types
    - Combine current year with past years
    - Output all data google cloud storage

Program Input:
    - Credentials to auth in order to write to cloud storage: 'C:\\Users\\nrankin\\PycharmProjects\\Portfolio\\GCP\\clientcreds_storage_sa.json'
    - '2021_22_PlayTypeStats.csv' in nmrankin0_nbaappfiles bucket in GCS

Program Output:
    - 'AllSeasons_PlayTypeStats.csv' in nmrankin0_nbaappfiles bucket in GCS

'''

# ------------- IMPORT PACKAGES ------------- #
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import pandas as pd
import datetime
import random
import os
from google.cloud import storage

# ------------- ENDPOINT PARAMETERS ------------- #
# Play-type URL endpoints
playtype_endpoint_list = ['transition', 'isolation', 'ball-handler', 'roll-man',
                          'playtype-post-up', 'spot-up', 'hand-off', 'cut',
                          'off-screen', 'putbacks', 'playtype-misc']

playtype_words_list = ['Transition', 'Isolation', 'Pick & Roll Ball Handler',
                       'Pick & Roll Roll Man', 'Post Up', 'Spot Up', 'Handoff', 'Cut',
                        'Off Screen', 'Putbacks', 'Misc']

# To randomizer order
rand_order_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
random.shuffle(rand_order_list)

# Word to endpoint dictionary
word_to_endp_dict = {}
for num in rand_order_list:
    word_to_endp_dict[playtype_words_list[num]] = playtype_endpoint_list[num]

# Add index to dictionary format =  {index: {key:value}}
ordered_dict = {}
for i, (k, v) in enumerate(word_to_endp_dict.items()):
    ordered_dict[i] = [k, v]

# ------------- INITIATE CHROME WEB BROWSER & NAVIGATE TO SITE ------------- #
df_holder_list = []
with sync_playwright() as p:

    # Launch browser
    print('Preparing browser', '\n')
    browser = p.chromium.launch(headless=False, slow_mo=200)        # headless = False is used so that we can see the browser on our screen
    page = browser.new_page()
    stealth_sync(page)

    # ---- Navigate to play type page (diff flow based on first iteration) ---- #
    for index, wordlink_list in ordered_dict.items():

        # If we're navigating to first page we are collecting, use endpoint (i.e., word) in link
        if wordlink_list[0] == playtype_words_list[rand_order_list[0]]:
            print('Launching to first page of browser:', wordlink_list[0], '\n')
            page.goto('https://www.nba.com/stats/players/' + wordlink_list[1])
            page.wait_for_timeout(random.randint(5000, 12000))
            page.mouse.move(random.randint(100, 200), random.randint(100, 200))


            # If the 'opt in' pops up, click accept
            try:
                print('Checking if TOS required', '\n')
                page.query_selector('#onetrust-accept-btn-handler').click()
            except Exception as e:
                pass

        # If not navigating to first page we are collecting, navigate through clicking dropdown
        else:
            print('Finding how to navigate to next page:', wordlink_list[0], '\n')
            all_filts = page.query_selector_all('.StatsQuickNavSelector_selector__LkTyQ')
            for filt in all_filts:
                if filt.inner_text() == ordered_dict[index-1][0]:          # The filter text should be the same as the text on the first endpoint we navigated to
                    filt.click()

                    # Find all dropdown values, and click value/word that corresponds with current index iteration to bring to new page
                    print('Navigating to next page', '\n')
                    playtype_dd_selections = page.query_selector_all('.StatsQuickNavSelector_link__yl1f2')
                    for dd_sel in playtype_dd_selections:
                        if dd_sel.inner_text() == wordlink_list[0]:
                            dd_sel.click()
                            break
                        else:
                            pass

        # ------------- GATHER INFO FROM TABLES ------------- #
        page.mouse.move(random.randint(100, 200), random.randint(100, 200))
        page.wait_for_timeout(random.randint(6000, 9000))

        # Find dropdown of interest, select 'All' within table dropdown to load all rows
        page_dds = page.query_selector_all('.DropDown_select__4pIg9')
        print('Expanding table', '\n')
        for dd in page_dds:
            if 'All' in dd.inner_text():
                dd.select_option(label='All')
                break
            else:
                pass

        page.wait_for_timeout(random.randint(10000, 13000))
        page.mouse.move(random.randint(100, 200), random.randint(100, 200))

        # Gather whole table into & add df to holder list
        print('Gathering', '\n')
        df_statstabl = pd.read_html(page.query_selector('.Crom_container__C45Ti').inner_html())[0]
        df_statstabl['PlayType'] = wordlink_list[0]
        df_holder_list.append(df_statstabl)


# ------------- CONCAT DATAFRAMES INTO 1 FRAME & OUTPUT TO GOOGLE CLOUD STORAGE ------------- #
# Combine all dfs into single df
print('Combining & outputting dfs', '\n')
df_allstats = pd.concat(df_holder_list)
df_allstats['SEASON'] = '2022-23'
df_allstats['UpdateDate'] = datetime.date.today()

# Load previous season from google cloud storage ; local code = #df_prevseason = pd.read_excel('2021_22_PlayTypeStats.xlsx')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\nrankin\\PycharmProjects\\Portfolio\\GCP\\clientcreds_storage_sa.json'
bucket_name = 'nmrankin0_nbaappfiles'
df_prevseason = pd.read_csv('gs://' + bucket_name + '/2021_22_PlayTypeStats.csv')

# Concat current and previous season
df_allseason_allstats = pd.concat([df_prevseason, df_allstats])

# Write file to GCS  ; local code = #df_allseason_allstats.to_excel('AllSeasons_PlayTypeStats.xlsx', index=False)
bucket_name = 'nmrankin0_nbaappfiles'
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)
bucket.blob('AllSeasons_PlayTypeStats.csv').upload_from_string(df_allseason_allstats.to_csv(index=False), 'text/csv')

print('Output complete', '\n')
