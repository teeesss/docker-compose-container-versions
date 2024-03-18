#!/usr/bin/env python3

import subprocess
import requests
import json
import os
from tabulate import tabulate
from datetime import datetime

# Variables for file path and directories
html_file_path = "/volume1/media-stack/docker.html"
directories_path = [
    "/var/services/homes/jonesy/docker-compose/full-stack",
    "/var/services/homes/jonesy/docker-compose/openspeedtest",
    "/var/services/homes/jonesy/docker-compose/portainer",
    "/var/services/homes/jonesy/docker-compose/syncthing",
    "/var/services/homes/jonesy/docker-compose/unifi",
    "/var/services/homes/jonesy/docker-compose/watchtower",
    "/var/services/homes/jonesy/docker-compose/cloudflair",
    "/var/services/homes/jonesy/docker-compose/ddns"
]

def get_container_info(directory):
    # Change to the specified directory
    os.chdir(directory)

    # Run Docker command to get container information
    try:
        # Get container status
        status_output = subprocess.check_output(["docker-compose", "ps", "-q"])
        status_output = status_output.decode().strip().split("\n")

        container_info = []

        for container_id in status_output:
            # Get container name
            container_name = subprocess.check_output(["docker", "ps", "--filter", f"id={container_id}", "--format", "{{.Names}}"]).decode().strip()

            # Get container image
            container_image = subprocess.check_output(["docker", "ps", "--filter", f"id={container_id}", "--format", "{{.Image}}"]).decode().strip()

            # Get container version
            container_version = subprocess.check_output(["docker", "inspect", "--format", "{{.Config.Labels.version}}", container_id]).decode().strip()
            if container_version == "<no value>":
                container_version = ""

            # Get latest stable version from repository
            latest_version, release_url = get_latest_stable_version(container_image)

            # Get image creation date
            image_creation_date = get_image_creation_date(container_id)

            # Get pull date
            pull_date = get_pull_date(container_id)

            # Append container info
            container_info.append({"Name": container_name, "Image": container_image,
                                   "Latest Version": latest_version, "Image Creation Date": image_creation_date,
                                   "Pull Date": pull_date, "Tags": release_url})

        return container_info

    except subprocess.CalledProcessError as e:
        print("Error executing Docker commands:", e)
        return None

def get_latest_stable_version(image):
    # Remove "lscr.io/" from the image name if it exists
    if "lscr.io/" in image or "ghcr.io/" in image:
        image = image.split("/", 1)[1]

    # Extract image name and tag
    image_parts = image.split(":")
    image_name = image_parts[0]

    try:
        # Send request to Docker Hub API to get tags
        response = requests.get(f"https://hub.docker.com/v2/repositories/{image_name}/tags/?page_size=100")
        if response.status_code == 200:
            tags = response.json()["results"]
            stable_versions = []
            for tag in tags:
                tag_name = tag["name"]
                # Check if the tag is a stable version (exclude specific keywords)
                if not any(keyword in tag_name.lower() for keyword in ['develop', 'test', 'testing', 'beta', 'preview', 'unstable']):
                    stable_versions.append(tag_name)

            # Sort the stable versions and get the latest one
            latest_stable_version = sorted(stable_versions)[-1] if stable_versions else "Not found"
            release_url = f"https://hub.docker.com/r/{image_name}/tags"
            return f"{image_name}:{latest_stable_version}", release_url
        else:
            return "Not found", ""
    except Exception as e:
        print(f"Error retrieving latest stable version for {image_name}: {e}")
        return "Not found", ""

def get_image_creation_date(container_id):
    try:
        # Run docker inspect command to get container details
        inspect_output = subprocess.check_output(["docker", "inspect", "--format", "{{.Created}}", container_id]).decode().strip()

        # Extract the date part from the string and format it
        creation_date = inspect_output.split("T")[0]
        creation_time = inspect_output.split("T")[1].split(".")[0]
        creation_datetime = f"{creation_date} {creation_time}"

        return creation_datetime
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving creation date for container {container_id}: {e}")
        return "Not found"

def get_pull_date(container_id):
    try:
        # Run docker inspect command to get container details
        inspect_output = subprocess.check_output(["docker", "inspect", container_id]).decode().strip()
        container_details = json.loads(inspect_output)[0]

        # Extract the pull date from the container details
        pull_date = container_details["Created"].split("T")[0]

        return pull_date
    except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as e:
        print(f"Error retrieving pull date for container {container_id}: {e}")
        return "Not found"

import string

from tabulate import tabulate

def print_container_info(container_info):
    # Define the column headers
    headers = ["Name", "Image", "Latest Version", "Image Creation Date", "Pull Date", "Tags"]

    # Create a list of lists, where each inner list represents a row
    rows = [[container[header] for header in headers] for container in container_info]

    # Print the table using tabulate
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

def create_html_file(container_info):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Docker Container Info</title>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
                max-width: 300px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            a {{
                color: blue;
                text-decoration: underline;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <h1>Docker Container Info</h1>
        <p>Generated on: {}</p>
        <table id="containerTable">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Image</th>
                    <th>Latest Version</th>
                    <th>Image Creation Date</th>
                    <th>Pull Date</th>
                    <th>Tags</th>
                </tr>
            </thead>
            <tbody>
    """.format(now)

    for container in container_info:
        html_content += """
            <tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td><a href="{}" target="_blank">Tags</a></td>
            </tr>
        """.format(container['Name'], container['Image'], container['Latest Version'], container['Image Creation Date'], container['Pull Date'], container['Tags'])

    html_content += """
            </tbody>
        </table>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script>
        <script>
            $(document).ready(function() {
                $('#containerTable').DataTable({
                    "lengthMenu": [25, 50, 100, -1],
                    "pageLength": 25
                });
            });
        </script>
    </body>
    </html>
    """

    # Write HTML content to a file
    with open(html_file_path, "w") as html_file:
        html_file.write(html_content)

    print("HTML file created successfully at:", html_file_path)

if __name__ == "__main__":
    container_info_all = []

    for directory in directories_path:
        container_info = get_container_info(directory)
        container_info_all.extend(container_info)

    print_container_info(container_info_all)
    create_html_file(container_info_all)
