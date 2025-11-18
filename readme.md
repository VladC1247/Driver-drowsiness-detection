# Driver Drowsiness Detection 🚗💤

Acest proiect oferă un sistem complet pentru detectarea oboselii șoferilor în timp real, folosind recunoaștere facială și un model YOLOv8 antrenat cu imagini etichetate. Sistemul permite logarea evenimentelor, vizualizarea statisticilor și gestionarea utilizatorilor printr-o interfață grafică.

## 🧠 Funcționalități

- Recunoaștere facială pentru identificarea șoferului
- Detecția somnolenței (`awake` / `drowsy`) în timp real
- Alerte audio/vizuale la oboseală
- Pauze scurte și lungi cu logare și avertizări
- Panou de administrare pentru gestionarea utilizatorilor și logurilor
- Statistici vizuale (grafice) pentru analiza sesiunilor

## 📦 Structura Proiectului

DriverDrowsinessDetection/
│
├── main.py # Interfața de start și autentificare facială
├── drowsiness_detection.py # Detecția oboselii și logica principală
├── admin_panel.py # Interfața de administrare și statistici
├── db.py # Interfață cu baza de date SQLite
├── database.db # Baza de date SQLite cu utilizatori și evenimente
├── alarm.wav # Sunet pentru avertizarea oboselii
├── yolov8.pt # Model YOLOv8 antrenat
└── tools/
   ├── captureImg.py  # Script de captură imagini etichetate
   ├── labelImg/      # Tool etichetare
   └── yolov8/        # Antrenare model YOLOv8
 

## 🛠 Tehnologii

- **Limbaj**: Python 3.12
- **Interfață grafică**: Tkinter, Ttk
- **Procesare video**: OpenCV, Pillow
- **Recunoaștere facială**: face_recognition
- **Model AI detecție**: YOLOv8 (Ultralytics)
- **Audio alertă**: pygame
- **Bază de date**: SQLite (sqlite3 + json pentru serializare)
- **Statistici și grafice**: matplotlib

## 🔧 Tool-uri folosite în pregătirea datasetului

- **captureImg.py**: script propriu pentru capturarea imaginilor `awake` și `drowsy` folosind webcam-ul
- **Etichetare imagini**: [labelImg](https://github.com/HumanSignal/labelImg)
- **Antrenare model**: [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)

## 📸 Flux de antrenare al modelului

   Modelul YOLOv8 folosit pentru detecția stării de oboseală (`awake` / `drowsy`) a fost antrenat în mai mulți pași:

 1. **Capturarea imaginilor**
    - Scriptul `tools/capture/captureImg.py` permite generarea de imagini cu stările dorite (`awake`, `drowsy`) folosind webcamul.
    - Imaginile sunt salvate în `tools/capture/data/images`.

 2. **Etichetarea imaginilor**
    - Imaginile generate sunt etichetate manual folosind aplicația [labelImg](https://github.com/HumanSignal/labelImg).
    - Fiecare imagine este însoțită de un fișier `.txt` cu etichetele aferente, în format YOLO.

 3. **Organizarea datasetului pentru antrenare**
   - Imaginile și fișierele de etichete sunt copiate în structura YOLOv8:
     
     tools/yolov8/data/
     ├── images/
     │   ├── train/
     │   └── val/
     └── labels/
         ├── train/
         └── val/
    
   - **Precizări**:
     - Este recomandat ca aproximativ **80%** din imaginile capturate să fie plasate în `images/train`, iar restul de **20%** în `images/val` (pentru validare).
     - În mod similar, fișierele de etichete `.txt` asociate trebuie mutate în aceleași subfoldere: `labels/train` și `labels/val`.
     - **Atenție**: asigurați-vă că numele fișierelor `.jpg` și `.txt` corespund și că sunt sincronizate între imaginile de antrenare și cele de validare.


 4. **Antrenarea modelului**
    - Se folosește comanda YOLOv8:
      ```bash
      yolo detect train data=tools/yolov8/data.yaml model=yolov8n.pt epochs=150 imgsz=640 device=cpu
      ```
    - Parametrul `device=cpu` este utilizat în cazul sistemelor care **nu dispun de o placă video performantă**, dar au un procesor suficient de puternic. Astfel, antrenarea poate avea loc direct pe CPU, fără a fi necesar un GPU dedicat.
    - Rezultatul antrenării este salvat automat în runs/detect/train/weights/best.pt

 5. **Integrarea în proiectul principal**
    - După finalizarea antrenării, modelul antrenat `best.pt` este redenumit ca `yolov8.pt`
    - Acesta este ulterior mutat în folderul DriverDrowsinessDetection
    - La rularea programului, modelul este folosit pentru a face predicții pe cadrele video capturate în timp real. Etichetele `awake` și `drowsy` sunt extrase pentru a decide dacă se declanșează o alertă de oboseală.

Astfel, întregul pipeline — de la captură și etichetare, până la integrarea modelului în aplicație — este complet automatizat și flexibil.


## 🚀 Cum rulezi proiectul

1. Instalează toate dependențele (`requirements.txt`)

   pip install -r requirements.txt

2. Rulează interfața principală:

   Rulează comanda: python main.py în terminal

3. Identifică-te prin recunoaștere facială sau adaugă un utilizator nou

4. Începe monitorizarea sesiunii sau accesează panoul de administrare (dacă ai permisiuni)   

## 🔐 Notă pentru testare și acces administrativ

Pentru utilizatorii noi care vor să testeze aplicația, dar nu au deja statut de administrator:

1. Rulați comanda: python main.py în terminal

2. La prima rulare, fața nefiind recunoscută, veți fi adăugat automat ca utilizator de tip user după ce introduceți un nume nou.

3. După salvarea utilizatorului, închideți aplicația și rulați: python admin_panel.py

4. Din panoul de administrare, selectați numele dvs. din listă și apăsați Make Admin pentru a vă acorda permisiuni administrative.

## 📂 Bază de date
   
   `users` – embedding facial + rol (admin/user)

   `events` – loguri precum start_trip, fatigue_detected, short_break_exceeded, etc.
