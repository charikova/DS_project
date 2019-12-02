# Group Project Assignment: Distributed File System
## Mariia Charikova, Igor Krasheninnikov, Roman Solovev <br>BS17-SB
## Backup Video of working system:
https://drive.google.com/file/d/18WsAa2DlePjVnSI5JXkVPJHaKN3p9v7b/view?usp=sharing
## How to launch and use the system
### First choice
* `cd` in every component folder and just run `docker-compose up`
* docker will pull all necessary images and start every part of the system separately
### Second choice
* Initiate the docker swarm network
* Run `sudo docker stack deploy --compose-file docker-compose.yml dfs`
* Docker will automatically pull all necessary images and will create 3 containers on manager node: Nameserver, Neo4j and visualization and one Client container on worker node and three replicas of Storage server container
## Architectural diagram
![](https://i.imgur.com/LWZkSHF.png)
### Docker swarm architecture
![](https://i.imgur.com/98isMU8.png)
## Description of communication protocols
### Initialize
![](https://i.imgur.com/8L1CNEo.png)
### File create
![](https://i.imgur.com/ndQ6JAZ.png)
### File download
![](https://i.imgur.com/7NaLEib.png)
### File upload
![](https://i.imgur.com/m6STKiv.png)
### File delete
![](https://i.imgur.com/wmfNd62.png)
### File info
![](https://i.imgur.com/CJVfUhN.png)
### File copy
![](https://i.imgur.com/fLSmqiL.png)
### File move
![](https://i.imgur.com/unuGw8u.png)
### Open + Read directory
![](https://i.imgur.com/3QG1kbI.png)
### Make directory
![](https://i.imgur.com/imPGn2P.png)
### Delete directory
![](https://i.imgur.com/8brYiZw.png)
