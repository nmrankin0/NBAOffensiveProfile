#####################
## IMPORT PACKAGES ##
#####################
# --------- DASH MODULES --------- #
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output


# --------- OTHER MODULES --------- #
from textwrap import dedent
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import gcsfs


####################################
## COLOR SCHEME & FIGURE TEMPLATE ##
####################################
# --------- COLOR SCHEME --------- #
bgcolor = "ghostwhite"              # mapbox light map land color
bar_bgcolor = "#b0bec5"             # material blue-gray 200
bar_unselected_color = "#78909c"    # material blue-gray 400
bar_color = "#546e7a"               # material blue-gray 600
bar_selected_color = "#37474f"      # material blue-gray 800
bar_unselected_opacity = 0.8


# --------- FIGURE TEMPLATE --------- #
# Figure template
row_heights = [150, 500, 300, 600, 850]
template = {"layout": {"paper_bgcolor": bgcolor, "plot_bgcolor": bgcolor}}



####################################
## ITEMS TO BUILD DASH COMPONENTS ##
####################################
# --------- BLANK FIG --------- #
def blank_fig(height):
    """
    Build blank figure with the requested height
    """
    return {"data": [], "layout": {"height": height, "template": template, "xaxis": {"visible": False}, "yaxis": {"visible": False}}}


# --------- INFO BOX OVERLAY --------- #
def build_modal_info_overlay(id, side, content):
    """
    Build div representing the info overlay for a plot panel
    """
    div = html.Div(
        [  # modal div
            html.Div(
                        [  # content div
                            html.Div([html.H4(["Info", html.Img(id=f"close-{id}-modal", src="assets/x_circle.svg", n_clicks=0, className="info-icon", style={"margin": 0})], className="container_title", style={"color": "white"}), dcc.Markdown(content)])
                        ], className=f"modal-content {side}",
                    ),

            html.Div(className="modal")
        ],
        id=f"{id}-modal",
        style={"display": "none"},
    )

    return div


# --------- DATA FOR FILTERS/DROPDOWNS/CHARTS --------- #
# Import data
#df_clus = pd.read_excel("C:\\Users\\nrankin\\PycharmProjects\\Portfolio\\NBAOffensiveProfile\\DashApp\\Dev\\AllSeasons_ClusteredFreqs.xlsx")
#df_freq_eff = pd.read_excel("C:\\Users\\nrankin\\PycharmProjects\\Portfolio\\NBAOffensiveProfile\\DashApp\\Dev\\AllSeasons_PlayTypeStats.xlsx")

bucket_name = 'nmrankin0_nbaappfiles'

