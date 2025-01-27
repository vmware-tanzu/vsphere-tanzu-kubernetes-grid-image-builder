import argparse
import json
import subprocess

IMAGE_NAME = "docker.io/vmware/docker-registry"
PAUSE_IMAGE_NAME = "localhost:5000/vmware.io/pause"
LABEL = "io.cri-containerd.pinned=pinned"

def get_registry_version():
    cp = subprocess.run(["crictl", "images", "-o", "json"], capture_output=True, text=True)
    cp.check_returncode()
    images = json.loads(cp.stdout)["images"]
    for image in images:
        for repo_tag in image["repoTags"]:
            if repo_tag.startswith(IMAGE_NAME):
                return repo_tag.split(":")[-1]
    else:
        raise Exception(f"No image with name {IMAGE_NAME} found")

def get_pause_version():
    cp = subprocess.run(["crictl", "images", "-o", "json"], capture_output=True, text=True)
    cp.check_returncode()
    images = json.loads(cp.stdout)["images"]
    for image in images:
        for repo_tag in image["repoTags"]:
            if repo_tag.startswith(PAUSE_IMAGE_NAME):
                return repo_tag.split(":")[-1]
    else:
        raise Exception(f"No image with name {PAUSE_IMAGE_NAME} found")

def pin_image():
    image_name_with_version = IMAGE_NAME + ":" + get_registry_version()
    image_name_with_latest = IMAGE_NAME + ":" + "latest"
    subprocess.run(["ctr", "-n", "k8s.io", "images", "label", image_name_with_version, LABEL], check=True)
    subprocess.run(["ctr", "-n", "k8s.io", "images", "label", image_name_with_latest, LABEL], check=False)

    pause_image_name_with_version = PAUSE_IMAGE_NAME + ":" + get_pause_version()
    subprocess.run(["ctr", "-n", "k8s.io", "images", "label", pause_image_name_with_version, LABEL], check=True)

def main():
    parser = argparse.ArgumentParser(
        description='Script to copy carvel packages')
    parser.add_argument('--version',
                        action='store_true',
                        help='Print version of docker-registry image')
    parser.add_argument('--pin',
                        action='store_true',
                        help='Pin image by applying label io.cri-containerd.pinned=pinned')

    args = parser.parse_args()
    if args.version:
        print(get_registry_version())
    elif args.pin:
        pin_image()


if __name__ == '__main__':
    main()
