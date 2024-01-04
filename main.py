# main.py
import json

import numpy as np
import pandas as pd
import requests
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder

from tasks import fetch_corporates_celery as fetch_corporates

app = FastAPI()
result_json = {"corporate_details": [], "corporate_count": 0}
fetch_status = "not started"
clustered_data = {"clusters": {}}


# Data extraction operations
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
        "variables": {"companyName": company_name},
    }

    try:
        response = requests.post(
            url, json=query, headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        startup_partners = (
            data.get("data", {}).get("company", {}).get("startup_partners", [])
        )
        return len({partner["company_name"] for partner in startup_partners})
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return 0


async def fetch_corporates():
    global result_json, fetch_status, clustered_data
    result_json = {"corporate_details": [], "corporate_count": 0}
    fetch_status = "started"
    url = "https://ranking.glassdollar.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Your User Agent String",
    }
    page = 1

    while True:
        corporates_json_data = {
            "operationName": "GetCorporates",
            "variables": {"filters": {"hq_city": [], "industry": []}, "page": page},
            "query": "query GetCorporates($filters: CorporateFilters, $page: Int) { corporates(filters: $filters, page: $page) { rows { id name } count } }",
        }

        try:
            corporates_response = requests.post(
                url, headers=headers, json=corporates_json_data, timeout=10
            )
            corporates_response_data = corporates_response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"An error occurred: {e}")
            break

        if (
            corporates_response.status_code != 200
            or not corporates_response_data["data"]["corporates"]["rows"]
        ):
            break

        for corporate in corporates_response_data["data"]["corporates"]["rows"]:
            corporate_id = corporate["id"]
            corporate_details_json_data = {
                "operationName": "GetCorporateDetails",
                "variables": {"id": corporate_id},
                "query": "query GetCorporateDetails($id: String) { corporate(id: $id) { name description logo_url hq_city hq_country website_url linkedin_url twitter_url startup_partners_count startup_partners { company_name logo city website country theme_gd } startup_themes } }",
            }

            corporate_details_response = requests.post(
                url, json=corporate_details_json_data
            )
            corporate_details_response_data = corporate_details_response.json()
            startup_partners_count = await fetch_startup_partners_count(
                corporate_details_response_data["data"]["corporate"]["name"]
            )
            corporate_details_response_data["data"]["corporate"][
                "startup_partners_count"
            ] = startup_partners_count
            result_json["corporate_details"].append(
                corporate_details_response_data["data"]["corporate"]
            )
            result_json["corporate_count"] += 1

        page += 1

    fetch_status = "done"


def fetch_corporates_thread():
    import asyncio

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
    if clustered_data and clustered_data["clusters"]:
        formatted_json = json.dumps(clustered_data, indent=4, ensure_ascii=False)
        return HTMLResponse(f"<pre>{formatted_json}</pre>")
    else:
        return HTMLResponse("<h1>Clustering not performed yet...</h1>")


# Clustering Processes
@app.post("/perform_clustering")
async def perform_clustering():
    global result_json, clustered_data
    if not result_json["corporate_details"]:
        return {"message": "No data to perform clustering"}

    all_companies = []

    for company in result_json["corporate_details"]:
        company_info = {
            "type": "company",
            "name": company.get("name", ""),
            "hq_country": company.get("hq_country", ""),
            "description": company.get("description", ""),
            "industries": company.get("startup_themes", []),
        }
        all_companies.append(company_info)

    df = pd.DataFrame(all_companies)

    if df.empty:
        return {"message": "DataFrame is empty."}

    all_industries_flat = set()
    for industries_list in df["industries"]:
        all_industries_flat.update(tuple(industry) for industry in industries_list)

    all_industries_flat = list(all_industries_flat)

    # Create weighted vector for each company
    for industry in all_industries_flat:
        df[industry] = df["industries"].apply(lambda x: 1 if industry in x else 0)

    # Improving vector representations - Add additional features
    vectorizer = TfidfVectorizer(stop_words="english")
    X_text = vectorizer.fit_transform(df["description"]).toarray()

    df_industries = pd.DataFrame(
        df[all_industries_flat].values, columns=all_industries_flat
    )

    X = np.hstack([X_text, df_industries])

    optimal_num_clusters = 4
    # Build the KMeans model and perform clustering
    kmeans = KMeans(
        n_clusters=optimal_num_clusters,
        init="k-means++",
        max_iter=300,
        n_init=10,
        random_state=0,
    )
    df["cluster"] = kmeans.fit_predict(X)

    #
    clusters = {"clusters": {}}
    for cluster_id in range(optimal_num_clusters):
        cluster_data = df[df["cluster"] == cluster_id]
        cluster_info = {
            "cluster_id": cluster_id + 1,
            "companies": cluster_data[
                [
                    "name",
                ]
            ].to_dict(orient="records"),
        }

        clusters["clusters"][f"Cluster {cluster_id + 1}"] = cluster_info

    with open("clustered_companies.json", "w", encoding="utf-8") as json_file:
        json.dump(clusters, json_file, indent=4, ensure_ascii=False)

    clustered_data = clusters
    return {"message": "Clustering performed successfully"}


@app.post("/start_fetch")
async def start_fetch(background_tasks: BackgroundTasks):
    global fetch_status
    if fetch_status == "started":
        return {"message": "Fetch is already running"}
    elif fetch_status == "done":
        return {"message": "Fetch is already completed"}

    # Start Celery task in the background
    background_tasks.add_task(fetch_corporates)

    return {"message": "Fetch started"}


@app.get("/all_companies")
async def get_all_companies():
    global result_json
    if result_json["corporate_details"]:
        formatted_json = json.dumps(result_json, indent=4, ensure_ascii=False)
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
                    currentPage = "/clustered_companies";
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