fs = gcsfs.GCSFileSystem(project='nbaoffensiveprofile', token=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
with fs.open('gs://' + bucket_name + '/AllSeasons_ClusteredFreqs.csv') as f:
    df_clus = pd.read_csv(f)

with fs.open('gs://' + bucket_name + '/AllSeasons_PlayTypeStats.csv') as f:
    df_freq_eff = pd.read_csv(f)

# Season dropdown
season_dd = df_clus['SEASON'].unique().tolist()

# Player, team, year dropdown
df_freq_eff['UniqueID'] = df_freq_eff['PLAYER'] + ' - ' + df_freq_eff['TEAM'] + ' - ' + df_freq_eff['SEASON']
player_dd = sorted(df_clus[df_clus['SEASON'] == '2022-23']['UniqueID'].tolist())

# Play types
playtype_words_list = ['Transition', 'Isolation', 'Pick & Roll Ball Handler', 'Pick & Roll Roll Man', 'Post Up', 'Spot Up', 'Handoff', 'Cut','Off Screen', 'Putbacks', 'Misc']

# --------- PLAYER PLAY-TYPE SCATTER-PLOT --------- #
# Get 20+ colors for clusters
clus_color_list = px.colors.qualitative.Plotly + px.colors.qualitative.T10

# Create scatter trace for each cluster
fig_scatter = go.Figure()
clus_num_iter = 0
for clus in sorted(df_clus['Cluster'].unique().tolist()):
    for player_unq_id in df_clus[df_clus['Cluster'] == clus]['UniqueID'].tolist():
        x = df_clus[df_clus['UniqueID'] == player_unq_id]['PC1']
        y = df_clus[df_clus['UniqueID'] == player_unq_id]['PC2']
        name = df_clus[df_clus['UniqueID'] == player_unq_id]['UniqueID'].tolist()[0]

        fig_scatter.add_trace(go.Scatter(x=x, y=y, mode='markers', name=name, showlegend=False, hoverinfo='text', hovertext=name, marker=dict(color=clus_color_list[clus_num_iter])))

    # Add legend entry
    fig_scatter.add_trace(go.Scatter(x=[None], y=[None], name=('Cluster' + str(clus_num_iter+1)), mode='markers', marker=dict(color=clus_color_list[clus_num_iter])))

    # Iterate for next clus
    clus_num_iter += 1


# Remove axes
#x axis
fig_scatter.update_xaxes(visible=False)
fig_scatter.update_yaxes(visible=False)

# Change Plot & BG Color
fig_scatter.update_layout(margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor='ghostwhite', plot_bgcolor='ghostwhite')           # 'aliceblue' is closer to default color

# Increase Marker Size
fig_scatter.update_traces(marker=dict(size=10, line=dict(width=1, color='DarkSlateGrey')))


#####################
## DASH APP LAYOUT ##
#####################
# Build Dash layout
app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.Div(
            [
                html.H1(children=
                            [
                            "NBA Offensive Profile Explorer",
                            #html.A(html.Img(src="assets/flamingball.png", style={"float": "right", "height": "50px"})),
                            ], style={"text-align": "left"}
                        )
            ]
        ),
        html.Div(
            children=[
                build_modal_info_overlay("cluster", "bottom", dedent(
                """
                The _**Clustering**_ panel displays how similar players are to one another based on their offensive profile.
                
                A player's _**offensive profile**_ is determined based on how often they engage in each of the following offensive _**play-types**_:
                - Transition, Isolation, Pick & Roll Ball Handler, Pick & Roll Roll Man, Post Up, Spot Up, Handoff, Cut, Off Screen, Putbacks, Misc
                
                
                Each circle represents a player. Each circle color represents a different offensive profile archetype.
                
                **In most cases**, circles within close proximity to one another show player with a high  similarity in offensive profile. 
                """
                    )
                ),

                build_modal_info_overlay("frequency", "top", dedent(
                """
                The _**Frequency**_ panel will populate after the user selects a player (or players) within the _**'Select Players from Season(s)' dropdown**_.
                
                - For each selected player, the bar chart is sliced by _**offensive play-type**_ and displays how frequently each selected player engages in each applicable play-type
                
                """
                    )
                ),

                build_modal_info_overlay("efficiency", "top", dedent(
                """
                The _**Efficiency**_ panel will populate after the user selects a player (or players) within the _**'Select Players from Season(s)' dropdown**_.
                
                - For each selected player, a bar is generated for each applicable offensive play-type. The bar depicts the selected player's _**Points Per Possession Percentile**_ for a given play-type
                    - For example, if player 'X' has a _**Points Per Possession Percentile**_ value of _**92**_ for _**Post-Up**_ plays, that would indicate that, as compared to player 'X', _**92%**_ of players in the NBA achieve less points per possessions when 'posting-up'
                    - All _**Points Per Possession Percentile**_ values are calculated relative to the selected season (i.e., 2021-22 season percentiles are determined solely based on the 2021-22 season)
                    - The _**Thickness**_ of each bar reflects how frequently the player engages in the play-type. The _**thicker**_ the bar, the more often the player engages in that play-type
                """
                    )
                ),

                # Banner
                html.Div(children=
                    [
                    html.Div(children=[html.H6("Select Season(s)"), dcc.Dropdown(id='season-dd', options=season_dd, clearable=False, value=['2022-23', '2021-22'], multi=True,  placeholder="Select 1 or More Seasons")], className="four columns pretty_container"),
                    html.Div(children=[html.H6("Select Players from Season(s)"), dcc.Dropdown(id='player-dd', options=player_dd, multi=True, placeholder="Select 1 or More Players")], className="eight columns pretty_container", style={'display': 'inline-block'})
                    ]
                ),

                # Cluster visual
                html.Div(children=[html.H4(["Clustering Players based on Offensive Play-Type Frequency", html.Img(id="show-cluster-modal", src="assets/question_circle.png", className="info-icon")], className="container_title"), html.Div(id="player-scatter-container", children=[dcc.Graph(id="player-scatter", figure=fig_scatter, config={"displayModeBar": False})])], className="twelve columns pretty_container", style={"width": "98%", "margin-right": "0"}, id="cluster-div"),

                # Frequency & efficiency visuals
                html.Div(children=
                            [
                            html.Div(children=[html.H4(["Selected Players - Frequency by Offensive Play-Type", html.Img(id="show-frequency-modal", src="assets/question_circle.png", className="info-icon")], className="container_title"), html.Div(id="player-freq-container", children=[dcc.Graph(id="freq-viz", figure=blank_fig(row_heights[3]), config={"displayModeBar": False})])], className="six columns pretty_container", id="frequency-div"),
                            html.Div(children=[html.H4(["Selected Players - Efficiency by Offensive Play-Type", html.Img(id="show-efficiency-modal", src="assets/question_circle.png", className="info-icon")], className="container_title"), html.Div(id="player-eff-container", children=[dcc.Graph(id="eff-viz", figure=blank_fig(row_heights[3]), config={"displayModeBar": False})])], className="six columns pretty_container", id="efficiency-div"),
                            ]
                        ),
            ]
        ),

        # App Details
        html.Div([html.H4("Dashboard Details", style={"margin-top": "0"}), dcc.Markdown(
        """
         - Dashboard written in Python using the [Dash](https://dash.plot.ly/) web framework, leveraging [Elliot Gunn's] (https://github.com/elliotgunn) World Cell Tower's Dashboard CSS
         - Data is sourced from [NBA.com's Play-Type Stats] (https://www.nba.com/stats/players/isolation)
         - Currently, the data in this app is static. The data will soon be updated on a daily basis using [Docker] (https://docs.docker.com/) and [Google Cloud Platform's Compute Engine] (https://cloud.google.com/compute)
         - Play-Type frequency clusters are computed using the [K-Means Algorithm] (https://en.wikipedia.org/wiki/K-means_clustering) from the sklearn python module
         - Play-Type frequency clusters are visualized using [Principal Component Analysis] (https://en.wikipedia.org/wiki/Principal_component_analysis) from the sklearn python module
        """
        )], style={"width": "98%", "margin-right": "0", "padding": "5px"}, className="twelve columns pretty_container"),
    ]
)


