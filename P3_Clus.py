'''
File Purpose:
    - Cluster unique IDs (player, team, season) based on how often they engage in each play-type

Program Flow:
    - Get the bottom 20% of league in terms of frequency data completeness and apply negative values to their missing values to further separate them from active players during clustering
    - Find the 'optimal' number of cluster in K-Means through finding the point that maximizes incremental decrease in SSE (elbow method)
    - K-Means clustering
    - Reduce data to two features through PCA, for the purpose of data visualization
    - Add PCs to cluster dataset
    - Output clusters with PC coordinates

Program Input:
    - Credentials to auth in order to write to cloud storage: 'C:\\Users\\nrankin\\PycharmProjects\\Portfolio\\GCP\\clientcreds_storage_sa.json'
    - 'AllSeasons_FreqsForClus.csv' in nmrankin0_nbaappfiles bucket in GCS

Program Output:
    - 'AllSeasons_ClusteredFreqs.csv' in nmrankin0_nbaappfiles bucket in GCS

'''

# ------------- IMPORT PACKAGES & DATA ------------- #
import pandas as pd
from sklearn.cluster import KMeans
from kneed import KneeLocator
from sklearn.decomposition import PCA
import os
from google.cloud import storage


# Data to df ; local code: #df = pd.read_excel('AllSeasons_FreqsForClus.xlsx')
print('Importing data', '\n')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\nrankin\\PycharmProjects\\Portfolio\\GCP\\clientcreds_storage_sa.json'
bucket_name = 'nmrankin0_nbaappfiles'
df = pd.read_csv('gs://' + bucket_name + '/AllSeasons_FreqsForClus.csv')


# ------------- FURTHER SEPARATE PLAYERS WITH SPARSE DATA (THESE HAVE NOT PLAYED MANY MINUTES, FILTER DF TO ONLY INCLUDE INPUTS ------------- #
print('Separating zero frequencies for bottom 20% of league', '\n')

playtype_words_list = ['Transition', 'Isolation', 'Pick & Roll Ball Handler',
                       'Pick & Roll Roll Man', 'Post Up', 'Spot Up', 'Handoff', 'Cut',
                        'Off Screen', 'Putbacks', 'Misc']

# Get bottom 20% of league for summed freq
bottom_20 = df['SummedFreq'].quantile(.2)

# Get percentage of zeros
for col in playtype_words_list:
    df.loc[(df['SummedFreq'] < bottom_20) & (df[col] == 0), col] = -20

# Get input only df
df_inputfeats = df[[i for i in df.columns.tolist() if i in playtype_words_list]]


# ------------- SELECTING 'K' IN K-MEANS THROUGH ELBOW METHOD ------------- #
print('Finding optimal number of clusters based on elbow method', '\n')

sse_list = []
feats = df_inputfeats.to_numpy()

# Sum of squared error for each 'k' between 2 and 12
for k in range(2, 12):
    model = KMeans(n_clusters=k, init='random', n_init=100, max_iter=1000, random_state=50)
    model.fit(feats)
    sse_list.append(model.inertia_)

# Find largest drop point for SSE
kl = KneeLocator(range(2, 12), sse_list, curve="convex", direction="decreasing").elbow


# ---------------- CLUSTERING & DIMENSION REDUCTION ---------------- #
print('Generate clusters with optimal number of clusters', '\n')

# Model & Output Clusters
model = KMeans(n_clusters=kl, init='random', n_init=100, max_iter=1000, random_state=50)
model.fit(feats)

df_cluscoords = df.copy()
df_cluscoords['Cluster'] = model.labels_
df_cluscoords['Cluster'] = df_cluscoords['Cluster'].astype(str)

# Feature reduction for viz
print('Reduce inputs to 2 features using PCA & Add 2 features to df', '\n')

pca = PCA(n_components=2)
principalComponents = pca.fit_transform(df_inputfeats)
principalDf = pd.DataFrame(data=principalComponents, columns=['PC1', 'PC2'])
pca_variance = pca.explained_variance_ratio_
print('Percentage of variance explained by PC1 & PC2: ', pca_variance, '\n')

# Get coords into df
df_cluscoords = pd.merge(df_cluscoords, principalDf, how='left', left_index=True, right_index=True)


# ---------------- OUTPUT ORIGINAL DATAFRAME WITH CLUSTER INFO ---------------- #
print('Outputting clustered frequencies', '\n')

# Output to GCS ; local code : # df_cluscoords.to_excel('AllSeasons_ClusteredFreqs.xlsx', index=False)
bucket_name = 'nmrankin0_nbaappfiles'
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)
bucket.blob('AllSeasons_ClusteredFreqs.csv').upload_from_string(df_cluscoords.to_csv(index=False), 'text/csv')

print('Output complete', '\n')
