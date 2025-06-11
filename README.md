![image](https://github.com/user-attachments/assets/50ad5254-7f82-43ad-89fb-803fad689346)# glowing-engine
Text-To-SQL Playground

[![Watch the video](https://raw.githubusercontent.com/tituslhy/glowing-engine/main/images/bullrun_thumbnail.png)](https://raw.githubusercontent.com/tituslhy/glowing-engine/main/media/bullrun_app.mp4)

## Setup
This repository uses the [uv package installer](https://docs.astral.sh/uv/pip/packages/). 

To create a virtual environment with the dependencies installed, simply type in your terminal:
```
uv sync
```

You'll need to ingest the data into an SQLite database before you can interact with the app. Simply run the codes in `./notebooks/setup_db.ipynb` to ingest the ticker information from Yahoo Finance.

## To run Chainlit app
This spins up your application on port 8000
```
chainlit run app.py
```
