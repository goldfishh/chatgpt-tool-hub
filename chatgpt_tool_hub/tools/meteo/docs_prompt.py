OPEN_METEO_DOCS = """BASE URL: https://api.open-meteo.com/

API Documentation
The API endpoint /v1/forecast accepts a geographical coordinate, a list of weather variables and responds with a JSON hourly weather forecast for 7 days. Time always starts at 0:00 today and contains 168 hours. All URL parameters are listed below:

Parameter	Format	Required	Default	Description
latitude, longitude	Floating point	Yes		Geographical WGS84 coordinate of the location
hourly	String array	No		A list of weather variables which should be returned. Values can be comma separated, or multiple &hourly= parameter in the URL can be used.
daily	String array	No		A list of daily weather variable aggregations which should be returned. Values can be comma separated, or multiple &daily= parameter in the URL can be used. 
current_weather	Bool	No	false	Include current weather conditions in the JSON output.
temperature_unit	String	No	celsius	If fahrenheit is set, all temperature values are converted to Fahrenheit.
windspeed_unit	String	No	kmh	Other wind speed speed units: ms, mph and kn
precipitation_unit	String	No	mm	Other precipitation amount units: inch
timeformat	String	No	iso8601	If format unixtime is selected, all time values are returned in UNIX epoch time in seconds. Please note that all timestamp are in GMT+0! For daily values with unix timestamps, please apply utc_offset_seconds again to get the correct date.
timezone	String	No	GMT	If timezone is set, all timestamps are returned as local-time and data is returned starting at 00:00 local-time. Any time zone name from the time zone database is supported. If auto is set as a time zone, the coordinates will be automatically resolved to the local time zone.
past_days	Integer (0-2)	No	0	If past_days is set, yesterday or the day before yesterday data are also returned.
start_date & end_date	String (yyyy-mm-dd)	No		The time interval to get weather data. A day must be specified as an ISO8601 date (e.g. 2022-06-30).

Hourly Parameter Definition:
The parameter &hourly= accepts the following values; note that you cannot use Daily Parameter in &hourly=.
Most weather variables are given as an instantaneous value for the indicated hour. 
Some variables like precipitation are calculated from the preceding hour as an average or sum.

Variable	Valid time	Unit	Description
temperature_2m	Instant	°C (°F)	Air temperature at 2 meters above ground
cloudcover	Instant	%	Total cloud cover as an area fraction
precipitation	Preceding hour sum	mm (inch)	Total precipitation (rain, showers, snow) sum of the preceding hour
snowfall	Preceding hour sum	cm (inch)	Snowfall amount of the preceding hour in centimeters. For the water equivalent in millimeter, divide by 7. E.g. 7 cm snow = 10 mm precipitation water equivalent
rain	Preceding hour sum	mm (inch)	Rain from large scale weather systems of the preceding hour in millimeter
weathercode	Instant	WMO code	Weather condition as a numeric code. Follow WMO weather interpretation codes.   
windspeed_10m & windspeed_80m & windspeed_120m & windspeed_180m	Instant	km/h (mph, m/s, knots)	Wind speed at 10, 80, 120 or 180 meters above ground. Wind speed on 10 meters is the standard level.
snow_depth	Instant	meters	Snow depth on the ground
visibility	Instant	meters	Viewing distance in meters. Influenced by low clouds, humidity and aerosols. Maximum visibility is approximately 24 km.

Daily Parameter Definition:
The parameter &daily= accepts the following values:
Aggregations are a simple 24 hour aggregation from hourly values.  
note that you cannot use Hourly Parameter in &daily=.

Variable	Unit	Description
temperature_2m_max & temperature_2m_min	°C (°F)	Maximum and minimum daily air temperature at 2 meters above ground
precipitation_sum	mm	Sum of daily precipitation (including rain, showers and snowfall)
rain_sum	mm	Sum of daily rain
weathercode	WMO code	The most severe weather condition on a given day. Follow WMO weather interpretation codes. 
sunrise & sunset	iso8601	Sun rise and set times
windspeed_10m_max & windgusts_10m_max	km/h (mph, m/s, knots)	Maximum wind speed and gusts on a day
winddirection_10m_dominant	°	Dominant wind direction


WMO Weather interpretation codes (WW)
Code	Description
0	Clear sky
1, 2, 3	Mainly clear, partly cloudy, and overcast
45, 48	Fog and depositing rime fog
51, 53, 55	Drizzle: Light, moderate, and dense intensity
56, 57	Freezing Drizzle: Light and dense intensity
61, 63, 65	Rain: Slight, moderate and heavy intensity
66, 67	Freezing Rain: Light and heavy intensity
71, 73, 75	Snow fall: Slight, moderate, and heavy intensity
77	Snow grains
80, 81, 82	Rain showers: Slight, moderate, and violent
85, 86	Snow showers slight and heavy

Think step by step: 
1. You should only use the parameters described in this document to construct the API URL, 
and should not make up parameters. If there is no parameter for daily granularity, 
you can use the parameter for hourly granularity instead.
2. Access weather information for no more than 3 days using the parameters start_date, or end_date.
3. Parameter past_days is mutually exclusive with start_date and end_date.
4. If daily weather variables are specified, parameter timezone is required.
5. Your output can only be a URL, no need for explanation.

URL: """
