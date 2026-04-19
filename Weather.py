import os
import requests


class WeatherAPI:
    os.environ["WEATHER_API_KEY"] = "you weather api key"
    os.environ["WEATHER_API_BASE_URL"] = "https://api.weatherapi.com/v1/"

    def get_Current_Weather(self, location: str):
        """
        Fetch current weather for a given location like Bengaluru.
        Args:
            location (str): City name, zip, or lat/long

        Returns:
            dict: Parsed weather data
        """
        params = {
            "key": os.environ.get("WEATHER_API_KEY"),
            "q": location
        }

        try:
            response = requests.get(os.environ.get("WEATHER_API_BASE_URL")+"current.json", params=params)
            response.raise_for_status()
            data = response.json()
            print(f" Response from Weather API: ")
            print(f" {data} ") 
            return data
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        
    def get_Weather_Forecast(self, location: str, days: int):
        """
        Fetch weather forecast for a given location like Bengaluru for the given number of days like 3
        
        Args:
            location (str): City name, zip, or lat/long
            days (int): 1, 2, 3
        Returns:
            dict: Parsed weather data
        """
        url = os.environ.get("WEATHER_API_BASE_URL") + "forecast.json"
        params = {
            "key": os.environ.get("WEATHER_API_KEY"),
            "q": location,
            "days": days
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            print(f" Response from Weather API: ")
            print(f" {data} ") 
            return data
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}



if __name__ == "__main__":
    #WeatherAPI().get_Current_Weather("Bengaluru")
    WeatherAPI().get_Weather_Forecast("Bengaluru", 7)