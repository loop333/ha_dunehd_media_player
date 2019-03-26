## DuneHD Media Player Component for Home Assistant

install:  
```sh
cd ~/.homeassistant/custom_components
git clone https://github.com/loop333/ha_dunehd_media_player dunehd
```
configuration.yaml:  
```yaml
media_player:
  - platform: dunehd
     name: dunehd
     host: 192.168.1.4
     timeout: 20
```
