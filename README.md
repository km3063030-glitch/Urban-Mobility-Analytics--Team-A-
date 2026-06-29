# Urban Mobility Analytics Dashboard

This repository contains an Urban Mobility Analytics dashboard as per the "Set A" Python Data Science Hackathon requirements.

## Files included:
- `urban_mobility_analytics.ipynb`: A Jupyter Notebook with the block-by-block solution for easy interactive running.
- `app.py`: A Streamlit dashboard version of the analysis.
- `requirements.txt`: Python dependencies required to run the code.

## How to run the Jupyter Notebook
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install jupyter
   ```
2. Launch Jupyter Notebook:
   ```bash
   jupyter notebook
   ```
3. Open `urban_mobility_analytics.ipynb` and run the cells.

## How to run the Streamlit App locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run Streamlit:
   ```bash
   streamlit run app.py
   ```
3. The app will open in your browser automatically.

## How to deploy on Streamlit Community Cloud (Online)
1. Push this code to a GitHub repository (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click on "New app" (or "Create app").
4. Select the GitHub repository and branch you just pushed to.
5. Set the Main file path to `app.py`.
6. Click "Deploy". Your app will be live within a few minutes and accessible via a shareable public URL!
