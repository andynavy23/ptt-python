# 使用 Docker 建置 PTT 爬蟲

### 使用工具說明：

  - Mac Pro 
  - Docker
  - MongoDB
  - Python
  - Visual Studio Code


### 安裝說明：

1. 安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. 安裝完成後於終端機進行映像檔安裝，需要安裝的項目有：
    - mongodb(使用官方的image)
    - python(使用官方的image修改後建立自己的image)

```sh
$ docker pull mongo
$ docker pull python
```

將github上的檔案全部下載到本機電腦後到工作目錄下建立自己的python image
例如將所有檔案下載放到/Users/使用者名字/Downloads，當執行以下建立自己的image指令時要確保工作目錄是在/Users/使用者名字/Downloads
