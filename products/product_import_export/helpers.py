# your_app/graphql/helpers.py
import base64
import csv
import json
from io import StringIO, BytesIO # Import BytesIO
from django.core.files.base import ContentFile
from django.utils.text import slugify
# Ensure your models are importable, adjust path if necessary
from ..models import ProductCategory # Example for specific model check
import requests # For downloading images from URLs
from PIL import Image # For image conversion to WebP

def handle_image_import(image_data_source, field_name_prefix):
    """
    Processes image data, which can be a base64 string or a URL.
    If it's a URL, it downloads the image and converts it to WebP format.
    Returns a ContentFile (WebP) or None.
    """
    if not image_data_source:
        return None
    
    image_content = None
    original_ext = None
    filename_base = slugify(field_name_prefix)

    try:
        if isinstance(image_data_source, str) and image_data_source.startswith('data:image'):
            # Handle base64 encoded images
            header, imgstr = image_data_source.split(';base64,')
            mime_type = header.split(':')[1].split(';')[0] # e.g., image/png
            original_ext = mime_type.split('/')[-1]
            if '+' in original_ext: # e.g., svg+xml
                original_ext = original_ext.split('+')[0]
            
            image_bytes = base64.b64decode(imgstr)
            img = Image.open(BytesIO(image_bytes))
            
            # If the original is already WebP, you might decide to keep it or re-process
            # For simplicity, we'll convert to ensure settings are applied.
            # img.format will give the original format if needed.

        elif isinstance(image_data_source, str) and image_data_source.startswith('http'):
            # Handle image URLs
            response = requests.get(image_data_source, stream=True, timeout=10)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            # Try to guess original extension for logging or intermediate steps if needed
            content_type = response.headers.get('content-type')
            if content_type and 'image/' in content_type:
                original_ext = content_type.split('image/')[-1]

            img = Image.open(response.raw) # Load image directly from response stream

        else:
            # Unsupported image data source type
            print(f"Unsupported image data source: {image_data_source}")
            return None

        # Convert to RGB if it's RGBA (or other modes that WebP might have issues with for transparency)
        # WebP supports transparency, but converting to RGB first if alpha is not needed can be safer.
        # If you need to preserve transparency, ensure your WebP save options are correct.
        if img.mode == 'RGBA' or img.mode == 'P': # P is paletted, might have transparency
            img = img.convert("RGBA") # Keep alpha for WebP
        elif img.mode != 'RGB':
            img = img.convert("RGB")

        # Save to WebP format in memory
        webp_buffer = BytesIO()
        # You can adjust quality, lossless, etc.
        # For transparency with lossless, use `lossless=True`. For lossy with alpha, WebP handles it.
        img.save(webp_buffer, format='WEBP', quality=80) # Adjust quality as needed
        webp_buffer.seek(0)
        
        final_filename = f"{filename_base}.webp"
        return ContentFile(webp_buffer.read(), name=final_filename)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {image_data_source}: {e}")
        return None
    except IOError as e: # Pillow (PIL) specific errors
        print(f"Error processing image (PIL) from {image_data_source} (format: {original_ext}): {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while handling image {image_data_source}: {e}")
        return None

# --- Other helper functions (get_or_create_related, process_csv_file, process_json_file) ---
# These remain the same as previously defined. Make sure they are present in this file.

def get_or_create_related(model, lookup_params, defaults=None, create_if_missing=True, update_existing_flag=False):
    if defaults is None:
        defaults = {}
    errors = []
    instance = None
    try:
        if update_existing_flag:
            instance, created = model.objects.update_or_create(
                defaults=defaults,
                **lookup_params
            )
        else:
            try:
                instance = model.objects.get(**lookup_params)
            except model.DoesNotExist:
                if create_if_missing:
                    create_data = {**defaults, **lookup_params}
                    instance = model.objects.create(**create_data)
                else:
                    errors.append(f"{model.__name__} with {lookup_params} not found and creation not allowed.")
            except model.MultipleObjectsReturned:
                errors.append(f"Multiple {model.__name__} instances found for {lookup_params}. Please ensure unique lookups.")
    except Exception as e:
        errors.append(f"Error processing {model.__name__} with {lookup_params}: {str(e)}")
    return instance, errors

def process_csv_file(file_content_string):
    file_like_object = StringIO(file_content_string)
    reader = csv.DictReader(file_like_object)
    return list(reader)

def process_json_file(file_content_string):
    parsed_json = json.loads(file_content_string)
    if not isinstance(parsed_json, list):
        return [parsed_json]
    return parsed_json
