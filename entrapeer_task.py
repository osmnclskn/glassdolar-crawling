from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import requests
import threading
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import asyncio

app = FastAPI()
result_json = {'corporate_details': [], 'corporate_count': 0}
fetch_status = "not started"
clustered_data = {"clusters": {}, "sorted_countries": {}, "total_countries": {}}

# Veri çekme işlemleri
async def fetch_startup_partners_count(company_name):
    url = "https://glassdollar-api.com/graphql"
    query = {
        "operationName": "GetStartupPartners",
        "query": """
            query GetStartupPartners($companyName: String!) {
                company(name: $companyName) {
                    startup_partners {
                        company_name
                    }
                }
            }
        """,
        "variables": {
            "companyName": company_name
        }
    }

    try:
        response = requests.post(url, json=query, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        data = response.json()
        startup_partners = data.get("data", {}).get("company", {}).get("startup_partners", [])
        return len({partner["company_name"] for partner in startup_partners})
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return 0

async def fetch_corporates():
    global result_json, fetch_status, clustered_data
    result_json = {'corporate_details': [], 'corporate_count': 0}
    fetch_status = "started"
    url = "https://ranking.glassdollar.com/graphql"
    headers = {"Content-Type": "application/json", "User-Agent": "Your User Agent String"}
    page = 1

    while True:
        corporates_json_data = {
            "operationName": "GetCorporates",
            "variables": {
                "filters": {
                    "hq_city": [],
                    "industry": []
                },
                "page": page
            },
            "query": "query GetCorporates($filters: CorporateFilters, $page: Int) { corporates(filters: $filters, page: $page) { rows { id name } count } }"
        }

        try:
            corporates_response = requests.post(url, headers=headers, json=corporates_json_data, timeout=10)
            corporates_response_data = corporates_response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"An error occurred: {e}")
            break

        if corporates_response.status_code != 200 or not corporates_response_data['data']['corporates']['rows']:
            break

        for corporate in corporates_response_data['data']['corporates']['rows']:
            corporate_id = corporate['id']
            corporate_details_json_data = {
                "operationName": "GetCorporateDetails",
                "variables": {"id": corporate_id},
                "query": "query GetCorporateDetails($id: String) { corporate(id: $id) { name description logo_url hq_city hq_country website_url linkedin_url twitter_url startup_partners_count startup_partners { company_name logo city website country theme_gd } startup_themes } }"
            }

            corporate_details_response = requests.post(url, json=corporate_details_json_data)
            corporate_details_response_data = corporate_details_response.json()
            startup_partners_count = await fetch_startup_partners_count(corporate_details_response_data['data']['corporate']['name'])
            corporate_details_response_data['data']['corporate']['startup_partners_count'] = startup_partners_count
            result_json['corporate_details'].append(corporate_details_response_data['data']['corporate'])
            result_json['corporate_count'] += 1

        page += 1

    fetch_status = "done"

def fetch_corporates_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fetch_corporates())

@app.post("/count_companies")
async def count_companies():
    global result_json
    return {"message": f"Total companies: {result_json['corporate_count']}"}

@app.get("/clustered_companies")
async def get_clustered_companies():
    global clustered_data
    if clustered_data and clustered_data["total_countries"]:
        formatted_json = json.dumps(clustered_data["total_countries"], indent=4)
        return HTMLResponse(f"<pre>{formatted_json}</pre>")
    else:
        return HTMLResponse("<h1>Clustering not performed yet...</h1>")

# Kümeleme işlemleri
@app.post("/perform_clustering")
async def perform_clustering():
    global result_json, clustered_data
    if not result_json['corporate_details']:
        return {"message": "No data to perform clustering"}

    company_descriptions = [company['description'] for company in result_json['corporate_details']]
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(company_descriptions)
    num_clusters = 3
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(X)
    cluster_labels = kmeans.labels_

    clusters = {i: [] for i in range(num_clusters)}
    for idx, company in enumerate(result_json['corporate_details']):
        clusters[cluster_labels[idx]].append(company)

    country_weights = {i: {} for i in range(num_clusters)}
    for cluster_idx, companies_in_cluster in clusters.items():
        for company in companies_in_cluster:
            country = company['hq_country']
            if country in country_weights[cluster_idx]:
                country_weights[cluster_idx][country] += 1
            else:
                country_weights[cluster_idx][country] = 1

    sorted_countries = {i: sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3] for i, weights in country_weights.items()}
    total_countries = {}
    for cluster_idx, countries in country_weights.items():
        for country, count in countries.items():
            total_countries[country] = total_countries.get(country, 0) + count

    clustered_data = {"total_countries": total_countries, "clusters": clusters, "sorted_countries": sorted_countries}
    return {"message": "Clustering performed successfully"}

# Asenkron veri çekme işlemleri
@app.post("/start_fetch")
async def start_fetch():
    global fetch_status
    if fetch_status == "started":
        return {"message": "Fetch is already running"}
    elif fetch_status == "done":
        return {"message": "Fetch is already completed"}
    threading.Thread(target=fetch_corporates_thread).start()
    return {"message": "Fetch started"}

@app.get("/all_companies")
async def get_all_companies():
    global result_json
    if result_json['corporate_details']:
        formatted_json = json.dumps(result_json, indent=4)
        return HTMLResponse(f"<pre>{formatted_json}</pre>")
    else:
        return HTMLResponse("<h1>No companies fetched yet...</h1>")

@app.get("/")
async def root():
    content = """
    <html>
        <head>
            <title>Corporate Fetch</title>
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
            <script>
                var currentPage = "/";

                function startFetch() {
                    currentPage = "/fetch_status";
                    $.post("/start_fetch", function(data) {
                        alert(data.message);
                        if (data.message === "Fetch started") {
                            window.location.href = "/fetch_status";
                        }
                    });
                }

                function countCompanies() {
                    $.post("/count_companies", function(data) {
                        alert(data.message);
                    });
                }

                function performClustering() {
                    $.post("/perform_clustering", function(data) {
                        alert(data.message);
                    });
                }

                function getClusteredCompanies() {
                    currentPage = "/clustered_companies";
                    window.location.href = "/clustered_companies";
                }

                function getAllCompanies() {
                    currentPage = "/all_companies";
                    window.location.href = "/all_companies";
                }

                function fetchCount() {
                    $.getJSON("/fetch_status", function(data) {
                        $('#count').text("Corporates fetched so far: " + data.corporate_count);
                        if(data.fetch_status == "done" && currentPage == "/fetch_status") {
                            window.location.href = "/corporate_results";
                        } else if(currentPage == "/fetch_status") {
                            setTimeout(fetchCount, 2000);
                        }
                    });
                }

                $(document).ready(function() {
                    currentPage = "/";
                    fetchCount();
                });
            </script>
        </head>
        <body>
            <button onclick="startFetch()">Start Fetch</button>
            <button onclick="countCompanies()">Count Companies</button>
            <button onclick="performClustering()">Perform Clustering</button>
            <button onclick="getClusteredCompanies()">Clustered Companies</button>
            <button onclick="getAllCompanies()">All Companies</button>
            <p id="count"></p>
        </body>
    </html>
    """
    return HTMLResponse(content=content)