################################
## CREATE CALLBACKS & RUN APP ##
################################
# ------------- MODAL INFO QUESTION BUTTON CALLBACKS ------------- #
for id in ["cluster", "frequency", "efficiency"]:
    @app.callback(
        [Output(f"{id}-modal", "style"), Output(f"{id}-div", "style")],
        [Input(f"show-{id}-modal", "n_clicks"), Input(f"close-{id}-modal", "n_clicks")] )
    def toggle_modal(n_show, n_close):
        # Enable us to check what button was clicked
        ctx = dash.callback_context

        # If its one of the modal buttons, display the block of text
        if ctx.triggered and ctx.triggered[0]["prop_id"].startswith("show-"):
            return {"display": "block"}, {"zIndex": 1003}
        else:
            return {"display": "none"}, {"zIndex": 0}


# ------------- SEASONS FILTER CALLBACKS ------------- #
# Update season filter to always default to current season if it is nullified
@app.callback(Output('season-dd', 'value'), [Input('season-dd', 'value')])
def update_season_dd(sel_season_val_list):
    # Get dropdown value on app initialization. It initiates as string so we need to make into list
    if type(sel_season_val_list) == str or not sel_season_val_list:
        return ['2022-23']
    else:
        return sel_season_val_list


# Filter Player Dropdown based on selected season
@app.callback(Output('player-dd', 'options'), [Input('season-dd', 'value')])
def update_player_dd(sel_season_val_list):
    # Get dropdown value on app initialization. It initiates as string so we need to make into list
    if type(sel_season_val_list) == str:
        sel_season_val_list = ['2022-23']
    else:
        pass

    # Filter df based on selection and update dropdown
    df_filtered = df_clus[df_clus['SEASON'].isin(sel_season_val_list)]
    updated_player_dd = sorted(df_filtered['UniqueID'].tolist())
    return updated_player_dd


