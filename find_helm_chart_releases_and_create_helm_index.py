import yaml
import requests
import hashlib
import re
import tarfile
from datetime import datetime
from io import BytesIO


def get_releases(repo, token):
    url = f"https://api.github.com/repos/{repo}/releases"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def find_tgz_assets(releases):
    tgz_assets = []
    pattern = re.compile(r"^knative-operator-(v?\d+\.\d+\.\d+)\.tgz$")

    for release in releases:
        release_date = release["published_at"]
        for asset in release.get("assets", []):
            if pattern.match(asset["name"]):
                tgz_assets.append(
                    {
                        "release": release["tag_name"],
                        "name": asset["name"],
                        "download_url": asset["browser_download_url"],
                        "release_date": release_date,
                    }
                )
    return tgz_assets


def get_chart_details(tgz_content):
    description = "No description available"
    app_version = "No app version available"
    chart_version = "No version available"

    with tarfile.open(fileobj=BytesIO(tgz_content), mode="r:gz") as tar:
        try:
            chart_yaml = tar.extractfile("knative-operator/Chart.yaml")
            if chart_yaml:
                chart_data = yaml.safe_load(chart_yaml)
                description = chart_data.get("description", description)
                chart_version = chart_data.get("version", chart_version)
                app_version = chart_version  # Use chart version as app version
        except KeyError:
            pass

    return description, app_version


def create_helm_index(tgz_assets):
    index = {"apiVersion": "v1", "entries": {}}
    for asset in tgz_assets:
        name_version = asset["name"].replace(".tgz", "")
        name, version = name_version.rsplit("-", 1)

        print(
            f"Processing Helm chart release: {name} version: {version} from URL: {asset['download_url']}"
        )

        response = requests.get(asset["download_url"])
        response.raise_for_status()
        tgz_content = response.content

        digest = hashlib.sha256(tgz_content).hexdigest()
        description, app_version = get_chart_details(tgz_content)

        if name not in index["entries"]:
            index["entries"][name] = []

        index["entries"][name].append(
            {
                "apiVersion": "v2",
                "name": name,
                "version": version,
                "urls": [asset["download_url"]],
                "created": asset["release_date"],
                "digest": digest,
                "description": description,
                "appVersion": app_version,
            }
        )

    with open("index.yaml", "w") as f:
        yaml.dump(index, f, sort_keys=False)


def main():
    repo = "knative/operator"  # replace with the repository you want to check
    token = "your_personal_access_token_here"  # replace with your personal access token
    releases = get_releases(repo, token)
    tgz_assets = find_tgz_assets(releases)

    print(f"Found {len(tgz_assets)} Helm chart assets in the releases.")

    if tgz_assets:
        create_helm_index(tgz_assets)
        print("Helm index.yaml file created successfully.")
    else:
        print("No .tgz files found in the releases.")


if __name__ == "__main__":
    main()
