# Football Scout

Football Scout is a **data-driven scouting web application** that compares and ranks football players across multiple leagues according to a criteria that the user can adjust.  
It consolidates detailed player statistics from [FBref](https://fbref.com) and market values from [Transfermarkt](https://www.transfermarkt.com), providing interactive tools for player discovery and analysis.

The project is built in **Python** and deployed with **Streamlit Cloud**.

👉 [**Try it live here**](https://scout-football.streamlit.app/)

---

## 🚀 Features

- **Top Players Ranking**  
  Rank players by custom metrics (e.g. passing, shooting, defensive actions) and filter by age, position, or league.

- **Radar Comparison**  
  Compare players head-to-head with customizable radar charts.

- **Market Value Integration**  
  Automatically retrieves player market values from Transfermarkt.

- **League Filters**  
  Select one or multiple leagues to explore specific markets.

- **Interactive Web UI**  
  Built with Streamlit for fast deployment and easy use.

---

## 🏗️ Project Structure

football_scout/
│
├── assets/                   # Stored datasets and static files
│
├── scout_core/               # Core logic
│   ├── __init__.py
│   ├── data.py               # Dataset already scraped, cleaned and processed
│   ├── market_value.py       # Market value scraper (may fail in public envs)
│   ├── radar.py              # Radar chart generation
│   └── ranking.py            # Ranking players by metrics
│
├── 1. Data Collection.ipynb       # Data scraping
├── 2. Data Cleaning and EDA.ipynb # Cleaning & exploratory analysis
├── 3. Scout.ipynb                  # Defining scouting rules
├── 4. Web App.ipynb                # Testing scout and developing the Streamlit app
│
├── app.py                   # Streamlit app entry point
├── requirements.txt         # Project dependencies
├── runtime.txt              # Runtime for deployment
├── .gitignore               # Git ignore rules
└── README.md                # Project documentation


## 🧩 Tech Stack

- Python 3.13

- Data Processing: Pandas / NumPy / Scikit-learn

- Visualization: Matplotlib

- Web App: Streamlit

- Web Scraping: Selenium / Requests / BeautifulSoup / Fake-UserAgent


## 🔮 Future Improvements 

- **Optimize 'Market Value' scraping** to run in public environments
  
- **Create a new view with 'Player Detailed Stats'** that user could enter to know more about a given player

- **Extend player analysis with time-series** stats - as for now it's limited to one season

- **Add clustering/recommendation system** for player similarity


## 🤝 Contributing

Contributions are welcome! Please open an issue if you’d like to make any suggestion.