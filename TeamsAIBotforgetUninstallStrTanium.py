import sys
import requests
import pandas as pd
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


# Allowed naming rules
allowed_prefixes = ("s00", "d00", "t01", "t00", "d01", "s09", "syd")
allowed_domains = (".blackbaud.global", ".blackbaudhost.com", ".blackbaud.net")

# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")


def validate_computer_name(name):
    name = name.lower()
    return name.startswith(allowed_prefixes) and name.endswith(allowed_domains)


def chunk_text(text, chunk_size=100):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks


def urlandheaders():
    url = "https://blackbaud-api.cloud.tanium.com/plugin/products/gateway/graphql"
    headers = {
        "session": "token-7fc9ea2aab6abe6616623bbaee6ed2ebdb42d15a341fb851c115dc5505",
        "Content-Type": "application/json"
    }
    return url, headers


def export_apps(computerName):

    url, headers = urlandheaders()

    payload = {
                "query": """
                query getFirstTenEndpoints($computerName:String) {
            endpoints(
                filter:{
                filters:{
                    sensor: { name: "Computer Name" },
                    op: EQ,
                    value: $computerName
                }
                },
                first: 10) {
                edges {
                node {
                    name
                    computerID
                    sensorReadings(sensors: [{name: "Installed Applications", columns: ["Name", "Silent Uninstall String"]}]) {
                    columns {
                        name
                        values
                        sensor {
                        name
                        }
                    }
                    }
                }
                }
            }
            }
                """,
                    "variables": {
                "computerName": computerName
                    }
            }

    response = requests.post(url, headers=headers, json=payload)

    data = json.loads(response.text)

    edges = data["data"]["endpoints"]["edges"]

    results = []

    for edge in edges:

        node = edge["node"]
        name = node["name"]
        computerID = node["computerID"]
        sensorReadings = node["sensorReadings"]

        if sensorReadings:

            columns = sensorReadings["columns"]

            for column in columns:

                if column["name"] == "Name":
                    app_names = column["values"]

                elif column["name"] == "Silent Uninstall String":
                    uninstall_strings = column["values"]

            for app_name, uninstall_string in zip(app_names, uninstall_strings):

                results.append({
                    "Computer Name": name,
                    "Computer ID": computerID,
                    "Application": app_name,
                    "Silent Uninstall String": uninstall_string
                })

    df = pd.DataFrame(results)

    df.to_excel("Tanium_export.xlsx", index=False)

    print("Exported successfully to Tanium_export.xlsx")

    return df


def build_faiss_index(df):

    texts = df[['Application', 'Silent Uninstall String']].fillna('').apply(
        lambda row: ' '.join(row.astype(str)), axis=1
    ).tolist()

    all_chunks = []

    for t in texts:
        all_chunks.extend(chunk_text(t, 100))

    embeddings = model.encode(all_chunks).astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    return index, all_chunks


def search_application(index, chunks, query):

    query_embedding = model.encode([query]).astype("float32")

    k = 3

    distances, results = index.search(query_embedding, k)

    answers = []

    for i, idx in enumerate(results[0]):

        answers.append({
            "rank": i + 1,
            "distance": float(distances[0][i]),
            "result": chunks[idx]
        })

    return answers


def main():

    if len(sys.argv) < 3:
        print("Usage: rag.exe <ComputerName> <ApplicationName>")
        return

    computerName = sys.argv[1].strip().lower()
    query = sys.argv[2].strip()

    if not validate_computer_name(computerName):
        print("Invalid Computer Name")
        return

    try:

        df = export_apps(computerName)

        index, chunks = build_faiss_index(df)

        results = search_application(index, chunks, query)

        print("\nTop Results:\n")

        for r in results:
            print(f"Result {r['rank']} (distance {r['distance']:.4f})")
            print(r["result"])
            print("-" * 80)

    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    main()