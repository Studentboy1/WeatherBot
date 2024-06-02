import openmeteo_requests
import requests
import os

import requests_cache
import pandas as pd
from retry_requests import retry
from dotenv import load_dotenv

load_dotenv()

def get_weather():
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 56.51,
        "longitude": 35.55,
        "hourly": ["temperature_2m", "precipitation_probability", "precipitation"],
        "timezone": "Europe/Moscow",
        "forecast_days": 1
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(),unit="s",utc=True),
        end=pd.to_datetime(hourly.TimeEnd(),unit="s",utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation_probability"] = hourly_precipitation_probability
    hourly_data["precipitation"] = hourly_precipitation

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    return hourly_dataframe.to_markdown(index=None)


def send_message(message):
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'

    params = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': f'''{message}'''
    }

    res = requests.post(url, params=params)
    res.raise_for_status()
    return res.json()

if __name__=='__main__':
    weather = get_weather()
    send_message(weather)