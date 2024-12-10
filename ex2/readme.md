---
lang: pl-PL
---

# Przykład prezentujący wysyłanie danych spoza pasma OOB

Przykład składa się z dwóch programów w architekturze klient-serwer.
Prezentuje on, w jaki sposób można obsługiwać przesyłanie danych spoza pasma. Klient zaczyna przesyłać dane, z prędkością większą niż serwer jest w stanie je przetworzyć. W normalnym przypadku po zatrzymaniu klienta połączenie zostałoby zerwane, jednak serwer dalej przetwarzałby dane znajdujące się w buforze.  Wysyłając bit OOB informujemy serwer, że połączenie zostało przerwane i natychmiast przestanie przetwarzać dane.
## Uruchomienie
serwer musi być uruchomiony jako pierwszy

### serwer
uruchomieni kontenera
```
docker compose run server
```
możliwe użycie
```
main.py [-h] [-w WAIT] [-s SIZE]

opcje:
  -h, --help            show this help message and exit
  -w WAIT, --wait WAIT  czas potrzebny do przetworzenia
                        jednego pakietu
  -s SIZE, --size SIZE  wielkość danych przetwarzanych 
                        jednorazowo


```

### klient
uruchomienie kontenera
```
docker compose run client
```
możliwe użycie
```
main.py [-h] [-w WAIT] [-s SIZE] [destination]

argumenty pozycyjne:
  destination - domyślnie 'server'

opcje:
  -h, --help            show this help message and exit
  -w WAIT, --wait WAIT  czas po jakim wysyłany jest kolejny poakiet
  -s SIZE, --size SIZE  wielkość pojedynczego pakietu

```

W celu uruchomienia programów z dodatkowymi opcjami należy zmienić zmienną środowiskowa `CMD` w pliku `compose.yaml`.

## Opis przykładu

Klient wysyła dane szybciej, niż serwer jest w stanie je przetworzyć.
Wyłączenie klienta poprzez naciśnięcie `Ctrl-C` spowoduje wysłanie bitu OOB,
który dla serwera będzie sygnałem, żeby zakończyć połączenie.