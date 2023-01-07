'''
File Purpose:
    - Prepare NBA data for clustering

Program Flow:
    - Create unique id for each player - season - team
    - Reformat the data by transposing so that for each unique id,  all play-type frequencies are in a single row
    - Create metric to sum all play-type frequencies to check data completeness
    - Output reformatted data

Program Input:
    - Credentials to auth in order to write to cloud storage: 'C:\\Users\\nrankin\\PycharmProjects\\Portfolio\\GCP\\clientcreds_storage_sa.json'
    - 'AllSeasons_PlayTypeStats.csv' in nmrankin0_nbaappfiles bucket in GCS

Program Output:
    - 'AllSeasons_FreqsForClus.csv' in nmrankin0_nbaappfiles bucket in GCS

'''

# ------------- IMPORT PACKAGES & DATA ------------- #
import pandas as pd
import os
from google.cloud import storage

# Data to df ; local code: #df = pd.read_excel('AllSeasons_PlayTypeStats.xlsx')
print('Importing data', '\n')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\nrankin\\PycharmProjects\\Portfolio\\GCP\\clientcreds_storage_sa.json'
bucket_name = 'nmrankin0_nbaappfiles'
df = pd.read_csv('gs://' + bucket_name + '/AllSeasons_PlayTypeStats.csv')


# ------------- CREATE UNIQUE ID ------------- #
print('Creating unique ID', '\n')
df['UniqueID'] = df['PLAYER'] + ' - ' + df['TEAM'] + ' - ' + df['SEASON']


# ------------- TRANSPOSE PLAY-TYPE BY FREQ ------------- #
print('Transposing frequencies by unique ID', '\n')

# Unique play types list
PT_LIST = df['PlayType'].dropna().unique().tolist()

df_transpose = df[['UniqueID', 'PLAYER', 'TEAM', 'SEASON']].drop_duplicates()
for row, col in df_transpose.iterrows():
    for pt in PT_LIST:
        # If player has no entry for play-type, default value to 0
        try:
            df_transpose.loc[row, pt] = df[(df['PLAYER'] == df_transpose.loc[row, 'PLAYER']) & (df['TEAM'] == df_transpose.loc[row, 'TEAM']) & (df['SEASON'] == df_transpose.loc[row, 'SEASON']) & (df['PlayType'] == pt)]['Freq%'].values[0]
        except IndexError as e:
            df_transpose.loc[row, pt] = 0


# ------------- CLEAN-UP & OUTPUT ------------- #
print('Preparing and outputting transposed data for clustering', '\n')

# Check summed freq %
df_transpose['SummedFreq'] = df_transpose[PT_LIST].sum(axis=1)

# Only keep required columns
df_transpose = df_transpose[['UniqueID', 'PLAYER', 'TEAM', 'SEASON'] + PT_LIST + ['SummedFreq']]

# Output to GCS ; local code : # df_transpose.to_excel('AllSeasons_FreqsForClus.xlsx', index=False)
bucket_name = 'nmrankin0_nbaappfiles'
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)
bucket.blob('AllSeasons_FreqsForClus.csv').upload_from_string(df_transpose.to_csv(index=False), 'text/csv')

print('Output complete', '\n')
