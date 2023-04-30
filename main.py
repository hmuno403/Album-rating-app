from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import pandas as pd
import streamlit as st
from PIL import Image
import requests
from io import BytesIO
from pathlib import Path
import pandas as pd
import numpy as np


load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return{"Authorization": "Bearer " + token}

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]

    if len(json_result) == 0:
        st.write("No artist with this name exist...")
        return None

    artist = json_result[0]
    artist_image_url = artist['images'][0]['url'] if artist['images'] else None
    return artist, artist_image_url

def search_for_album(token, album_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={album_name}&type=album&limit=30"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["albums"]["items"]

    if len(json_result) == 0:
        st.write("No album with this name exist...")
        return None

    return json_result

def get_albums_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    headers = get_auth_header(token)
    query = f"?limit=20"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["items"]

    if len(json_result) == 0:
        st.write("No albums found for this artist...")
        return None

    return json_result

def get_album_info(token, album_id):
    url = f"https://api.spotify.com/v1/albums/{album_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)

    if result.status_code == 200:
        json_result = json.loads(result.content)
        album_name = json_result["name"]
        release_date = json_result["release_date"]
        total_tracks = json_result["total_tracks"]
        artist_name = json_result["artists"][0]["name"]
        cover_art_url = json_result["images"][1]["url"]

        st.write(f"Album: {album_name}")
        st.write(f"Artist: {artist_name}")
        st.write(f"Release date: {release_date}")
        st.write(f"Total tracks: {total_tracks}")

        return {
            'cover_art_url': cover_art_url,
            'album_name': album_name,
            'artist_name': artist_name,
            'release_date': release_date,
            'total_tracks': total_tracks,
    },  cover_art_url 
    else:
        st.write("Error retrieving album info")
        return None
    
def get_tracklist_as_dict(token, album_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    res = get(url, headers=headers)
    tracks_data = res.json()

    tracklist = []

    for i, track in enumerate(tracks_data["items"]):
        duration_minutes, duration_seconds = divmod(track["duration_ms"] // 1000, 60)
        duration_str = f"{duration_minutes}:{duration_seconds:02}"
        track_info = {
            "Track Number": i + 1,
            "Track Name": track["name"],
            "Duration": duration_str,
        }
        tracklist.append(track_info)

    return tracklist
    
def display_cover_art(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img = img.resize((300, 300), Image.LANCZOS)
    st.image(img, caption="Album Cover Art")
     

def get_tracklist(token, album_id):
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    headers = get_auth_header(token)
    result = get(url, headers=headers)

    if result.status_code == 200:
        json_result = json.loads(result.content)
        tracks = json_result["items"]
        track_inputs = []
        for idx, track in enumerate(tracks):
            track_text = f"{idx + 1}. {track['name']}"
            track_input = st.text_input(track_text, key=f'track_{idx}')
            track_inputs.append(track_input)
        return track_inputs
    else:
        st.write("Error retrieving tracklist")

def get_artist_top_tracks(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    headers = get_auth_header(token)
    params = {"market": "US"}  # You can change the market as needed
    result = get(url, headers=headers, params=params)

    if result.status_code == 200:
        json_result = json.loads(result.content)
        tracks = json_result["tracks"]
        top_tracks = [{"name": track["name"], "popularity": track["popularity"]} for track in tracks[:10]]
        return top_tracks
    else:
        st.write("Error retrieving top tracks")
        return None
    
def clean_artist_name(artist_name):
    cleaned_name = artist_name.replace('_', ' ')
    cleaned_name = cleaned_name.replace('track data', '')
    cleaned_name = cleaned_name.replace('data track', '').strip()  # Add this line
    return cleaned_name

def clean_album_name(album_name):
    cleaned_name = album_name.replace('track data', '')
    cleaned_name = cleaned_name.replace('data track', '').strip()
    return cleaned_name

def display_tracklist_without_scores(tracklist):
    for track in tracklist:
        if 'name' in track and 'artist' in track:
            print(track['name'], '-', track['artist'])
        else:
            print('Invalid track data')
       

def save_data_to_csv(df, album_name, artist_name):
    cleaned_artist_name = clean_artist_name(artist_name)
    cleaned_album_name = album_name.replace(" ", "_").replace("-", "_")
    filename = f"{cleaned_album_name}_{cleaned_artist_name}_track_data.csv"
    df['Album'] = album_name  # Add the album name to the DataFrame
    df['Artist'] = artist_name  # Add the artist name to the DataFrame
    df.to_csv(filename, index=False)
    return filename

def load_data_from_csv(album_name, artist_name):
    cleaned_artist_name = clean_artist_name(artist_name)
    filename = f"{album_name}_{cleaned_artist_name}_track_data.csv".replace(" ", "_")
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return None            

def process_filename(filename):
    # Remove the "_track_data.csv" part from the filename
    filename = filename.replace("_track_data.csv", "")

    # Split the filename based on the first occurrence of "track_data"
    album_parts, artist_parts = filename.split("track_data", 1)

    # Split the album and artist parts by underscores
    album_parts = album_parts.split("_")
    artist_parts = artist_parts.split("_")

    # Join the parts and replace underscores with spaces
    album = " ".join(album_parts).replace("-", " ").strip()
    artist = " ".join(artist_parts).replace("-", " ").strip()

    return album, artist

# retrieve all the CSV files in the current directory
csv_files = list(Path(".").glob("*_track_data.csv"))

# create an empty list to store the sorted album scores
sorted_album_scores = []

# read each CSV file and calculate the average score
for file in csv_files:
    data = pd.read_csv(file)
    # album, artist = process_filename(file.stem)
    album = data.at[0,'Album']  # Get the album name from the DataFrame
    artist = data['Artist'][0]  # Get the artist name from the DataFrame
    avg_score = data["Average Score"].mean()

    # append the album score to the list
    sorted_album_scores.append({"Album": album, "Artist": artist, "Average Score": avg_score})

# sort the album scores by average score (descending)
sorted_album_scores = sorted(sorted_album_scores, key=lambda x: x["Average Score"], reverse=True)

# add position numbers
for i, album_score in enumerate(sorted_album_scores):
    album_score["Position Number"] = i + 1

# display the sorted list of album scores
for album_score in sorted_album_scores:
    print(f"{album_score['Position Number']}\t{album_score['Album']}\t{album_score['Artist']}\t{album_score['Average Score']:.4f}")

# def display_album_scores():
#     st.title("Top Albums")
#     st.write("List of processed albums and their average scores:")

#     # Retrieve all CSV files
#     csv_files = list(Path(".").glob("*_track_data.csv"))

#     # Create an empty DataFrame to store album scores
#     album_scores = pd.DataFrame(columns=["Artist", "Album", "Average Score"])

#     # Read each CSV file and calculate the average score
#     for file in csv_files:
#         data = pd.read_csv(file)

#         if 'Album' not in data.columns or 'Artist' not in data.columns or 'Average Score' not in data.columns:
#             st.write(f"Error: One or more required columns are missing in {file}. Make sure the 'Album', 'Artist', and 'Average Score' columns exist in the file.")
#             continue

#         album = data.at[0, 'Album']  # Get the album name from the DataFrame
#         artist = data.at[0, 'Artist']  # Get the artist name from the DataFrame
#         avg_score = data["Average Score"].mean()

#         # append the album score to the list
#         album_scores = album_scores.append({"Artist": artist, "Album": album, "Average Score": avg_score}, ignore_index=True)

#     # Sort the DataFrame by average score (descending)
#     sorted_album_scores = album_scores.sort_values(by="Average Score", ascending=False)

#     # Add position numbers
#     sorted_album_scores.insert(0, "Position Number", range(1, len(sorted_album_scores) + 1))

#     # Display the sorted list of album scores
#     df = pd.DataFrame(sorted_album_scores, columns=['Position Number', 'Album', 'Artist', 'Average Score'])
#     st.table(df)

def display_album_scores():
    st.title("Top Albums")
    st.write("List of processed albums and their average scores:")

    # Retrieve all CSV files
    csv_files = list(Path(".").glob("*_track_data.csv"))

    # Create an empty DataFrame to store album scores
    album_scores = pd.DataFrame(columns=["Artist", "Album", "Average Score"])

    # Read each CSV file and calculate the average score
    for file in csv_files:
        data = pd.read_csv(file)

        if 'Album' not in data.columns or 'Artist' not in data.columns or 'Average Score' not in data.columns:
            st.write(f"Error: One or more required columns are missing in {file}. Make sure the 'Album', 'Artist', and 'Average Score' columns exist in the file.")
            continue

        album = data.at[0, 'Album']  # Get the album name from the DataFrame
        artist = data.at[0, 'Artist']  # Get the artist name from the DataFrame
        avg_score = data["Average Score"].mean()

        # Append the album score to the DataFrame
        # album_scores = album_scores.append({"Artist": artist, "Album": album, "Average Score": avg_score}, ignore_index=True)
        album_scores = pd.concat([album_scores, pd.DataFrame({"Artist": [artist], "Album": [album], "Average Score": [avg_score]})], ignore_index=True)


    # Sort the DataFrame by average score (descending)
    sorted_album_scores = album_scores.sort_values(by="Average Score", ascending=False)

    # Add position numbers
    sorted_album_scores.insert(0, "Position Number", range(1, len(sorted_album_scores) + 1))

    # Display the sorted list of album scores
    df = pd.DataFrame(sorted_album_scores, columns=['Position Number', 'Album', 'Artist', 'Average Score'])
    st.table(df)
    st.markdown(get_csv_download_link(df, "top_rated_albums"), unsafe_allow_html=True)



def load_css(css_file):
    with open(css_file) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def get_csv_download_link(df, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download CSV file</a>'
    return href


st.set_page_config(page_title="Music Review App", page_icon=":musical_note:", layout="wide")

def app(display_average_scores_button):

    token = get_token()

    # st.set_page_config(page_title="Music Review App", page_icon=":musical_note:", layout="wide")

    st.markdown(
        """
        <h1 class="app-title">
            <span class="title-upper-line">Justin and Hector's</span><br>
            <span class="title-lower-line">MUSIC RATING APP</span>
        </h1>
        """,
        unsafe_allow_html=True
    )

    load_css("style.css")

    search_type = st.radio(
        "", 
        ("artist", "album", "quit"),
        
    )
    
    # display_average_scores_button = st.button("Top Rated Albums")
    

    search_query = st.text_input("Enter artist or album:")
    df = None

    if search_query or display_average_scores_button:

        if display_average_scores_button:
            display_album_scores()

    if search_type == 'quit':
        st.write("Exiting the app.")
        return

    if search_query:

        if search_type == 'artist':
            artist, artist_image_url = search_for_artist(token, search_query)
            if artist:
                artist_id = artist["id"]
                albums = get_albums_by_artist(token, artist_id)
                artist_info_col, artist_image_col = st.columns(2) #added this 

                with artist_info_col:

                    st.write(f"Artist: {artist['name']}")
                    st.write(f"Followers: {artist['followers']['total']}")
                    st.write(f"Monthly Listeners: {artist['popularity']}")  # Popularity is a proxy for monthly listeners


                if artist_image_url:
                    with artist_image_col:
                        st.image(artist_image_url, caption=f"Artist: {artist['name']}", width=200)

                top_tracks = get_artist_top_tracks(token, artist_id)
                if top_tracks:
                    st.write("Top 10 Tracks:")
                    for i, track in enumerate(top_tracks):
                        st.write(f"{i + 1}. {track['name']} (Popularity: {track['popularity']})")
                else:
                     st.write("No top tracks found for this artist")
                selected_album = st.selectbox("Select an album:", [album['name'] for album in albums])
                selected_album_idx = [album['name'] for album in albums].index(selected_album)
                album_id = albums[selected_album_idx]["id"]
                album_info = get_album_info(token, album_id)
                
                if album_info:
                    st.image(album_info[0]['cover_art_url'], caption=f"Album: {album_info[0]['album_name']} by {album_info[0]['artist_name']}", width=300)
                    tracklist = get_tracklist_as_dict(token, album_id)
                    tracklist_df = pd.DataFrame(tracklist)
                    st.write("Tracklist:")
                    st.write(tracklist_df)
                else:
                    st.write("No album selected")

            else:
                st.write("Artist not found.")

        elif search_type == 'album':
            albums = search_for_album(token, search_query)
            if albums:
                selected_album = st.selectbox("Select an album:", [f"{album['name']} - {album['artists'][0]['name']}" for album in albums])
                selected_album_idx = [f"{album['name']} - {album['artists'][0]['name']}" for album in albums].index(selected_album)
                album_id = albums[selected_album_idx]["id"]
                album_info, album_image_url = get_album_info(token, album_id)
                display_cover_art(album_image_url)
                tracklist = get_tracklist_as_dict(token, album_id)
                display_tracklist_without_scores(tracklist)

                # Create a DataFrame
                data = {'Track Number': [track['Track Number'] for track in tracklist],
                        'Track Name': [track['Track Name'] for track in tracklist],
                        'Duration': [track['Duration'] for track in tracklist]}
                df = pd.DataFrame(data)

                # Add a new column to store the input data
                df["Justin's Score"] = ''
                df["Hector's Score"] = ''

                # df["Justin's Score"] = None
                # df["Hector's Score"] = None

                # Initialize variables to store the sum
                            # of scores
                total_score_justin = 0
                total_score_hector = 0

                # Loop through each track and gather input
                for index, row in df.iterrows():

                    with st.container():
                        column1, column2 = st.columns(2)

                        with column1:
                            justin_score = st.number_input(f"Enter Justin's score for {row['Track Name']}:", key=f"justin_input_{index}", format="%.2f")
                        with column2:
                            hector_score = st.number_input(f"Enter Hector's score for {row['Track Name']}:", key=f"hector_input_{index}", format="%.2f")
                         
                        

                # justin_input_container = st.container()
                # hector_input_container = st.container()

                # Add the input values to their respective sums
                    total_score_justin += justin_score
                    total_score_hector += hector_score

                # Store the input values in the DataFrame
                if justin_score != 0:
                    df.loc[index, "Justin's Score"] = justin_score
                if hector_score != 0:    
                    cledf.loc[index, "Hector's Score"] = hector_score

                # Compute the average score for the album
                average_score = (total_score_justin + total_score_hector) / (2 * len(tracklist))

                # Display the average score
                st.write(f"Average Score for the Album: {average_score:.2f}")

                # Store the average score in the DataFrame
                df.loc[:, "Average Score"] = average_score

                # Add this line to create a download link for the user input data
                st.markdown(get_csv_download_link(df, "user_input_data"), unsafe_allow_html=True)

                # Load the data from the CSV file, if it exists
                loaded_df = load_data_from_csv(album_info['album_name'], album_info['artist_name'])
                if loaded_df is not None:
                    st.write("Loaded data from the saved CSV file:")
                    st.write(loaded_df)
                    loaded_avg_score = loaded_df['Average Score'].iloc[0]
                    st.write(f"Loaded Average Score for the Album: {loaded_avg_score:.2f}")
                else:
                    st.write(df)

                save_button = st.button("Save data to CSV")

                if save_button:
                    if df is not None:
                        saved_filename = save_data_to_csv(df, album_info['album_name'], album_info['artist_name'])
                        st.write(f"Data saved to {saved_filename}")
            else:
                st.write("Album not found")

if __name__ == "__main__":
    display_average_scores_button = st.button("Top Rated Albums")
    app(display_average_scores_button)
    # app()

