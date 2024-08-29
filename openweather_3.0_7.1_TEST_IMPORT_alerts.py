import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from tabulate import tabulate
import logging
from colorama import Fore, Style, init
import arrow
import pandas as pd
from datetime import datetime, timedelta, date
import json
import time
import pytz
import gc

# Logging initialisieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class OpenWeather:
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1,
                        status_forcelist=[502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        # Deaktiviere Warnungen für unsichere Anfragen
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def get_sunrise_sunset(self, lat, lon):
        api_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={self.api_key}&units=metric&lang=de"
        try:
            response = self.session.get(api_url)
            response.raise_for_status()
            data = response.json()

            if 'daily' in data:
                berlin_tz = pytz.timezone('Europe/Berlin')
                sunrise_utc = datetime.utcfromtimestamp(
                    data['daily'][0]['sunrise']).replace(tzinfo=pytz.utc)
                sunset_utc = datetime.utcfromtimestamp(
                    data['daily'][0]['sunset']).replace(tzinfo=pytz.utc)
                sunrise_local = sunrise_utc.astimezone(finsterbergen_tz)
                sunset_local = sunset_utc.astimezone(finsterbergen_tz)
                return sunrise_local, sunset_local
            else:
                logger.error(
                    "Fehler: Sonnenaufgangs- und Sonnenuntergangszeiten nicht verfügbar.")
                return None, None

        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler bei der API-Anfrage: {e}")
            return None, None

    def get_daily_sunshine_duration(self, lat, lon):
        sunrise, sunset = self.get_sunrise_sunset(lat, lon)
        if sunrise and sunset:
            duration = sunset - sunrise
            return duration.total_seconds() / 3600  # Rückgabe der Dauer in Sekunden
        else:
            return None

    api_key = "9d6509fc0d1cbc0b0ee0527cf9f72ef5"
    lat = 50.8578  # Friedrichroda, Deutschland
    lon = 10.5634

    def __init__(self, api_key, city, country_code):
        self.api_key = api_key
        self.city = city
        self.country_code = country_code
        self.units = "metric"
        self.session = requests.Session()
        self.rain_1h = 0.0
        init(autoreset=True)

    def print_events(self):
        today = date.today()
        events = [
            (date(today.year + 1, 1, 1), "Neujahr"),
            (date(today.year, 2, 14), "Valentinstag"),
            (date(today.year, 3, 20), "TagundNachtGleichen_Frühjahr"),
            (date(today.year, 3, 29), "Karfreitag"),
            (date(today.year, 3, 31), "Ostern"),
            (date(today.year, 4, 26), "zum Geburtstag Jutta"),
            (date(today.year, 5, 1), "Tag der Arbeit"),
            (date(today.year, 5, 9), "Himmelfahrt"),
            (date(today.year, 5, 19), "Pfingsten"),
            (date(today.year, 6, 17), "zum Geburtstag Matthias"),
            (date(today.year, 6, 21), "Sommersonnenwende"),
            (date(today.year, 6, 30), "Das ERSTE Halbjahr ist heute um!"),
            (date(today.year, 8, 4), "zum Geburtstag Logan"),
            (date(today.year, 9, 22), "TagundNachtGleichen_Herbst"),
            (date(today.year, 10, 24), "zum Geburtstag Manuel"),
            (date(today.year, 10, 31), "Reformationstag u. Halloween"),
            (date(today.year, 11, 10), "zum Geburtstag Julia"),
            (date(today.year, 12, 24), "Heiligabend"),
            (date(today.year, 12, 25), "Weihnachten")
        ]
        events = sorted(events, key=lambda x: x[0])
        next_event = next((e for e in events if e[0] > today), None)
        if next_event:
            days_until = (next_event[0] - today).days
            print(Fore.BLUE +
                  f"Noch {days_until} Tage bis: {next_event[1]}" + Fore.RESET)
                  
    def print_status_code(self, url, days, event_name):
        response = self.session.get(url, timeout=60)
        status_codes = {
            200: "Statuscode ok!",
            204: "No Content: Die Anfrage war erfolgreich, es wurden jedoch keine Daten zurückgegeben.",
            400: "Bad Request: Die Anfrage war ungültig oder fehlerhaft.",
            401: "Unauthorized: Der API-Schlüssel ist ungültig oder fehlt.",
            403: "Forbidden: Der API-Schlüssel hat nicht die erforderlichen Berechtigungen.",
            404: "Not Found: Die angeforderten Daten wurden nicht gefunden.",
            429: "Too Many Requests: Es wurden zu viele Anfragen innerhalb eines bestimmten Zeitraums gesendet.",
            500: "Internal Server Error: Ein interner Serverfehler ist aufgetreten."
        }
        status_code = response.status_code
        if status_code in status_codes:
            print(
                Fore.BLUE + f"{status_code} | {status_codes[status_code]} | Ab heute noch {days} Tage bis {event_name}" + Fore.RESET)
        else:
            print(
                Fore.RED + f"{status_code} Fehler Requestanforderung prüfen" + Fore.RESET)
                
    def get_weather_data(self, lat, lon, retries=3, delay=5):
        API_anfrage_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={self.api_key}&units=metric&lang=de"
        for attempt in range(retries):
            try:
                response = self.session.get(API_anfrage_url, timeout=120)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise
    def wind_direction(self, deg):
        wind_directions = [
            (337.5, 22.5, "Nordwind"),
            (22.5, 67.5, "Nordostwind"),
            (67.5, 112.5, "Ostwind"),
            (112.5, 157.5, "Südostwind"),
            (157.5, 202.5, "Südwind"),
            (202.5, 247.5, "Südwestwind"),
            (247.5, 292.5, "Westwind"),
            (292.5, 337.5, "Nordwestwind")
        ]
        for min_deg, max_deg, direction in wind_directions:
            if min_deg <= deg < max_deg:
                return direction
        return "Unbekannt"
    def print_red(self, text):
        print(Fore.RED + text + Fore.RESET)
    def print_current_weather(self, data, sunrise, sunset):
        if data:
            current_weather = data['current']
            weather_id = current_weather['weather'][0]['id']
            temp = f"{current_weather['temp']:.1f}°C".replace('.', ',')
            pressure = f"{current_weather['pressure']} hPa"
            humidity = current_weather['humidity']
            description = current_weather['weather'][0]['description']
            clouds = f"{current_weather['clouds']}%"
            wind_speed = f"{current_weather['wind_speed']:.1f} m/s".replace(
                '.', ',')
            wind_deg = current_weather['wind_deg']
            wind_direction = self.wind_direction(wind_deg)
            uvi = f"{current_weather['uvi']:.1f}".replace('.', ',')
            visibility = f"{current_weather.get('visibility', 'N/A')} m"  # Added default value
            feels_like = f"{current_weather['feels_like']:.1f}°C".replace(
                '.', ',')
            temp_max = f"{data['daily'][0]['temp']['max']:.1f}°C".replace(
                '.', ',')
            temp_min = f"{data['daily'][0]['temp']['min']:.1f}°C".replace(
                '.', ',')

            wind_gust = current_weather.get('wind_gust', None)
            if wind_gust is not None:
                wind_gust = f"{wind_gust:.1f} m/s".replace('.', ',')
            else:
                wind_gust = "N/A"

            rain_1h = current_weather.get('rain', {}).get('1h', 0.0)
            rain_1h = f"{rain_1h:.1f} L/m²/h".replace('.', ',')

            snow_1h = current_weather.get('snow', {}).get('1h', 0.0)
            snow_1h = f"{snow_1h:.1f} mm/h".replace('.', ',')

            pop = data['hourly'][0].get('pop', 0.0)
            pop = f"{pop * 100:.1f}%".replace('.', ',')
            # Erstellen der DataFrame ohne erste Spalte und erste Zeile
            weather_data = [
                ["Wetter-ID", weather_id, "Wetter", description],
                ["Aktuelle Temperatur", temp, "Bewölkung", clouds],
                ["Gefühlte Temperatur", feels_like, "UV-Index", uvi],
                ["Sichtweite", visibility, "Windrichtung", wind_direction],
                ["Luftdruck", pressure, "Luftfeuchtigkeit", f"{humidity}%"],
                ["Maximale Temperatur", temp_max, "Minimale Temperatur", temp_min],
                ["Niederschlagsintensität Regen", rain_1h, "Niederschlagsintensität Schnee", snow_1h],
                ["Wahrscheinlichkeit von Niederschlag", pop, "", ""]
            ]
            # Umwandlung in eine Tabelle ohne Zellen-Rahmen
            df = pd.DataFrame(weather_data, columns=['', '', '', ''])
            print(tabulate(df.values.tolist(), tablefmt='plain',
                  showindex=False, headers=[]))
            print()  # Leerzeile nach der Tabelle
            
    def print_special_messages(self):
        today = datetime.today()
        special_days = {
            (7, 6): "<<< HEUT IST UNSER HOCHZEITSTAG, ICH WÜNSCHE UNS EINEN HERRLICHEN TAG, KLAREN HIMMEL UND SONNENSCHEIN >>>",
            (6, 21): "<<< HEUTE IST SOMMERANFANG, ICH WÜNSCHE UNS EINEN HERRLICHEN TAG, KLAREN HIMMEL UND SONNENSCHEIN >>>",
            (4, 26): "<<< HEUTE HAT MEIN SCHATZ GEBURTSTAG! ICH WÜNSCHE DIR NUR DAS BESTE! >>>",
            (6, 17): "<<< HEUTE HABE ICH GEBURTSTAG! ICH WÜNSCHE MIR GESUNDHEIT! >>>",
            (11, 10): "<<< HEUTE HAT UNSERE JULIA GEBURTSTAG! WIR WÜNSCHEN IHR NUR DAS BESTE! >>>",
            (5, 1): "<<< HEUT IST DER 1. MAI - FEIERTAG! >>>",
            (8, 4): "<<< HEUTE HAT UNSER LOGAN GEBURTSTAG! WIR WÜNSCHEN IHM NUR DAS BESTE! >>>",
            (10, 24): "<<< HEUT HAT MANUEL GEBURTSTAG! WIR WÜNSCHEN IHM NUR DAS BESTE! >>>",
            (12, 24): "<<< HEUT IST HEILIGABEND! MAL SEHEN WAS DER ABEND SO BRINGT ...? >>>",
            (12, 25): "<<< HEUTE IST DER 1. WEIHNACHTSFEIERTAG! MAL SEHEN WAS DER TAG UNS BRINGT? >>>",
            (12, 26): "<<< HEUTE IST DER 2. WEIHNACHTSFEIERTAG! MAL SEHEN WAS DER TAG UNS BRINGT? >>>",
            (1, 1): "<<< HEUT BEGINNT DAS NEUE JAHR! ICH BIN GESPANNT WAS ES UNS BRINGT ...? >>>"
        }
        msg = special_days.get((today.month, today.day), None)
        if msg:
            print(Fore.RED + msg + Fore.RESET)
            
    def print_meal_times(self):
        current_time = arrow.now().time()
        # if current_time > arrow.get('12:00', 'HH:mm').time() and current_time < arrow.get('13:30', 'HH:mm').time():
        # print(Fore.RED + "*** JUTTA BITTET ZU TISCH - M A H L Z E I T! ***" + Fore.RESET)
        # if current_time > arrow.get('18:00', 'HH:mm').time() and current_time < arrow.get('19:30', 'HH:mm').time():
        # print(Fore.RED + "*** ZEIT FÜR'S ABENDBROT - M A H L Z E I T! ***" + Fore.RESET)
        
    def fahrenheit_to_celsius(self, fahrenheit):
        return (fahrenheit - 32) * 5 / 9
    
    def get_sunrise_sunset(self, lat, lon):
        api_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={self.api_key}&units=metric&lang=de"
        try:
            response = self.session.get(api_url)
            response.raise_for_status()
            data = response.json()
            if 'daily' in data:
                sunrise = datetime.utcfromtimestamp(
                    data['daily'][0]['sunrise'])
                sunset = datetime.utcfromtimestamp(data['daily'][0]['sunset'])
                return sunrise, sunset
            else:
                print(
                    "Fehler: Sonnenaufgangs- und Sonnenuntergangszeiten nicht verfügbar.")
                return None, None
        except requests.exceptions.RequestException as e:
            print(f"Fehler bei der API-Anfrage: {e}")
            return None, None
    
    def get_daily_sunshine_duration(self, lat, lon):
        api_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly&appid={self.api_key}&units=metric&lang=de"
        try:
            response = self.session.get(api_url)
            response.raise_for_status()
            data = response.json()
            if 'daily' in data:
                daily_data = data['daily']
                today_data = daily_data[0]  # Daten für den aktuellen Tag
                sunrise = datetime.utcfromtimestamp(today_data['sunrise'])
                sunset = datetime.utcfromtimestamp(today_data['sunset'])
                # Berechne die tatsächlichen Sonnenstunden basierend auf den Wolkenbedeckungsdaten
                sunshine_duration_seconds = (sunset - sunrise).total_seconds()
                # Annahme: Wolkenbedeckung in Prozent
                cloud_coverage = today_data.get('clouds', 0) / 100.0
                actual_sunshine_seconds = sunshine_duration_seconds * \
                    (1 - cloud_coverage)
                actual_sunshine_hours = actual_sunshine_seconds // 3600
                actual_sunshine_minutes = (
                    actual_sunshine_seconds % 3600) // 60
                return sunrise, sunset, actual_sunshine_hours, actual_sunshine_minutes
            else:
                print("Fehler: Tägliche Daten nicht verfügbar.")
                return None, None, None, None
        except requests.exceptions.RequestException as e:
            print(f"Fehler bei der API-Anfrage: {e}")
            return None, None, None, None
    
    def print_weather_forecast(self, lat, lon):
        api_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={self.api_key}&units=metric&lang=de"
        try:
            response = self.session.get(api_url, timeout=60)
            response.raise_for_status()
            data = response.json()
            forecast_data = data['daily'][:5]  # 5 Tage Vorhersage
            dates, temperatures, precipitation, clouds = [], [], [], []
            for day in forecast_data:
                date = datetime.utcfromtimestamp(day['dt']).strftime('%A')
                min_temp = day['temp']['min']
                max_temp = day['temp']['max']
                # Wahrscheinlichkeit für Niederschlag
                pop = day.get('pop', 0) * 100
                cloud_coverage = day.get('clouds', 0)
                dates.append(date)
                temperatures.append(f"{round(min_temp)} bis {round(max_temp)}")
                precipitation.append(int(pop))
                clouds.append(cloud_coverage)
            wochentage = {'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
                          'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag', 'Sunday': 'Sonntag'}
            dates = [wochentage[date] for date in dates]
            df = pd.DataFrame({
                'WOCHENTAG': dates,
                'TEMPERATUR (°C)': temperatures,
                'NIEDERSCHLAG (%)': precipitation,
                'BEWÖLKUNG (%)': clouds
            })
            table_string = df.to_string(index=False)
            print(Fore.BLUE + table_string + Fore.RESET)
            with open("vorhersage.txt", "w") as outfile:
                outfile.write(table_string)
        except requests.exceptions.RequestException as e:
            print(f"Fehler bei der API-Anfrage: {e}")
    
    def get_weather_alerts(self, lat, lon):
        url = f"https://api.openweathermap.org/data/3.0/onecall"
        params = {
            'lat': lat,
            'lon': lon,
            'exclude': 'current,minutely,hourly,daily',
            'appid': self.api_key
        }
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            alerts = data.get('alerts', [])
            if alerts:
                for alert in alerts:
                    # Assuming alert level is provided by 'severity' or similar key
                    level = alert.get('severity', 0)
                    if level >= 3: # Erst ab Level 3 werden Wetterwaarnungen ausgegeben!
                        event = alert['event']
                        start_timestamp = alert['start']
                        end_timestamp = alert['end']
                        description = alert['description']
                        start = datetime.fromtimestamp(
                            start_timestamp).strftime('%d.%m.%Y %H:%M:%S')
                        end = datetime.fromtimestamp(
                            end_timestamp).strftime('%d.%m.%Y %H:%M:%S')
                        print(Fore.RED + f"Ereignis: {event}" + Fore.RESET)
                        print(Fore.RED + f"Beginn: {start}" +
                              f"  Ende: {end}" + Fore.RESET)
                        print(
                            Fore.RED + f"Beschreibung: {description}\n" + Fore.RESET)
        except requests.exceptions.RequestException as e:
            print(
                f"Fehler: Wetterwarnungen konnten nicht abgerufen werden. Statuscode: {response.status_code}")

        
    def print_wind_info(self, data):
        wind_speed = data['current']['wind_speed']
        gust_speed = data['current'].get('wind_gust')
        windkmh = wind_speed * 3.6
        boenkmh = gust_speed * 3.6 if gust_speed else None

        print(f"Aktuelle Windgeschwindigkeit: {windkmh:.1f} km/h")

        if boenkmh:
            print(f"Windböen: {round(boenkmh, 1)} km/h")
        else:
            print("Keine Böengeschwindigkeit verfügbar")

        wind_deg = data['current']['wind_deg']
        wind_direction = self.wind_direction(wind_deg)
        print(f"Aktuelle Windrichtung: {wind_direction}")
        wind_strength = [
            (0, 1.0, "Windstärke 0 - Windstille"),
            (1.0, 5.0, "Windstärke 1 - schwacher Wind"),
            (5.0, 11.0, "Windstärke 2 - leichte Brise"),
            (11.0, 19.0, "Windstärke 3 - schwache Brise"),
            (19.0, 28.0, "Windstärke 4 - mäßige Brise"),
            (28.0, 38.0, "Windstärke 5 - frische Brise"),
            (38.0, 49.0, "Windstärke 6 - starke Brise"),
            (49.0, 61.0, "Windstärke 7 - steifer Wind"),
            (61.0, 74.0, "Windstärke 8 - stürmischer Wind"),
            (74.0, 88.0, "Windstärke 9 - Sturm"),
            (88.0, 102.0, "Windstärke 10 - schwerer Sturm"),
            (102.0, 117.0, "Windstärke 11 - orkanartiger Sturm"),
            (117.0, float('inf'), "Windstärke 12 - Orkan")
        ]
        for min_speed, max_speed, description in wind_strength:
            if min_speed <= windkmh < max_speed:
                print(Fore.BLUE + description + Fore.RESET)
                break

if __name__ == "__main__":
    country_code = "DE"
    api_key = "9d6509fc0d1cbc0b0ee0527cf9f72ef5"
    lat = 50.8324
    lon = 10.5846
    while True:
        weather = OpenWeather(api_key, lat, lon)
        today = date.today()

		# Zusätzlicher Codeblock aus Version 2.5
        sunrise, sunset, _, _ = weather.get_daily_sunshine_duration(lat, lon)
        zeit = datetime.today().time()
        # Konvertiere sunrise und sunset zu datetime.time Objekten
        if sunrise and sunset:
            sunrise_time = sunrise.time()
            sunset_time = sunset.time()
            now = datetime.now()
            dt_string = now.strftime("%d.%m.%Y %H:%M:%S")
        if sunrise_time < zeit < sunset_time:
        # Die Zeiten stimmen nicht
        # print(Fore.RED + f"Mögliche Gesamtdauer Sonnenschein heute: {int(hours)} Stunden und {int(minutes)} Minuten" + Fore.RESET)
            print(Fore.RED + "<<< HALLO UND EINEN SCHÖNEN TAG! >>>" + Fore.RESET, f"Aktuelles Wetter am {dt_string} ")
        else:
            print(Fore.RED + ">>> DER TAG NEIGT SICH SEINEM ENDE ... <<<" + Fore.RESET, f"Aktuelles Wetter am {dt_string} ")
		# Leerzeile nach den Meldungen        
        # Mahlzeiten:
        zeit = arrow.now().time()
        if zeit > arrow.get('12:00', 'HH:mm').time() and zeit < arrow.get('13:30', 'HH:mm').time(): weather.print_red("*** JUTTA BITTET ZU TISCH - M A H L Z E I T! ***")
        if zeit > arrow.get('18:00', 'HH:mm').time() and zeit < arrow.get('19:30', 'HH:mm').time(): weather.print_red("*** ZEIT FÜR'S ABENDBROT - M A H L Z E I T! ***")
		
		# Wetterwarnungen ausgeben
            #weather.get_weather_alerts(lat, lon)
		# Leerzeile nach den Wetterwarnungen
            #weather.print_status_code(f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=de", days_until, next_event[1])
		# Leerzeile nach den Statuscodes

        weather.print_events()
        weather.print_special_messages()
        weather.print_meal_times()
        data = weather.get_weather_data(lat, lon)
        weather.print_current_weather(data, sunrise, sunset)
        sunrise, sunset, hours, minutes = weather.get_daily_sunshine_duration(
            lat, lon)
        if sunrise and sunset:
            print(Fore.RED + f"Mögliche Gesamtdauer Sonnenschein heute: {int(hours)} Stunden und {int(minutes)} Minuten" + Fore.RESET)
        weather.print_weather_forecast(lat, lon)
        if weather.rain_1h > 0.0 and weather.rain_1h <= 1.5:
            print(
                f"Sprühregen mit: {weather.rain_1h:.1f} L/m²/h".replace('.', ','))
        elif weather.rain_1h > 1.5 and weather.rain_1h < 2.5:
            print(
                f"Leichter Regen mit: {weather.rain_1h:.1f} L/m²/h".replace('.', ','))
        elif weather.rain_1h >= 2.5 and weather.rain_1h < 7.6:
            print(
                f"Mäßiger Regen mit: {weather.rain_1h:.1f} L/m²/h".replace('.', ','))
        elif weather.rain_1h >= 7.6 and weather.rain_1h < 30.0:
            print(
                Fore.RED + f"Starker Regen mit: {weather.rain_1h:.1f} L/m²/h".replace('.', ',') + Fore.RESET)
        elif weather.rain_1h >= 30.0:
            print(
                Fore.RED + f"Ergiebiger Regen mit: {weather.rain_1h:.1f} L/m²/h".replace('.', ',') + Fore.RESET)
        print()
        # Korrekturfaktor Windgeschwindigkeit in Fibe
        # WindFibe = windkmh * 1.45
        # Ausgabe der aktuellen Windgeschwindigkeit und Windböengeschwindigkeit in km/h:
        windkmh = data['current']['wind_speed'] * 3.6
        boenkmh = data['current'].get('wind_gust', 0.0) * 3.6
        print("Aktuelle Windgeschwindigkeit ", "%.1f" % (windkmh),
              "km/h", " | ", "Windböen ", "%.1f" % (boenkmh), "km/h")
        # Ausgabe der Windverhältnisse in Abhängigkeit der korrigierten Windstärke:
        if windkmh > 0 and windkmh < 1.0:
            print(Fore.BLUE + "Windstärke 0 - Windstille")
        elif windkmh >= 1.0 and windkmh < 5.0:
            print(Fore.BLUE + "Windstärke 1 - schwacher Wind")
        elif windkmh >= 5.0 and windkmh < 11.0:
            print(
                Fore.BLUE + "Windstärke 2 - leichte Brise, Wind im Gesicht fühlbar und die Blätter säuseln")
        elif windkmh >= 11.0 and windkmh < 19.0:
            print(
                Fore.BLUE + "Windstärke 3 - schwache Brise, bewegt Blätter und Zweige bis in die Baumwipfel")
        elif windkmh >= 19.0 and windkmh < 28.0:
            print(Fore.BLUE + "Windstärke 4 - mäßige Brise, hebt Staub und loses Papier, bewegt Zweige und dünne Äste")
        elif windkmh >= 28.0 and windkmh < 38.0:
            print(
                Fore.BLUE + "Windstärke 5 - frische Brise, kleine Laubbäume schwanken, Schaumkämme auf Seen")
        elif windkmh >= 38.0 and windkmh < 49.0:
            print(Fore.BLUE + "Windstärke 6 - mäßige Brise, starker Wind, starke Äste in Bewegung, Pfeifen in Freileitungen")
        elif windkmh >= 49.0 and windkmh < 61.0:
            print(Fore.BLUE + "Windstärke 7 - steifer Wind, ganze Bäume in Bewegung, Hemmung beim Gehen gegen den Wind")
        elif windkmh >= 61.0 and windkmh < 74.0:
            print(
                Fore.RED + "Windstärke 8 - stürmischer Wind, lose Dinge sichern!" + Fore.RESET)
        elif (windkmh >= 74.0 and windkmh < 88.0) or (boenkmh >= 76.0 and boenkmh < 89.0):
            print(Fore.RED + "Winstärke 9 - Sturm mit Sturmböen, kleine Schäden an Häusern und Dächern möglich" + Fore.RESET)
        elif (windkmh >= 88.0 and windkmh < 102.0) or (boenkmh >= 89.0 and boenkmh < 104.0):
            print(Fore.RED + "Windstärke 10 - schwerer Sturm mit Sturmböen, entwurzelt Bäume, bedeutet Schäden an Häusern" + Fore.RESET)
        elif (windkmh >= 102.0 and windkmh < 117.0) or (boenkmh >= 104.0 and boenkmh < 119.0):
            print(Fore.RED + "Windstärke 11 - orkanartiger Sturm mit Orkanartigen Böen, verbreitet Sturmschäden, verbreitet im Bergland" + Fore.RESET)
        elif windkmh >= 117.0 or boenkmh >= 117.0:
            print(Fore.RED + "Windstärke 12 - Orkan oder Orkanböen- schnallt Euch an, schwere Verwüstungen möglich!" + Fore.RESET)
        

        # Fordere den Garbage Collector auf, den Speicher zu bereinigen
        gc.collect()
        
        print()
        time.sleep(1800)  # Wartezeit von einer Stunde (1800 Sekunden)