# ------------- SCATTER PLOT VISUAL CALLBACKS ------------- #
# Update cluster scatter plot based on selected season
@app.callback(Output('player-scatter-container', 'children'), [Input('season-dd', 'value'), Input('player-dd', 'value')])
def update_scatter(sel_season_val_list, sel_player_val_list):
    # Get dropdown value on app initialization. It initiates as string so we need to make into list
    if type(sel_season_val_list) == str:
        sel_season_val_list = ['2022-23']
    else:
        pass


    # WHEN THERE IS A VALUE IN SEASON DD (CONSTANT) ; NO VALUE IN PLAYER DD
    if sel_season_val_list and not sel_player_val_list:

        # Filter df based on selection and update dropdown
        df_filtered = df_clus[df_clus['SEASON'].isin(sel_season_val_list)]

        # Get 20+ colors for clusters
        clus_color_list = px.colors.qualitative.Plotly + px.colors.qualitative.T10

        # Create scatter trace for each cluster
        fig_scatter = go.Figure()
        clus_num_iter = 0
        for clus in sorted(df_filtered['Cluster'].unique().tolist()):
            for player_unq_id in df_filtered[df_filtered['Cluster'] == clus]['UniqueID'].tolist():
                x = df_filtered[df_filtered['UniqueID'] == player_unq_id]['PC1']
                y = df_filtered[df_filtered['UniqueID'] == player_unq_id]['PC2']
                name = df_filtered[df_filtered['UniqueID'] == player_unq_id]['UniqueID'].tolist()[0]

                fig_scatter.add_trace(go.Scatter(x=x, y=y, mode='markers', name=name, showlegend=False, hoverinfo='text', hovertext=name, marker=dict(color=clus_color_list[clus_num_iter])))

            # Add legend entry
            fig_scatter.add_trace(go.Scatter(x=[None], y=[None], name=('Cluster' + str(clus_num_iter+1)), mode='markers', marker=dict(color=clus_color_list[clus_num_iter])))

            # Iterate for next clus
            clus_num_iter += 1

        # Remove axes
        #x axis
        fig_scatter.update_xaxes(visible=False)
        fig_scatter.update_yaxes(visible=False)

        # Change Plot & BG Color
        fig_scatter.update_layout(margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor='ghostwhite', plot_bgcolor='ghostwhite')           # 'aliceblue' is closer to default color

        # Increase Marker Size
        fig_scatter.update_traces(marker=dict(size=10, line=dict(width=1, color='DarkSlateGrey')))

        # return
        return [dcc.Graph(id="player-scatter", figure=fig_scatter, config={"displayModeBar": False})]

    # WHEN THERE IS A VALUE IN SEASON DD (CONSTANT) ; AND A VALUE IN PLAYER DD
    elif sel_season_val_list and sel_player_val_list:
        # Update current player drop down value based on season value
        updated_player_list = []
        for player in sel_player_val_list:
            for season in sel_season_val_list:
                if season in player:
                    updated_player_list.append(player)
                    continue

        # Highlight selected players
        if updated_player_list is not None:

            # Filter df based on selection and update dropdown
            df_filtered = df_clus[df_clus['SEASON'].isin(sel_season_val_list)]

            # Get 20+ colors for clusters
            clus_color_list = px.colors.qualitative.Plotly + px.colors.qualitative.T10

            # Create scatter trace for each cluster
            fig_scatter = go.Figure()
            clus_num_iter = 0
            for clus in sorted(df_filtered['Cluster'].unique().tolist()):
                for player_unq_id in df_filtered[df_filtered['Cluster'] == clus]['UniqueID'].tolist():
                    x = df_filtered[df_filtered['UniqueID'] == player_unq_id]['PC1']
                    y = df_filtered[df_filtered['UniqueID'] == player_unq_id]['PC2']
                    name = df_filtered[df_filtered['UniqueID'] == player_unq_id]['UniqueID'].tolist()[0]

                    fig_scatter.add_trace(go.Scatter(x=x, y=y, mode='markers', name=name, showlegend=False, hoverinfo='text', hovertext=name, marker=dict(color=clus_color_list[clus_num_iter])))

                # Add legend entry
                fig_scatter.add_trace(go.Scatter(x=[None], y=[None], name=('Cluster' + str(clus_num_iter+1)), mode='markers', marker=dict(color=clus_color_list[clus_num_iter])))

                # Iterate for next clus
                clus_num_iter += 1

            # Remove axes
            #x axis
            fig_scatter.update_xaxes(visible=False)
            fig_scatter.update_yaxes(visible=False)

            # Change Plot & BG Color
            fig_scatter.update_layout(margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor='ghostwhite', plot_bgcolor='ghostwhite')           # 'aliceblue' is closer to default color

            # Increase Marker Size
            fig_scatter.update_traces(marker=dict(size=10, line=dict(width=1, color='DarkSlateGrey')))

            # Create new fig as copy of orig
            new_fig_scatter = fig_scatter

            # For each player that was selected, highlight them, otherwise use original marker formatting
            new_fig_scatter.for_each_trace(lambda trace: trace.update(marker=dict(size=15, line=dict(width=5.5,color='#F8EE35'))) if trace.name in updated_player_list else trace.update(marker=dict(size=10, line=dict(width=1, color='DarkSlateGrey'))))

            # Return updated fig
            return [dcc.Graph(id="player-scatter", figure=new_fig_scatter, config={"displayModeBar": False})]


    else:
        # this condition shouldn't ever hit
        return [dcc.Graph(id="player-scatter", figure=blank_fig(row_heights[3]), config={"displayModeBar": False})]


