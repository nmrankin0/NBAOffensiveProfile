
# NBA Offensive Profile Explorer

## Web Application
Web App Link: [Explore NBA Player Offensive Profiles Here](http://nmrankin0.pythonanywhere.com/)

## About the Application
The purpose of this project is to generate a web application where NBA fans can explore the similarities and difference between different player's offensive profiles.

**-"How has James role and efficiency changed since he was traded to Philadelphia?"**

**-"What player's offensive play-style is most similar to Scottie Barnes'?"**

**-"Who is a better offensive role player, Duncan Robinson or Grayson Allen?"**

**These are all questions that can be explored using this web application**

This is achieved through clustering NBA player's based on how often they engage in each of the following offensive _**play-types**_:  
- Transition, Isolation, Pick & Roll Ball Handler, Pick & Roll Roll Man, Post Up, Spot Up, Handoff, Cut, Off Screen, Putbacks, Misc

Users can then select players to their play-type frequencies and efficiencies.

**FOR MORE INFORMATION, AND TO LEARN HOW TO USE THE WEB APP, PLEASE VISIT THE WEB APP LINK ABOVE AND CLICK ON THE QUESTION MARK SYMBOLS:**

![image](https://user-images.githubusercontent.com/45741484/211229197-2e29ad91-0f0d-4f05-9f84-228d74185142.png)


## Project Structure
[Data Collection & Analysis Folder](https://github.com/nmrankin0/NBAOffensiveProfile/tree/main/DataCollectionAndAnalysis):

- Contains files used to collect the data, manipulate the data, and generate player clusters
- Each .py file contains more details about the program within the file
- Most of these programs output data to **Google Cloud Storage** for later consumption by the web application

[Web Application Folder](https://github.com/nmrankin0/NBAOffensiveProfile/tree/main/WebApplication):

- Contains files used to generate the web application
- Application is currently hosted on [PythonAnywhere](https://www.pythonanywhere.com/)


## Project Process Flow
1. Gather play-type frequency data for each play-type from https://www.nba.com/stats/players/isolation and store the dataframes in Google Cloud Storage.

2. Collect, manipulate, and transform the stored dataframes to prepare the data for clustering.

3. Identify the optimal number of clusters using the elbow-method and perform K-Means clustering.

4. Reduce the 11 inputs used for clustering (i.e., play-type frequencies) down to 2 dimensions using PCA for the purpose of cluster visualization.

5. Display the cluster visualization and the accompanying play-type frequency and efficiency visuals within the web application.
