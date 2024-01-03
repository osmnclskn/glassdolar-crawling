# corporate_fetch.py
import json
import pandas as pd
import requests
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder

result_json = {"corporate_details": [], "corporate_count": 0}
fetch_status = "not started"
clustered_data = {"clusters": {}}


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
            startup_partners_count = fetch_startup_partners_count(
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
