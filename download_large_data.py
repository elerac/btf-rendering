import urllib.error
import urllib.request
import os
import time
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def download_file(url, dst_dir):
    dst_path = os.path.join(dst_dir, os.path.basename(url))
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request) as web_file, open(dst_path, 'wb') as local_file:
            local_file.write(web_file.read())
    except urllib.error.URLError as e:
        print(e)

def main():
    print("UBO2003 BTF Dataset")
    ubo2003_dir = "UBO2003"
    os.makedirs(ubo2003_dir, exist_ok=True)
    
    file_path = f"{ubo2003_dir}/UBO_IMPALLA256.zip"
    if os.path.exists(file_path):
        print(f"  {file_path} is already exists")
    else:
        print(f"  Download {file_path}...")
        download_file("http://cg.cs.uni-bonn.de/fileadmin/btf/UBO2003/IMPALLA/ONEFILE/UBO_IMPALLA256.zip", ubo2003_dir)
        time.sleep(1)
    
    file_path = f"{ubo2003_dir}/UBO_WOOL256.zip"
    if os.path.exists(file_path):
        print(f"  {file_path} is already exists")
    else:
        print(f"  Download {file_path}...")
        download_file("http://cg.cs.uni-bonn.de/fileadmin/btf/UBO2003/WOOL/ONEFILE/UBO_WOOL256.zip", ubo2003_dir)
        time.sleep(1)


    print("Envmap from hdrihaven.com")
    cloth_dir = "scenes/cloth"
    os.makedirs(cloth_dir, exist_ok=True)

    file_path = f"{cloth_dir}/skylit_garage_1k.hdr"
    if os.path.exists(file_path):
        print(f"  {file_path} is already exists")
    else:
        print(f"  Download {file_path}...")
        download_file("https://hdrihaven.com/files/hdris/skylit_garage_1k.hdr", cloth_dir)
        time.sleep(1)


if __name__=="__main__":
    main()
