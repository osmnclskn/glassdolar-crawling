# GlassDollar Crawling
This project is a FastAPI application that fetches corporate data, performs clustering, and utilizes Celery for background task processing.

## Project Structure

- **main.py:** FastAPI application for handling HTTP requests and serving the API.

- **corporate_fetch.py:** Module containing functions for fetching corporate data.

- **tasks.py:** Celery tasks for background processing.

- **Dockerfile:** Dockerfile for building the FastAPI application container.

- **Dockerfile.celery:** Dockerfile for building the Celery worker container.

- **docker-compose.yml:** Docker Compose configuration file to orchestrate services.

- **requirements.txt:** List of Python dependencies for the project.
## Setup on Your Computer

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/osmnclskn/glassdolar-crawling.git
2.**Build and Run Docker Containers""
 ```bash
docker-compose up --build 
```
This command will start the FastAPI application,Celery worker and RabbitMQ services
3. **Access the FastAPI Application:
   Open your web browser and go to  http://localhost:8000 to interact with the FastAPI application.


## User Guide
### On Browser
.This is our main page !  

![main_page](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/21c6f146-4962-4054-90ae-5bf1a62a6a54)


.Click the "Start Fetch" button.

![Ekran görüntüsü 2023-12-27 075318](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/05ac0413-7ff5-481b-92da-f01be03346dc)


.After that you will see message like this.


![start_fetch_message](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/10772e2b-eada-4f79-bd2b-6ad315921fe6)


And click the "Tamam" button,

### Count Companies
.Click the "Count Companies" button to get the total number of fetched companies. A POST request is sent to the `/count_companies` endpoint.![count_companies](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/f2d366fa-79bb-4a61-b59f-24a3e4e25fd0)

### Perform Clustering
Click the "Perform Clustering" button to apply k-means clustering to the company descriptions. A POST request is sent to the `/perform_clustering` endpoint.(You must press this button when the "Count Companies" process is completed. Then it will start working and show this message.)

![perform_clustering](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/bb809594-0838-4fac-a442-10afa7046200)
### View Clustered Companies
Click the "Clustered Companies" button to view the results of the clustering operation. A GET request is sent to the `/clustered_companies` endpoint.(You should press this button when you press the "Perform Clustering" button. Then it will start working and you can access the .json file seen in the picture below.)

![clustering_json1](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/909a99d5-7be4-443b-9f24-70cbb6fdbf79)      

![clustering_json12png](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/264d8703-8d69-400c-a4c6-2c6e2805d6a2)   ![clustering_json123png](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/5f87ed6f-3396-485a-8186-a928e40e936c)

This clustering process was carried out by taking the country information of all companies and data on the 3 most densely populated countries. Accordingly, they were clustered. (Only some of the companies are shown in the picture, not included so as not to take up too much space)
### View All Companies
Click the "All Companies" button to view details of all fetched companies. A GET request is sent to the `/all_companies` endpoint.(A part of the file is shown due to its size. It contains information of all companies in the json file.)

![ALL_COMPANY](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/d5c69b39-9d54-429a-8b5f-e0654eccb582)



###Notes

The FastAPI application is exposed on port 8000, and you can access the API documentation at http://localhost:8000/docs.

The Celery worker runs in the background to handle tasks such as fetching corporate data

#Docker Compose Services

-**rabbitmq: RabbitMQ service used as a message broker for Celery.

-**celery-worker: Celery worker that processes background tasks.

-**fastapi-app: FastAPI application for fetching corporate data and performing clustering.
.












