from django.db import models
from django.utils.text import slugify


class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' -> '.join(full_path[::-1])


class Attribute(models.Model):
    name = models.CharField(max_length=600, unique=True)
    slug = models.SlugField(max_length=600, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    category = models.ForeignKey(
        ProductCategory, related_name='products',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    brand = models.ForeignKey(
        Brand, related_name='products',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    
    is_globally_active = models.BooleanField(default=True)

    # ✅ New Fields
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rating = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    similar_products = models.ManyToManyField(
        'self',  # same model
        blank=True,
        symmetrical=False,
        related_name='similar_to'
    )

    tags = models.ManyToManyField(Tag, through='ProductTagMap', related_name='products')

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.name)
            slug = original_slug
            count = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{original_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/images/')
    image_url = models.URLField(max_length=2048, blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['product'], condition=models.Q(is_primary=True), name='unique_primary_image_per_product')
        ]

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.product.name}" + (" (Primary)" if self.is_primary else "")


class ProductAttributeValue(models.Model):
    product = models.ForeignKey(Product, related_name="attribute_values", on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, related_name="values_for_products", on_delete=models.CASCADE)
    value = models.CharField(max_length=600)

    class Meta:
        unique_together = ('product', 'attribute')
        verbose_name = "Product Attribute Value"
        verbose_name_plural = "Product Attribute Values"

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"


class ProductTagMap(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('product', 'tag')
        verbose_name = "Product Tag Mapping"
        verbose_name_plural = "Product Tag Mappings"

    def __str__(self):
        return f"{self.product.name} tagged with {self.tag.name}"



class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=0)
    image = models.ForeignKey(ProductImage, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Dynamic attributes through this relationship
    attributes = models.ManyToManyField(
        Attribute,
        through='VariantAttribute',
        through_fields=('variant', 'attribute'),
        related_name='variants'
    )

    class Meta:
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        ordering = ['product', 'name']
        
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def get_price(self):
        """Calculate final price including base product price and variant additional price"""
        return self.product.price + self.additional_price
    
    def save(self, *args, **kwargs):
        if not self.sku:
            # Generate SKU if not provided
            base_sku = slugify(f"{self.product.id}-{self.name}").upper()
            self.sku = base_sku
            counter = 1
            while ProductVariant.objects.filter(sku=self.sku).exclude(pk=self.pk).exists():
                self.sku = f"{base_sku}-{counter}"
                counter += 1
        super().save(*args, **kwargs)


class VariantAttribute(models.Model):
    """Through model for variant-attribute relationship with values"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    
    class Meta:
        unique_together = ('variant', 'attribute')
        verbose_name = "Variant Attribute"
        verbose_name_plural = "Variant Attributes"
        
    def __str__(self):
        return f"{self.variant}: {self.attribute.name} = {self.value}"
    
class ProductSegment(models.Model):
    title = models.CharField(max_length=255, help_text="Section title for frontend (e.g. Trending Now)")
    slug = models.SlugField(unique=True, blank=True)
    products = models.ManyToManyField(Product, related_name='segments')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

