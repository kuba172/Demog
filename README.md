# DemoG

DemoG to projekt studencki z przedmiotu "Systemy informatyczne". Jest to aplikacja desktopowa stworzona w PyQt6, która służy do predykcji demografii w celu zbadania atrakcyjności biznesowej w Polsce dla wybranych powiatów. Powiaty można wybrać po nazwie, kodzie pocztowym lub z interaktywnej mapy Polski. Po wybraniu wymaganych ustawień generuje się raport w formie PDF. Projekt wykorzystuje model uczenia maszynowego, który jest trenowany na podstawie danych z Głównego Urzędu Statystycznego.

## Funkcje

1. **Wybór powiatu**: Użytkownik może wybrać powiat po nazwie, kodzie pocztowym lub z interaktywnej mapy Polski.
2. **Generowanie raportu**: Po wybraniu wymaganych ustawień, generowany jest raport w formie PDF.
3. **Personalizacja wyglądu aplikacji oraz ustawień raportu**: Możliwość zmiany kolorystyki aplikacji oraz zmiany ustawień aplikacji.
4. **Zapis pracy**: Możliwość zapisania stanu aplikacji do pliku .demog.

## Biblioteki

### UI
- PyQt6
- pyqt6-tools (opcjonalnie do projektowania ui w qtdesigner itp.)
- qt-material

### Raport
- pandas
- matplotlib
- reportlab
- plotnine

### Model
- scikit-learn

## Instalacja
1. Zacznij od sklonowania repozytorium na swój komputer za pomocą polecenia:
    ```bash
    git clone https://github.com/kuba172/demog.git
    ```

2. Zainstaluj wymagane biblioteki za pomocą polecenia:
    ```bash
    pip install -r requirements.txt
    ```

3. Uruchom aplikację za pomocą polecenia:
    ```bash
    python main.py
    ```
    
## Zdjęcia poglądowe aplikacji

### Główne okno aplikacji
![image1](https://github.com/OskarLewandowski/ImageLibrary/blob/master/ImageLibrary/DemoG_images/Screenshot_1.png)

### Okno ustawień aplikacji
![image2](https://github.com/OskarLewandowski/ImageLibrary/blob/master/ImageLibrary/DemoG_images/Screenshot_4.png)
