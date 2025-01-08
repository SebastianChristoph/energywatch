# energywatch

Diese App sammelt Strompreisdaten von verschiedenen Anbietern für deutsche Städte und speichert Preisänderungen. Nutzerinnen und Nutzer können für die 20 größten deutschen Städte Strompreisdaten abrufen und vergleichen.

Als Datengrundlage dient das Vergleichportal *check24.de*
Alle Strompreise beziehen sich auf Tarife, die mit einem durchschnittlichen Verbrauch von 2.500 kWh berechnet wurden.

Technischer Hintergrund
Zwei mal am Tag läuft auf einem Online-Server ein Python-Script, welches den Inhalt folgender URL request'et:

*https://www.check24.de/strom/vergleich/check24/?product_id=1&stats=yes&sortfield=popularity&sortorder=asc&zipcode={zipcode}&city={city_to_add}&totalconsumption=2500&pricing=month&setting=individual&commoncarrier=yes&customertype=private&energymix_type=all&tariffscore=0&contractperiod=12&consider_max_bonus_share=yes&cancellationperiod=30&contractextension=1&priceguarantee=fixed_price&priceguarantee_months=99&maxtariffs=2&companyevaluation_positive=yes&subscriptiononly=yes&guidelinematch=yes&packages=no&secondarytime_active=no&secondarytime=0&reference_provider_hash=drewag&reference_tariffversion_key=1278640-base&calculationparameter_id=1cbe3c84f1d5c154a174133c73c10fef&pagesize=120*

Wie in der URL zu sehen ist, werden Zipcode und City durch vorgegebene Werte ersetzt. Danach wird mit der library BeautifulSoup nach Tarif-Details gesucht. Alle Tarife werden gespeichert und mit einer SQLite-Datenbank verglichen. Unterscheidet sich ein Tarif-Preis vom letzten erfassten Tarif-Preis, wird ein neuer ProductChange in der Datenbank gespeichert und von dieser Flask-App abgerufen.
