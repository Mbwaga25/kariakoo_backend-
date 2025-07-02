# your_app/graphql/handlers/attribute_handler.py
from .base_handler import BaseHandler
from ...models import Attribute # Adjusted path to app's models

class AttributeHandler(BaseHandler):
    model = Attribute
    required_fields = ['name']
    lookup_field = 'name'

    def handle(self, data):
        errors = []
        if not self.validate_data(data, errors):
            return {'instance': None, 'status': 'error', 'errors': errors}

        lookup_params, param_errors = self._get_lookup_params(data)
        if param_errors:
            return {'instance': None, 'status': 'error', 'errors': param_errors}
        
        attribute_name = lookup_params.get(self.lookup_field)

        # Attributes are simple, defaults will be empty unless more fields are added to the model
        defaults = {} 

        instance = None
        status = 'skipped'

        try:
            if self.update_existing:
                instance, created = self.model.objects.update_or_create(
                    defaults=defaults, # No other fields to update by default for Attribute
                    **lookup_params
                )
                status = 'created' if created else 'updated'
            else:
                try:
                    instance = self.model.objects.get(**lookup_params)
                    # Found, not updating.
                except self.model.DoesNotExist:
                    if self.create_related: # Can we create this attribute?
                        # For Attribute, lookup_params (e.g. {'name': 'Color'}) is the creation data
                        instance = self.model.objects.create(**lookup_params)
                        status = 'created'
                    else:
                        errors.append(f"{self.model.__name__} '{attribute_name}' not found, and creation is disallowed.")
                        status = 'error'
                except self.model.MultipleObjectsReturned:
                    errors.append(f"Multiple {self.model.__name__} instances found for '{attribute_name}'.")
                    status = 'error'
        
        except Exception as e:
            errors.append(f"Error processing {self.model.__name__} '{attribute_name}': {str(e)}")
            status = 'error'
            if instance:
                instance = None
        
        final_status = status
        if errors and status not in ['error', 'skipped']:
            final_status = 'completed_with_errors' # Should not happen for Attribute if simple

        return {'instance': instance, 'status': final_status, 'errors': errors}
