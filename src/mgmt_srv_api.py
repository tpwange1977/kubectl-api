from fastapi import FastAPI, File, UploadFile
from kubernetes import client, config, utils
#from kubernetes.utils import create_from_yaml
import uvicorn, os
import yaml
import subprocess

app = FastAPI()

# config.load_kube_config()
os.environ["KUBECONFIG"]="/src/.config"


@app.post("/deploy_api_by_kind")
async def deploy(files: list[UploadFile] = File(...)):
    messages = []

    for file in files:
        content = await file.read()
        yaml_content = yaml.safe_load(content)

        if yaml_content["kind"] == "Deployment":
            apps_v1 = client.AppsV1Api()
            deployment = client.V1Deployment(**yaml_content)
            apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
            messages.append(f"Deployment {yaml_content['metadata']['name']} created successfully!")
        elif yaml_content["kind"] == "Service":
            v1 = client.CoreV1Api()
            service = client.V1Service(**yaml_content)
            v1.create_namespaced_service(namespace="default", body=service)
            messages.append(f"Service {yaml_content['metadata']['name']} created successfully!")
        elif yaml_content["kind"] == "VirtualService":
            custom_api = client.CustomObjectsApi()
            virtual_service = yaml_content
            custom_api.create_namespaced_custom_object(
                group="networking.istio.io",
                version="v1alpha3",
                namespace="default",
                plural="virtualservices",
                body=virtual_service,
            )
            messages.append(f"VirtualService {yaml_content['metadata']['name']} created successfully!")
        else:
            messages.append(f"Unsupported kind in file {file.filename}!")

    return {"messages": messages}

@app.post("/deploy_kubectl")
async def deploy(files: list[UploadFile] = File(...)):
    for file in files:
        content = await file.read()
        yaml_files = content.strip().decode().split('---')
        

        for yaml_file in yaml_files:
            print(f"process file: {file.filename} ") 
            print(f"process yaml content: {yaml_file} ") 
            process = subprocess.Popen(["kubectl", "apply", "-f", "-"], stdin=subprocess.PIPE)
            process.communicate(input=yaml_file.encode())

    return {"message": "Deployment successfully initiated"}

@app.post("/deploy_api")
async def deploy(path_to_dir: str):
    command = ["./src/kubectl", "apply", "-R", "-f", path_to_dir]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print("Error executing command:")
        print(result.stderr.decode())
    else:
        print(result.stdout.decode())
    return {"message": "Deployment successfully initiated"}


def main():
    uvicorn.run(app, host="127.0.0.1", port=5000)

if __name__ == "__main__":
    main()



## 
## 
## uvicorn app:mgmt_srv_api 0.0.0.0 --reload

