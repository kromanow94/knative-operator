import yaml
import requests
import hashlib
import re
from datetime import datetime


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
        digest = hashlib.sha256(response.content).hexdigest()

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
