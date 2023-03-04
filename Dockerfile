FROM python:3.11.2
EXPOSE 8501
WORKDIR /app

# Run initial code
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 sudo -y

# Copy necessary directories
COPY . .
#COPY session/ ./session/
COPY pages_/ ./pages_/
COPY helpers/ ./helpers/

# Copy the sessionkeeping script into cron.hourly
# Removes session directories older than 3 days from the session directory
COPY sessionkeep /etc/cron.hourly/sessoinkeep


# Run application 
CMD sudo streamlit run app.py