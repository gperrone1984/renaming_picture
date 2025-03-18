import pandas as pd
import requests
import os
import zipfile
from PIL import Image, ImageOps
from io import BytesIO

# Verifica se siamo in modalità interattiva (Colab) o meno
try:
    from google.colab import files
    interactive = True
except ImportError:
    interactive = False

# Configurazione cartelle e file ZIP
download_folder = "images"
zip_filename = "images.zip"
os.makedirs(download_folder, exist_ok=True)

# Funzione per rimuovere il prefisso CH e gli zeri iniziali
def extract_pharmacode(product_code):
    return product_code[2:].lstrip("0") if product_code.startswith("CH") else product_code

# Funzione per scaricare l'immagine, centrarla su una tela bianca 1000x1000 e salvarla
def process_image(product_code):
    pharmacode = extract_pharmacode(product_code)
    image_url = f"https://documedis.hcisolutions.ch/2020-01/api/products/image/PICFRONT3D/Pharmacode/{pharmacode}/F"

    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            # Apre l'immagine e applica eventuale correzione di orientamento
            img = Image.open(BytesIO(response.content))
            img = ImageOps.exif_transpose(img)

            # Se preferisci non ridimensionare l'immagine (anche se è maggiore di 1000x1000)
            # rimuovi o commenta il seguente blocco:
            # if img.width > 1000 or img.height > 1000:
            #     img.thumbnail((1000, 1000), Image.LANCZOS)

            # Crea una tela bianca 1000x1000
            canvas_size = (1000, 1000)
            canvas = Image.new("RGB", canvas_size, (255, 255, 255))

            # Calcola l'offset per centrare l'immagine
            offset_x = (canvas_size[0] - img.width) // 2
            offset_y = (canvas_size[1] - img.height) // 2

            # Incolla l'immagine sulla tela (se l'immagine è più grande, verrà tagliata)
            canvas.paste(img, (offset_x, offset_y))

            # Salva il file con nome <product_code>-h1.jpg
            new_filename = f"{product_code}-h1.jpg"
            img_path = os.path.join(download_folder, new_filename)
            canvas.save(img_path, "JPEG", quality=95)
            print(f"✔ Immagine salvata: {new_filename}")
        else:
            print(f"❌ Errore nel download: {product_code}")
    except Exception as e:
        print(f"❌ Errore per {product_code}: {str(e)}")

# Gestione dell'input Excel:
if interactive:
    # Modalità Colab: carica il file tramite l'interfaccia interattiva
    uploaded = files.upload()
    file_name = list(uploaded.keys())[0]
else:
    # Modalità non interattiva (GitHub Actions o esecuzione locale): si utilizza un file predefinito
    file_name = "input.xlsx"
    if not os.path.exists(file_name):
        print(f"File {file_name} non trovato. Assicurati di inserire il file di input nel repository.")
        exit(1)

# Legge il file Excel e processa ogni codice prodotto presente nella colonna 'sku'
df = pd.read_excel(file_name)
for product_code in df['sku']:
    process_image(str(product_code))

# Creazione del file ZIP contenente le immagini salvate
zip_path = os.path.join(download_folder, zip_filename)
with zipfile.ZipFile(zip_filename, 'w') as zipf:
    for file in os.listdir(download_folder):
        zipf.write(os.path.join(download_folder, file), file)

if interactive:
    # In Colab, scarica il file ZIP tramite l'interfaccia
    files.download(zip_filename)
    print("✅ Download completato!")
else:
    print("✅ Esecuzione completata. Il file ZIP è stato creato: ", zip_filename)
