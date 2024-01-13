import datetime

current_time = datetime.datetime.now().time()
formatted_time = current_time.strftime("%H:%M:%S")

# Add 5 minutes to the current time
new_time = (datetime.datetime.strptime(formatted_time, "%H:%M:%S") + datetime.timedelta(minutes=5)).time()

# Store the new time in the session
new = new_time.strftime("%H:%M:%S")

print(new_time)