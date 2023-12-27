# GlassDollar Crawling

## Setup on Your Computer

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/osmnclskn/glassdolar-crawling.git
2.**Build the Docker Image""
 ```bash
docker build -t glassdolar-crawling .
```

3** Run the Docker Container""
 ```bash
docker run -d -p 8000:8000 glassdollar-crawling
```

## User Guide
### On Browser
.Go to http://localhost:8000/ in your browser.
.Click the "Start Fetch" button.![Ekran görüntüsü 2023-12-27 075318](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/05ac0413-7ff5-481b-92da-f01be03346dc)

.After that you will see this message ![image](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/70982111-0263-443f-90e4-74198f619cb7)

.When you click on the "tamam" button, it will take you to a page. When you press the return button, you will return to the home page.
.This is our main page ![main_page](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/85a0629e-d92a-44c9-a64b-9a93db539aa7)
### Count Companies
.Click the "Count Companies" button to get the total number of fetched companies. A POST request is sent to the `/count_companies` endpoint.![count_companies](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/8e816141-765e-4462-a363-efdc87587c89)
### Perform Clustering
Click the "Perform Clustering" button to apply k-means clustering to the company descriptions. A POST request is sent to the `/perform_clustering` endpoint.(You must press this button when the "Count Companies" process is completed. Then it will start working and show this message.)![perform_clustering](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/bb809594-0838-4fac-a442-10afa7046200)
### View Clustered Companies
Click the "Clustered Companies" button to view the results of the clustering operation. A GET request is sent to the `/clustered_companies` endpoint.(You should press this button when you press the "Perform Clustering" button. Then it will start working and you can access the .json file seen in the picture below.)![clustering_json](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/6079fc01-f02f-47f2-b1a7-812c62544357)
### View All Companies
Click the "All Companies" button to view details of all fetched companies. A GET request is sent to the `/all_companies` endpoint.(A part of the file is shown due to its size. It contains information of all companies in the json file.)![company_json](https://github.com/osmnclskn/glassdolar-crawling/assets/95987598/9932bd42-fceb-43b4-8e08-e55c7f996d1f)









