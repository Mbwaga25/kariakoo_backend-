# products/mutations.py (or brands/mutations.py)

import graphene
from django.utils.text import slugify
from graphql_jwt.decorators import login_required
from django.core.exceptions import ValidationError
from graphql_relay import from_global_id 
import graphene_file_upload.scalars
from django.core.files.base import ContentFile
import base64 # Import base64 for decoding
import imghdr # For guessing image type from binary data
import uuid

# Import your Brand model, BrandType, and ProductType
from ..models import Brand, Product # Assuming Brand and Product models are in products/models.py
from ..types import BrandType, ProductType # Assuming BrandType and ProductType are in products/types.py

# IMPORTANT: Import graphene.Upload for file uploads
import graphene_file_upload.scalars


# --- Input Types ---
class BrandInput(graphene.InputObjectType):
    """
    Input type for creating and updating a Brand.
    """
    name = graphene.String(required=True, description="Name of the brand.")
    # Slug is optional; can be auto-generated or explicitly provided
    slug = graphene.String(description="Unique slug for the brand (auto-generated if not provided).")
    logo = graphene.String(description="Base64 encoded image data or image URL.")
    description = graphene.String(description="Description of the brand.")

class UpdateBrandInput(graphene.InputObjectType):
    """
    Input type for updating a Brand. All fields are optional.
    """
    name = graphene.String(description="New name for the brand.")
    slug = graphene.String(description="New unique slug for the brand.")
    logo = graphene.String(description="New Base64 encoded image data or image URL.")
    description = graphene.String(description="New description of the brand.")
    # Optional: A field to explicitly clear the existing logo
    clear_logo = graphene.Boolean(description="Set to true to remove the existing logo.")


def base64_to_django_file(base64_string, filename_prefix="image"):
    if not base64_string:
        return None

    # Check for data URL prefix (e.g., "data:image/png;base64,")
    if ";base64," in base64_string:
        header, base64_data = base64_string.split(";base64,")
        # Try to infer extension from header, e.g., image/jpeg -> .jpeg
        try:
            mime_type = header.split("data:")[1].split(";")[0]
            extension = f".{mime_type.split('/')[1]}"
        except IndexError:
            extension = "" # No extension from header, will try imghdr later
    else:
        base64_data = base64_string
        extension = "" # No extension from header

    try:
        decoded_file = base64.b64decode(base64_data)
    except Exception as e:
        raise ValueError(f"Invalid base64 string: {e}")

    # Try to guess image type from decoded data if extension not found
    if not extension:
        image_type = imghdr.what(None, h=decoded_file)
        if image_type:
            extension = f".{image_type}"
        else:
            # Default to jpeg if type cannot be guessed
            extension = ".jpeg" 

    # Create a unique filename
    file_name = f"{filename_prefix}_{uuid.uuid4()}{extension}"
    
    return ContentFile(decoded_file, name=file_name)


class CreateBrandMutation(graphene.Mutation):
    class Arguments:
        input = BrandInput(required=True)

    brand = graphene.Field(BrandType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required
    def mutate(cls, root, info, input):
        # input.logo is now a string (Base64 or URL)
        logo_base64_string = input.logo

        brand_data = {
            'name': input.name,
            'slug': input.slug or slugify(input.name),
            'description': input.description,
        }

        try:
            brand = Brand(**brand_data)
            
            # Handle logo as Base64 string
            if logo_base64_string:
                logo_file = base64_to_django_file(logo_base64_string, filename_prefix=slugify(input.name or "brand"))
                if logo_file:
                    brand.logo.save(logo_file.name, logo_file, save=False)
                else:
                    raise ValueError("Failed to decode image data.")

            brand.full_clean()
            brand.save()

            return cls(brand=brand, success=True, errors=[])
        except ValidationError as e:
            return cls(brand=None, success=False, errors=list(e.messages))
        except ValueError as e: # Catch errors from base64_to_django_file
            return cls(brand=None, success=False, errors=[f"Image processing error: {str(e)}"])
        except Exception as e:
            return cls(brand=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


class UpdateBrandMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = UpdateBrandInput(required=True) # Use UpdateBrandInput

    brand = graphene.Field(BrandType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required
    def mutate(cls, root, info, id, input):
        try:
            brand = Brand.objects.get(pk=id)
        except Brand.DoesNotExist:
            return cls(brand=None, success=False, errors=["Brand not found."])
        except Exception as e:
            return cls(brand=None, success=False, errors=[f"Invalid ID: {str(e)}"])

        updated = False
        if input.name is not None:
            brand.name = input.name
            if input.slug is None: 
                brand.slug = slugify(input.name)
            updated = True
        
        if input.slug is not None:
            brand.slug = input.slug
            updated = True

        if input.description is not None:
            brand.description = input.description
            updated = True

        # Handle logo as Base64 string for update
        if input.logo is not None: # Check if logo string was provided
            if brand.logo:
                brand.logo.delete(save=False) # Delete old logo if a new one is provided
            
            logo_file = base64_to_django_file(input.logo, filename_prefix=slugify(input.name or brand.name or "brand"))
            if logo_file:
                brand.logo.save(logo_file.name, logo_file, save=False)
                updated = True
            else: # If input.logo was provided but decoded to None (e.g., empty string)
                # This could mean client wants to clear the image if empty string is sent for logo
                # Or you might handle this with a clear_logo boolean as in UpdateBrandInput
                if brand.logo:
                    brand.logo.delete(save=False)
                brand.logo = None
                updated = True
        elif hasattr(input, 'clear_logo') and input.clear_logo: # If clear_logo is explicitly true
            if brand.logo:
                brand.logo.delete(save=False)
            brand.logo = None
            updated = True
        # else: if input.logo is None and clear_logo is false, do nothing, keep existing logo

        try:
            if updated:
                brand.full_clean()
                brand.save()
            return cls(brand=brand, success=True, errors=[])
        except ValidationError as e:
            return cls(brand=None, success=False, errors=list(e.messages))
        except ValueError as e:
            return cls(brand=None, success=False, errors=[f"Image processing error: {str(e)}"])
        except Exception as e:
            return cls(brand=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])

class DeleteBrandMutation(graphene.Mutation):
    """
    Deletes an existing Brand.
    """
    class Arguments:
        id = graphene.ID(required=True, description="Global ID or primary key of the brand to delete.")

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Requires a logged-in user to delete a brand
    def mutate(cls, root, info, id):
        try:
            # Decode global ID if you are using Relay IDs
            # brand_pk = from_global_id(id)[1]
            # brand = Brand.objects.get(pk=brand_pk)
            brand = Brand.objects.get(pk=id)
            
            # Optional: Delete associated logo file when brand is deleted
            if brand.logo:
                brand.logo.delete() # This deletes the file from storage
            
            brand.delete() # This deletes the brand record from the database
            return cls(success=True, errors=[])
        except Brand.DoesNotExist:
            return cls(success=False, errors=["Brand not found."])
        except Exception as e:
            return cls(success=False, errors=[f"An unexpected error occurred: {str(e)}"])


