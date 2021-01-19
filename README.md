# About
This is an **UNOFFICIAL API** and CLI tool for https://programare.vaccinare-covid.gov.ro/.

It retrieves the list of available slots from all available locations within the country.

The list can be published to Google Drive as a Spreadsheet document. Currently, this is published every 30 minutes.
You can see it here:
- http://bit.ly/centre-vaccinare (HTML)
- http://bit.ly/centre-vaccinare-csv (CSV)
- http://bit.ly/centre-vaccinare-xlsx (XLSX)
- http://bit.ly/centre-vaccinare-pe-zile (HTML, grouped by centre and date)
- http://bit.ly/centre-vaccinare-pe-zile-csv (CSV, grouped by centre and date)
- http://bit.ly/centre-vaccinare-pe-zile-xls (XLS, grouped by centre and date)

Please note that this is an **UNOFFICIAL** repository, so I cannot guarantee the accuracy of the data provided. The
sole purpose of this project is to provide easier access to the list of all medical units and available slots for
vaccine appointments.

At the moment, there's also a bug in [programare.vaccinare-covid.gov.ro](https://programare.vaccinare-covid.gov.ro/)
that shows some units as having available slots, while there are none; this project curates the list and publishes only
those units with available slots.

Feel free to fork and improve this.

# Usage

1. Get the value of the `SESSION` cookie (after you create an account and log in at
   https://programare.vaccinare-covid.gov.ro).
   
   ```bash
   export VACCINARE_TOKEN="..."
   ```

2. Install the requirements:
   
   ```bash
   pip3 install -r requirements.txt
   ```

3. Execute the script:
    ```bash
    ./vca get-available-slots
    ```

For help and usage:
```bash
./vca --help
```

## Sample output
```
Județ,Localitate,Centru,Adresă centru,Date disponibile
Alba,Aiud,SALĂ DE SPORT,"Aiud, str Tribun Tudoran, nr. 5",2021-01-20;2021-01-21
Alba,Alba Iulia,SALĂ DE SPORT-Universitatea 1 Decembrie,"Alba Iulia, str. Vasile Alecsandri, FN",2021-01-24
...
Vrancea,Odobesti,Sala de sport,Odobesti,2021-01-23;2021-01-24
```

# License
TLD;R: Do whatever you want as long as you include the original license notice in any copy of this software.

This software is licensed under MIT. See [LICENSE](LICENSE) for more details.

# Disclaimer
This is provided "as is", without warranty of any kind. Don't abuse it. Go get Vaccinated!
