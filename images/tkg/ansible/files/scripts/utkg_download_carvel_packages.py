import argparse
import subprocess


def download_image_from_artifactory(image_path, localhost_image_path):
    image_path_list = image_path.split(',')
    localhost_image_path_list = localhost_image_path.split(',')
    try:
        for i in range(len(image_path_list)):
            image_path_list[i] = image_path_list[i].strip()
            localhost_image_path_list[i] = localhost_image_path_list[i].strip()
            download_tar = 'wget ' + image_path_list[i]
            subprocess.check_output(['bash', '-c', download_tar])
            tar_file_name = image_path_list[i].split('/')[-1]
            carvel_tools = '/tmp/carvel-tools/imgpkg copy --tar ' + tar_file_name + ' --to-repo ' + \
                           localhost_image_path_list[i]
            subprocess.check_output(['bash', '-c', carvel_tools])
    except Exception as e:
        raise Exception("Unable to download carvel package", str(e))

    if len(image_path_list) == 0:
        raise Exception("Could not find carvel package")


def main():
    parser = argparse.ArgumentParser(
        description='Script to copy carvel packages')
    parser.add_argument('--addonImageList',
                        help='List of addon package images')
    parser.add_argument('--addonLocalImageList',
                        help='List of addon package local images',
                        default=None)

    args = parser.parse_args()
    download_image_from_artifactory(args.addonImageList, args.addonLocalImageList)


if __name__ == '__main__':
    main()
