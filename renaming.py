import pandas as pd
import requests
import os
import zipfile
from PIL import Image, ImageOps
from io import BytesIO
from google.colab import files

download_folder = "images"
zip_filename = "images.zip"
os.makedirs(download_folder, exist_ok=True)

def extract_pharmacode(product_code):
    return product_code[2:].lstrip("0") if product_code.startswith("CH") else product_code

def process_image(product_code):
    pharmacode = extract_pharmacode(product_code)
    image_url = f"https://documedis.hcisolutions.ch/2020-01/api/products/image/PICFRONT3D/Pharmacode/{pharmacode}/F"

    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            # Apre l'immagine e applica eventuale correzione di orientamento
            img = Image.open(BytesIO(response.content))
            img = ImageOps.exif_transpose(img)

            # (Opzionale) Se NON vuoi mai che sia tagliata, riduci se > 1000x1000
            if img.width > 1000 or img.height > 1000:
                img.thumbnail((1000, 1000), Image.LANCZOS)

            # Crea tela 1000x1000 bianca
            canvas_size = (1000, 1000)
            canvas = Image.new("RGB", canvas_size, (255, 255, 255))

            # Calcolo offset per centrare
            offset_x = (canvas_size[0] - img.width) // 2
            offset_y = (canvas_size[1] - img.height) // 2

            # Incolla l'immagine (se rimane più grande, verrà tagliata)
            canvas.paste(img, (offset_x, offset_y))

            # Salvataggio
            new_filename = f"{product_code}-h1.jpg"
            img_path = os.path.join(download_folder, new_filename)
            canvas.save(img_path, "JPEG", quality=95)
            print(f"✔ Immagine salvata: {new_filename}")
        else:
            print(f"❌ Errore nel download: {product_code}")
    except Exception as e:
        print(f"❌ Errore per {product_code}: {str(e)}")

# Caricamento file Excel
uploaded = files.upload()
file_name = list(uploaded.keys())[0]
df = pd.read_excel(file_name)

for product_code in df['sku']:
    process_image(str(product_code))

# Crea file ZIP
zip_path = os.path.join(download_folder, zip_filename)
with zipfile.ZipFile(zip_filename, 'w') as zipf:
    for file in os.listdir(download_folder):
        zipf.write(os.path.join(download_folder, file), file)

# Download file ZIP
files.download(zip_filename)
print("✅ Download completato!")