# ------------- PLAYER FILTER CALLBACKS ------------- #
# Update Frequency Graph based on selected player
@app.callback(Output('player-freq-container', 'children'), [Input('season-dd', 'value'), Input('player-dd', 'value')])
def show_freq_graph(sel_season_val_list, sel_player_val_list):

    # Update current player drop down value based on season value
    if sel_player_val_list:
        updated_player_list = []
        for player in sel_player_val_list:
            for season in sel_season_val_list:
                if season in player:
                    updated_player_list.append(player)
                    continue
    else:
        updated_player_list = None

    # If player(s) is selected, put them into graph
    if updated_player_list is not None:
        df_update = df_freq_eff[df_freq_eff['UniqueID'].isin(updated_player_list)]
        new_fig_freq = px.bar(df_update, x="UniqueID", y="Freq%", color="PlayType", labels={'x': 'PLAYER'}, color_discrete_sequence=px.colors.qualitative.Vivid, text=df_update["Freq%"].apply(lambda x: '{0:1.2f}%'.format(x)))

        # Change Plot & BG Color
        new_fig_freq.update_layout(margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor='ghostwhite', plot_bgcolor='ghostwhite')

        return [dcc.Graph(id="freq-viz", figure=new_fig_freq, config={"displayModeBar": False})]

    # if no players are selected, leave graph empty
    else:
        return [dcc.Graph(id="freq-viz", figure=blank_fig(row_heights[3]), config={"displayModeBar": False})]


# Update Efficiency Graph based on selected player
@app.callback(Output('player-eff-container', 'children'),  [Input('season-dd', 'value'), Input('player-dd', 'value')])
def show_eff_graph(sel_season_val_list, sel_player_val_list):
    # Update current player drop down value based on season value
    if sel_player_val_list:
        updated_player_list = []
        for player in sel_player_val_list:
            for season in sel_season_val_list:
                if season in player:
                    updated_player_list.append(player)
                    continue
    else:
        updated_player_list = None

    # If player(s) is selected, put them into graph
    if updated_player_list is not None:
        # Filter df
        df_update = df_freq_eff[df_freq_eff['UniqueID'].isin(updated_player_list)]
        sel_uniqid_list = df_update['UniqueID'].unique().tolist()

        # Empty graph
        new_fig_eff = go.Figure(data=[])

        # For each selected player, update the graph with their stats
        for uid in sel_uniqid_list:
            player = df_update[df_update['UniqueID'] == uid]['PLAYER'].unique().tolist()[0]

            ppp_list = []
            freq_list = []
            exlude_playtype_list = []
            for playtype in playtype_words_list:
                # Check if any players in selection have a frequency value within the play type. If not, do not include in graph
                if df_update[(df_update['UniqueID'].isin(sel_uniqid_list)) & (df_update['PlayType'] == playtype)].empty:
                    exlude_playtype_list.append(playtype)
                    continue

                # Add a try for if there is no value for that play type
                try:
                    ppp = df_update[(df_update['UniqueID'] == uid) & (df_update['PlayType'] == playtype)]['Percentile'].values[0]
                    freq = df_update[(df_update['UniqueID'] == uid) & (df_update['PlayType'] == playtype)]['Freq%'].values[0]
                except IndexError as e:
                    ppp = None
                    freq = 0

                # Add stat to stat list
                ppp_list.append(ppp)
                freq_list.append(freq)

            # Rescale bar widths based on frequency
            scaler = 0.009
            scaled_freq_list = [i * scaler if i != 0 and i * scaler > 0.005 else 0.005 for i in freq_list]

            # Prep x-axis with exclusions
            filt_playtype_words_list = [i for i in playtype_words_list if i not in exlude_playtype_list]

            # Add player data to fig
            new_fig_eff.add_trace(go.Bar(name=uid, x=filt_playtype_words_list, y=ppp_list, width=scaled_freq_list, text=[str(i) + '%' if i is not None else '' for i in ppp_list],  textposition="outside"))

            # Change Plot & BG Color
            new_fig_eff.update_layout(margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor='ghostwhite', plot_bgcolor='ghostwhite', yaxis_title="Points Per Possession Percentile", xaxis_title="Play-Type", legend=dict(yanchor="top", orientation="h", y=1.1, xanchor="left", x=0.01), uniformtext=dict(minsize=12, mode='show'))           # 'aliceblue' is closer to default color

        return [dcc.Graph(id="eff-viz", figure=new_fig_eff, config={"displayModeBar": False})]

    # if no players are selected, leave graph empty
    else:
        return [dcc.Graph(id="eff-viz", figure=blank_fig(row_heights[3]), config={"displayModeBar": False})]


# ------------- NEEDED TO RUN APP ------------- #
# Run the server
if __name__ == "__main__":
    app.run_server(debug=False)
