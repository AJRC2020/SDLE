# Project 1 - Reliable Pub/Sub Service

## Instalation

This project was built using Python. Please use the following commands to install Python in Linux:

```
sudo apt-get install python3
```

For the instalation: 

```
pip install pyzmq
```


## Execution

### Proxy

In order to start the proxy please run the following command from the `src` folder:
```
python3 proxy.py
```

### Subscriber

In order to start a client please run the following command from the `src` folder:
```
python3 sub_client.py <topic>
```
Where:
- `<topic>` is the chosen topic to subscribe.

### Publisher

In order to start a client please run the following command from the `src` folder:
```
python3 pub_server.py <topic>
```
Where:
- `<topic>` is the chosen topic to publish.
