# yowsup-zmq
ZeroMQ (ZMQ) layer for yowsup

## Attention
This project is far from being complete. Not intended for production!
Right now, the following yowsup functionality is supported:
* message_send
* group_create

## Run
Create the configuration file `credentials.conf` with your credentials like this:
```
[CREDENTIALS]
CountryCode = 49
Phone = 49176123456
Password = B64PwdYouGotDuringRegistration=
```

Start the broker:
```
python3 run.py
```
