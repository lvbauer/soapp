FROM python:3.9.7
EXPOSE 8501
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 sudo -y
COPY . .
COPY session/ ./session/
COPY pages_/ ./pages_/
COPY helpers/ ./helpers/
CMD sudo streamlit run app.py